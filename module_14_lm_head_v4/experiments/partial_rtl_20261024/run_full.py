"""One official complete-configuration CoSim, no automatic downstream EDA."""
from pathlib import Path
import datetime,hashlib,json,os,shutil,socket,subprocess
ROOT=Path(__file__).resolve().parents[3];E=Path(__file__).resolve().parent
R=ROOT/'module_14_lm_head_v4/reports/partial_rtl_20261024_r1/full_r1'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(p,x):
    p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(x,indent=2)+'\n');tmp.replace(p)
def main():
    assert socket.gethostname()=='nvidia-Super-Server';os.nice(10)
    assert json.loads((R.parent/'r4/INDEPENDENT_REVIEW.json').read_text())['state']=='PASS_SELECTOR_RTL_FULL_ARRAYS_AND_AXI_STALLS'
    plan=json.loads((R/'PLAN.json').read_text());assert not (R/'FULL_WORKFLOW.json').exists()
    for name,h in plan['source_sha256'].items():
        if name==plan['only_path_rebind']['path']:h=plan['only_path_rebind']['remote_sha256']
        assert sha(ROOT/name)==h,name
    before=ROOT/'.cache/p64_r3/csynth/hls';after=ROOT/'.cache/p64_rtl_full_r1/hls'
    assert not after.exists() and not (R/'STOP_REQUESTED').exists()
    after.parent.mkdir(parents=True);shutil.copytree(before,after)
    old={str(p.relative_to(before)):sha(p) for p in (before/'solution1/syn/verilog').glob('*') if p.is_file()}
    for name,h in old.items():assert sha(after/name)==h
    fixture=E/'full_fixtures';fixture.mkdir()
    original=ROOT/'module_14_lm_head_v4/experiments/partial_hw_20261024/fixtures'
    for p in original.glob('old_chinese.*.bin'):shutil.copy2(p,fixture/p.name)
    shutil.copy2(original/'weight_paths.txt',fixture/'weight_paths.txt')
    write(R/'SYNTHESIS_REUSE.json',dict(state='PASS_IDENTICAL_R3_GENERATED_RTL_CLONE',files=old,original=str(before),clone=str(after),fifo_resizing=False,random_stall=True,full_valid_calls=1))
    active=R/'ACTIVE.lock';fd=os.open(str(active),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
    workflow=R/'FULL_WORKFLOW.json';state=dict(state='EXECUTING',phase='OFFICIAL_FULL_COSIM',started=now(),parent_pid=os.getpid(),parent_proc_stat=Path('/proc/self/stat').read_text(),plan_sha256=sha(R/'PLAN.json'),tool='2022.2',board='NOT_RUN',automatic_next_stage=False)
    write(active,state);write(workflow,state)
    try:
        command=['bash','-c','source /tools/Xilinx/Vitis/2022.2/settings64.sh >/dev/null 2>&1; exec /tools/Xilinx/Vitis_HLS/2022.2/bin/vitis_hls -f "$1"','partial-full',str(E/'full_cosim.tcl')]
        with (R/'cosim.log').open('w') as log:
            p=subprocess.Popen(command,cwd=str(after.parent),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            state.update(child_pid=p.pid,child_pgid=p.pid,command=command);write(active,state);write(workflow,state);code=p.wait()
        state['wrapper_exit_code']=code;log=(R/'cosim.log').read_text(errors='replace')
        assert code==0 and 'PARTIAL_FULL_COSIM_TOOL_PASS' in log and 'PARTIAL_FULL_RTL_REFERENCE_PASS calls=1 full_arrays=1' in log
        reports=list((after/'solution1/sim/report').glob('*'))
        assert any('Pass' in p.read_text(errors='replace') for p in reports if p.is_file())
        actual=fixture/'actual_RTL_full_chinese.bin';assert actual.is_file();shutil.copy2(actual,R/actual.name)
        for name,h in old.items():assert sha(before/name)==h,name
        state['state']='TOOL_COMPLETE_AWAITING_FULL_ARRAY_AND_FIFO_REVIEW'
    except BaseException as ex:state.update(state='FAILED_NO_AUTOMATIC_RETRY',error=repr(ex));raise
    finally:
        state['finished']=now();write(workflow,state);active.unlink()
    print(json.dumps(state))
if __name__=='__main__':main()
