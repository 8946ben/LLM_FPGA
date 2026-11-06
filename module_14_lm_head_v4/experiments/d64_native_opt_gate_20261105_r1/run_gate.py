"""STHL-only bounded model gate, manually enabled after full independent PASS.

Preparation only: no upload/launch is performed by creating or importing this file.
Requires --execute and a future MANUAL_GATE_AUTHORIZATION.json bound to real results.
"""
from pathlib import Path
import datetime, hashlib, json, os, re, shutil, signal, subprocess, sys, time

ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
M=ROOT/'module_14_lm_head_v4';NAME='d64_native_opt_gate_20261105_r1'
E=M/'experiments'/NAME;R=M/'reports'/NAME;V=ROOT/'.cache/d64_native_opt_gate_20261105_r1'
FULL=M/'reports/memory_repaired_full_20261103_r1'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def parts(s):return s[s.rindex(')')+2:].split()
def available():
    return next(int(s.split()[1]) for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:'))

def members(pgid):
    found=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            s=parts((p/'stat').read_text())
            if s[0]!='Z' and int(s[2])==pgid:
                found.append(dict(pid=int(p.name),start_ticks=s[19],rss_kib=int(s[21])*os.sysconf('SC_PAGE_SIZE')//1024))
        except OSError:pass
    return found

def require_full_pass():
    # No authorization file exists at preparation time. Never synthesize a PASS.
    auth=json.loads((R/'OPT_GATE_DECISION.json').read_text())
    assert auth['decision']=='QUALIFY_NATIVE_MEMORY_ONLY_AFTER_FULL_PASS'
    assert auth['full_independent_review_sha256']==sha(FULL/'INDEPENDENT_REVIEW.json')
    assert auth['full_workflow_sha256']==sha(FULL/'WORKFLOW.json')
    assert auth['execution_plan_sha256']==sha(R/'EXECUTION_PREPARATION_PLAN.json')
    review=json.loads((FULL/'INDEPENDENT_REVIEW.json').read_text())
    assert review['state']=='PASS_ONE_FULL_GENERATED_RTL_NUMERIC_AND_FINITE_FIFO_CALL'
    workflow=json.loads((FULL/'WORKFLOW.json').read_text())
    assert workflow['state']=='GENERATED_XSIM_AND_C_POSTCHECK_PASS_AWAITING_NUMERIC_AND_FIFO_REVIEW'
    assert workflow['process_after']==[]
    stat=Path('/proc')/str(workflow['parent_pid'])/'stat'
    if stat.exists():
        current=parts(stat.read_text())
        assert current[0]=='Z' or current[19]!=parts(workflow['parent_proc_stat'])[19]
    assert not members(workflow['child_pgid'])
    assert not list((M/'reports').rglob('ACTIVE.lock'))
    assert available()>=32*1048576
    previous=M/'reports/d64_state_suite_20261105_r1'
    prior=json.loads((previous/'WORKFLOW.json').read_text())
    assert sha(previous/'WORKFLOW.json')==auth['previous_suite_workflow_sha256']
    assert prior['state']=='FAILED_NO_AUTOMATIC_RETRY' and prior['stop_evidence']['reason']=='PHASE_TIMEOUT' and prior['process_after']==[]
    prior_stat=Path('/proc')/str(prior['parent_pid'])/'stat'
    if prior_stat.exists():
        current=parts(prior_stat.read_text());assert current[0]=='Z' or current[19]!=parts(prior['parent_proc_stat'])[19]
    assert not members(prior['child_pgid']) and not (previous/'ACTIVE.lock').exists()
    return auth

def main():
    assert sys.argv[1:]==['--execute'], 'Explicit --execute required; this preparation is not an automatic next stage.'
    assert os.name=='posix' and ROOT.is_dir()
    authorization=require_full_pass()
    plan=json.loads((R/'EXECUTION_PREPARATION_PLAN.json').read_text())
    for name,digest in plan['sources'].items():assert sha(ROOT/name)==digest,name
    assert not (R/'WORKFLOW.json').exists() and not V.exists()
    V.mkdir()
    for destination,source in plan['compile_copy_map'].items():
        target=V/destination;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/source,target)
    project='\n'.join('sv xil_defaultlib "'+name+'"' for name in plan['project_order'])+'\n'
    (V/'gate.prj').write_text(project)
    actual={p.relative_to(V).as_posix():sha(p) for p in V.rglob('*') if p.is_file()}
    (R/'COMPILED_SOURCES.json').write_text(json.dumps(actual,indent=2)+'\n')
    state=dict(state='PREPARING',started=now(),parent_pid=os.getpid(),parent_proc_stat=Path('/proc/self/stat').read_text(),
               phases={},board='NOT_RUN',full_m14='NOT_RUN_MODEL_ONLY',automatic_next_stage=False,
               execution_plan_sha256=sha(R/'EXECUTION_PREPARATION_PLAN.json'),authorization=authorization)
    def save():(R/'WORKFLOW.json').write_text(json.dumps(state,indent=2)+'\n')
    def terminate_owned(p):
        if members(p.pid):
            try:os.killpg(p.pid,signal.SIGTERM)
            except ProcessLookupError:pass
        try:p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            try:os.killpg(p.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            p.wait(timeout=10)
        deadline=time.monotonic()+10
        while members(p.pid) and time.monotonic()<deadline:time.sleep(.1)
        if members(p.pid):
            os.killpg(p.pid,signal.SIGKILL)
            deadline=time.monotonic()+10
            while members(p.pid) and time.monotonic()<deadline:time.sleep(.1)
        assert not members(p.pid), 'Owned process group did not drain'
    def run(phase,command,seconds,expected_fatal=None):
        assert available()>=32*1048576
        state.update(state='EXECUTING_'+phase.upper(),phase=phase,command=command);save()
        d=R/phase;d.mkdir();started=time.monotonic();peak=0
        with (d/'tool.log').open('w') as log,(d/'resources.jsonl').open('w') as resource:
            p=subprocess.Popen(['bash','-c','source /tools/Xilinx/Vitis/2022.2/settings64.sh >/dev/null 2>&1 && exec '+command],
                               cwd=V,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            state.update(child_pid=p.pid,child_pgid=p.pid);save()
            try:
                while True:
                    owned=members(p.pid);rss=sum(x['rss_kib'] for x in owned);peak=max(peak,rss)
                    elapsed=time.monotonic()-started;spare=available()
                    sample=dict(utc=now(),elapsed_s=elapsed,rss_kib=rss,available_kib=spare,members=owned)
                    resource.write(json.dumps(sample)+'\n');resource.flush()
                    reason=('STOP_REQUESTED' if (R/'STOP_REQUESTED').exists() else
                            'GROUP_RSS_ABOVE_8GIB' if rss>8*1048576 else
                            'AVAILABLE_BELOW_32GIB' if spare<32*1048576 else
                            'PHASE_TIMEOUT' if elapsed>seconds else None)
                    if reason:
                        state['stop_evidence']=dict(reason=reason,**sample);save();terminate_owned(p);raise RuntimeError(reason)
                    if p.poll() is not None:break
                    time.sleep(.5)
                # Wait for real helpers, not only the launcher. No surviving subgroup is accepted.
                deadline=time.monotonic()+5
                while members(p.pid) and time.monotonic()<deadline:time.sleep(.1)
                assert not members(p.pid)
            except BaseException:
                terminate_owned(p);raise
        lines=(d/'tool.log').read_text(errors='replace').splitlines()
        if expected_fatal is None:
            assert p.returncode==0,(phase,p.returncode)
            assert not any(x.startswith(('Fatal:','ERROR:','UVM_FATAL','UVM_ERROR')) and not re.fullmatch(r'UVM_(?:FATAL|ERROR)\s*:\s*0\s*',x) for x in lines)
            if phase=='positive':assert sum(x.startswith('NATIVE_GATE_PASS case=positive ') for x in lines)==1
        else:
            fatals=[x for x in lines if x.startswith('Fatal:')]
            assert len(fatals)==1 and expected_fatal in fatals[0],(phase,fatals)
            assert not any('GATE_EXPECTED_REJECTION_MISSING' in x or 'GATE_WATCHDOG' in x or 'GATE_UNKNOWN_CASE' in x for x in lines)
            assert not any(x.startswith('NATIVE_GATE_PASS ') for x in lines)
        for name in ['native_wire.csv','memory_phases.csv']:
            if (V/name).exists():shutil.copy2(V/name,d/name)
        state['phases'][phase]=dict(elapsed_s=elapsed,peak_group_rss_kib=peak,returncode=p.returncode,
                                  expected_fatal=expected_fatal,tool_log_sha256=sha(d/'tool.log'))
        save()
    (R/'ACTIVE.lock').write_text(str(os.getpid()));save()
    try:
        run('elaborate','/tools/Xilinx/Vivado/2022.2/bin/xelab xil_defaultlib.native_gate_tb -prj gate.prj -L uvm -L xil_defaultlib -i ./file_agent -i . -relax -debug off -O 3 -s d64_native_opt_gate',300)
        for case in plan['cases']:
            # Each simulation is a fresh kernel but the positive case itself exercises reset retention.
            for name in ['native_wire.csv','memory_phases.csv']:(V/name).unlink(missing_ok=True)
            run(case['case'],'/tools/Xilinx/Vivado/2022.2/bin/xsim d64_native_opt_gate -stats -runall -testplusarg CASE='+case['case'],180,case['expected_fatal'])
        state.update(state='TOOLS_RETURNED_AWAITING_INDEPENDENT_WIRE_AND_RESOURCE_REVIEW',finished=now())
    except BaseException as error:
        state.update(state='FAILED_NO_AUTOMATIC_RETRY',error=repr(error),finished=now())
    finally:
        state['process_after']=members(state.get('child_pgid',-1));save()
        if not state['process_after']:(R/'ACTIVE.lock').unlink(missing_ok=True)
    print(json.dumps(state,indent=2))

if __name__=='__main__':main()
