from pathlib import Path
import datetime,hashlib,json,os,re,shlex,shutil,signal,subprocess,sys,time
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1');R=ROOT/'module_14_lm_head_v4/reports/d64_state_init_20261105_r2';V=ROOT/'.cache/d64_state_compile_20261105_r2'
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def parts(s):
    return s[s.rindex(')') + 2:].split()

def available():
    return next((int(s.split()[1]) for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:')))

def members(pgid):
    found = []
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():
            continue
        try:
            s = parts((p / 'stat').read_text())
            if s[0] != 'Z' and int(s[2]) == pgid:
                found.append(dict(pid=int(p.name), start_ticks=s[19], rss_kib=int(s[21]) * os.sysconf('SC_PAGE_SIZE') // 1024))
        except OSError:
            pass
    return found

def save():
    (R / 'WORKFLOW.json').write_text(json.dumps(state, indent=2) + '\n')

def terminate_owned(p):
    if members(p.pid):
        try:
            os.killpg(p.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        p.wait(timeout=10)
    deadline = time.monotonic() + 10
    while members(p.pid) and time.monotonic() < deadline:
        time.sleep(0.1)
    if members(p.pid):
        os.killpg(p.pid, signal.SIGKILL)
        deadline = time.monotonic() + 10
        while members(p.pid) and time.monotonic() < deadline:
            time.sleep(0.1)
    assert not members(p.pid), 'Owned process group did not drain'

def run(phase, command, seconds, expected_fatal=None):
    assert available() >= 32 * 1048576
    state.update(state='EXECUTING_' + phase.upper(), phase=phase, command=command)
    save()
    d = R / phase
    d.mkdir()
    started = time.monotonic()
    peak = 0
    with (d / 'tool.log').open('w') as log, (d / 'resources.jsonl').open('w') as resource:
        p = subprocess.Popen(['bash', '-c', 'source /tools/Xilinx/Vitis/2022.2/settings64.sh >/dev/null 2>&1 && exec ' + command], cwd=V, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        state.update(child_pid=p.pid, child_pgid=p.pid)
        save()
        try:
            while True:
                owned = members(p.pid)
                rss = sum((x['rss_kib'] for x in owned))
                peak = max(peak, rss)
                elapsed = time.monotonic() - started
                spare = available()
                sample = dict(utc=now(), elapsed_s=elapsed, rss_kib=rss, available_kib=spare, members=owned)
                resource.write(json.dumps(sample) + '\n')
                resource.flush()
                reason = 'STOP_REQUESTED' if (R / 'STOP_REQUESTED').exists() else 'GROUP_RSS_ABOVE_16GIB' if rss > 16 * 1048576 else 'AVAILABLE_BELOW_32GIB' if spare < 32 * 1048576 else 'PHASE_TIMEOUT' if elapsed > seconds else None
                if reason:
                    state['stop_evidence'] = dict(reason=reason, **sample)
                    save()
                    terminate_owned(p)
                    raise RuntimeError(reason)
                if p.poll() is not None:
                    break
                time.sleep(0.5)
            deadline = time.monotonic() + 5
            while members(p.pid) and time.monotonic() < deadline:
                time.sleep(0.1)
            assert not members(p.pid)
        except BaseException:
            terminate_owned(p)
            raise
    lines = (d / 'tool.log').read_text(errors='replace').splitlines()
    if expected_fatal is None:
        assert p.returncode == 0, (phase, p.returncode)
        assert not any((x.startswith(('Fatal:', 'ERROR:', 'UVM_FATAL', 'UVM_ERROR')) and (not re.fullmatch('UVM_(?:FATAL|ERROR)\\s*:\\s*0\\s*', x)) for x in lines))
        if phase == 'positive':
            assert sum((x.startswith('NATIVE_GATE_PASS case=positive ') for x in lines)) == 1
    else:
        fatals = [x for x in lines if x.startswith('Fatal:')]
        assert len(fatals) == 1 and expected_fatal in fatals[0], (phase, fatals)
        assert not any(('GATE_EXPECTED_REJECTION_MISSING' in x or 'GATE_WATCHDOG' in x or 'GATE_UNKNOWN_CASE' in x for x in lines))
        assert not any((x.startswith('NATIVE_GATE_PASS ') for x in lines))
    for name in ['native_wire.csv', 'memory_phases.csv']:
        if (V / name).exists():
            shutil.copy2(V / name, d / name)
    state['phases'][phase] = dict(elapsed_s=elapsed, peak_group_rss_kib=peak, returncode=p.returncode, expected_fatal=expected_fatal, tool_log_sha256=sha(d / 'tool.log'))
    save()
def large_sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
assert sys.argv[1:]==['--execute']
plan=json.loads((R/'EXECUTION_PLAN.json').read_text());C=ROOT/'module_14_lm_head_v4/reports/d64_state_compile_20261105_r2'
for n,h in plan['bindings'].items():assert sha(ROOT/n)==h,n
compile_plan=json.loads((C/'EXECUTION_PLAN.json').read_text());compiled=json.loads((C/'COMPILED_SOURCES.json').read_text())
for n,h in compiled.items():assert sha(V/n)==h,n
assert not (R/'WORKFLOW.json').exists() and not list((ROOT/'module_14_lm_head_v4/reports').rglob('ACTIVE.lock'))
assert available()>=32*1048576
weights=ROOT/plan['tv'];assert large_sha(weights)==plan['tv_sha256']
state=dict(state='PREPARING',started=now(),parent_pid=os.getpid(),parent_proc_stat=Path('/proc/self/stat').read_text(),phases={},scope='Full weight loading/sentinels only;zero DUT calls;no automatic state suite',automatic_next_stage=False)
(R/'ACTIVE.lock').write_text(str(os.getpid()));save()
try:
 command='/tools/Xilinx/Vivado/2022.2/bin/xsim '+plan['snapshot']+' -runall -testplusarg '+shlex.quote('ROOT='+str(ROOT))+' -testplusarg '+shlex.quote('WEIGHTS_TV='+str(weights))+' -testplusarg '+shlex.quote('OUT='+str(R/'load'))
 run('load',command,900)
 lines=(R/'load/tool.log').read_text(errors='replace').splitlines()
 assert sum(x=='STATE_LOAD_ONLY_PASS bytes=545685504 sentinels=1522 starts=0 dones=0' for x in lines)==1
 assert not any(x.startswith(('STATE_CASE_RETURNED','D64_STATE_SUITE_RETURNED','LMH_STAGE_PROFILE')) for x in lines)
 assert large_sha(weights)==plan['tv_sha256']
 for n,h in compiled.items():assert sha(V/n)==h,n
 if (V/'stage_profile.csv').exists():(R/'load/stage_profile.csv').write_bytes((V/'stage_profile.csv').read_bytes())
 state.update(state='LOAD_ONLY_RETURNED_AWAITING_INDEPENDENT_REVIEW_NO_DUT_CALLS',finished=now())
except BaseException as error:state.update(state='FAILED_NO_AUTOMATIC_RETRY',error=repr(error),finished=now())
finally:
 state['process_after']=members(state.get('child_pgid',-1));save()
 if not state['process_after']:(R/'ACTIVE.lock').unlink(missing_ok=True)
print(json.dumps(state,indent=2))
