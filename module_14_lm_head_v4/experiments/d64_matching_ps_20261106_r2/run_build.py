from pathlib import Path
import datetime, hashlib, json, os, re, shlex, shutil, signal, subprocess, sys, time

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
    with (d / 'tool.log').open(errors='replace') as log_source:
        lines = [x.rstrip(chr(10)) for x in log_source if x.startswith(('Fatal:', 'ERROR:', 'UVM_FATAL', 'UVM_ERROR', 'NATIVE_GATE_PASS')) or any((marker in x for marker in ['GATE_EXPECTED_REJECTION_MISSING', 'GATE_WATCHDOG', 'GATE_UNKNOWN_CASE']))]
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

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()

ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1');M=ROOT/'module_14_lm_head_v4';E=M/'experiments/d64_matching_ps_20261106_r2';BASE=M/'reports/d64_matching_ps_20261106_r2';R=BASE/'execution';V=ROOT/'.cache/d64_matching_ps_20261106_r2'
assert sys.argv[1:]==['--execute'];plan=json.loads((E/'PLAN.json').read_text());assert all(sha(E/name)==h for name,h in plan['source_sha256'].items());review=json.loads((E/'INDEPENDENT_HARDWARE_REVIEW.json').read_text());assert review['state']=='PASS_BIT_XSA_IDENTITY_ONLY_NOT_BOARD'
assert sha(M/'reports/d64_bit_xsa_20261106_r1/hardware/m14_d64_200m.xsa')==review['xsa_sha256']
old=M/'reports/d64_bit_xsa_20261106_r1/execution';w=json.loads((old/'WORKFLOW.json').read_text());assert w['state']=='BIT_XSA_RETURNED_AWAITING_INDEPENDENT_REVIEW' and not members(w['child_pgid']) and not list((M/'reports').rglob('ACTIVE.lock'))
prior=M/'reports/d64_matching_ps_20261106_r1/execution';pw=json.loads((prior/'WORKFLOW.json').read_text());assert pw['state']=='FAILED_NO_AUTOMATIC_RETRY' and pw['error']=="AssertionError(('bsp', 1))" and not members(pw['child_pgid'])
ids={(6319,'354846648')}
for line in (prior/'bsp/resources.jsonl').open():ids.update((item['pid'],item['start_ticks']) for item in json.loads(line)['members'])
for pid,start in ids:
 p=Path('/proc')/str(pid)/'stat';assert not p.exists() or parts(p.read_text())[19]!=start or parts(p.read_text())[0]=='Z'
assert not R.exists() and not V.exists();R.mkdir(parents=True);V.mkdir();os.environ['MAKEFLAGS']='-j2';state=dict(state='PREPARING',started=now(),parent_pid=os.getpid(),parent_proc_stat=Path('/proc/self/stat').read_text(),phases={},scope='Offline matching standalone BSP and strict A53 ELF build only; no board')
(R/'ACTIVE.lock').write_text(str(os.getpid()));save()
try:
 run('bsp','/tools/Xilinx/Vitis/2022.2/bin/xsct -nodisp '+shlex.quote(str(E/'platform.tcl')),1800)
 assert (R/'bsp/tool.log').read_text().count('D64_MATCHING_BSP_RETURNED=PASS_OFFLINE_ONLY')==1
 run('elf','/home/zhangben/anaconda3/bin/python '+shlex.quote(str(E/'build_software.py')),600)
 assert (R/'elf/tool.log').read_text().count('D64_MATCHING_ELF_RETURNED=PASS_BUILD_ONLY_NOT_BOARD')==1
 state.update(state='BSP_ELF_RETURNED_AWAITING_INDEPENDENT_REVIEW',finished=now())
except BaseException as ex:state.update(state='FAILED_NO_AUTOMATIC_RETRY',error=repr(ex),finished=now())
finally:
 state['process_after']=members(state.get('child_pgid',-1));save()
 if not state['process_after']:(R/'ACTIVE.lock').unlink(missing_ok=True)
print(json.dumps(state,indent=2))
