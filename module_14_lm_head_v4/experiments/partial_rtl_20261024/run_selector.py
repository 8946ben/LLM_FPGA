"""Finite direct RTL test on the already-authorized STHL workspace."""
from pathlib import Path
import datetime,hashlib,json,os,socket,subprocess,sys
ROOT=Path(__file__).resolve().parents[3]
E=Path(__file__).resolve().parent;R=ROOT/'module_14_lm_head_v4/reports/partial_rtl_20261024_r1'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(x,indent=2)+'\n');tmp.replace(p)
def mapped(name):
    prefix='module_14_lm_head_v4/reports/partial_hw_20261024_r1/r3/remote_hls/syn/verilog/'
    return ROOT/'.cache/p64_r3/csynth/hls/solution1/syn/verilog'/name[len(prefix):] if name.startswith(prefix) else ROOT/name
def main():
    assert socket.gethostname()=='nvidia-Super-Server';os.nice(10)
    plan=json.loads((R/'PLAN.json').read_text());assert not (R/'STOP_REQUESTED').exists()
    for name,h in plan['source_sha256'].items():assert sha(mapped(name))==h,name
    build=ROOT/'.cache/p64_rtl_selector_r1';assert not build.exists();build.mkdir(parents=True)
    lock=R/'ACTIVE.lock';fd=os.open(str(lock),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
    state=dict(state='EXECUTING',started=now(),parent_pid=os.getpid(),parent_proc_stat=Path('/proc/self/stat').read_text(),host=socket.gethostname(),plan_sha256=sha(R/'PLAN.json'),board='NOT_RUN',automatic_next_stage=False)
    workflow=R/'SELECTOR_WORKFLOW.json';assert not workflow.exists();write(workflow,state);write(lock,state)
    files=[str(mapped(n)) for n in (E/'radix_sources.txt').read_text().splitlines()]
    steps=[('compile',['xvlog','--sv']+files+[str(E/'axi_stall_memory.sv'),str(E/'radix_tb.sv')]),
           ('elaborate',['xelab','radix_tb','-s','radix_sim','--debug','typical','--mt','4']),
           ('simulate',['xsim','radix_sim','-runall','-onfinish','quit','-testplusarg','fixtures='+str(E/'fixtures')])]
    try:
        for phase,args in steps:
            if (R/'STOP_REQUESTED').exists():raise InterruptedError('STOP requested')
            state['phase']=phase;state['command']=args;write(workflow,state)
            with (R/(phase+'.log')).open('w') as log:
                # argv stays data; no interpolated shell command.
                command=['bash','-c','source /tools/Xilinx/Vitis/2022.2/settings64.sh >/dev/null 2>&1; exec "$@"','rtl-selector']+args
                p=subprocess.Popen(command,cwd=str(build),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                state['child_pid']=p.pid;state['child_pgid']=p.pid;write(workflow,state);write(lock,state)
                try:code=p.wait(timeout=1200)
                except subprocess.TimeoutExpired:
                    import signal
                    os.killpg(p.pid,signal.SIGTERM);p.wait();raise
            state[phase+'_exit_code']=code;assert code==0,(phase,code)
        log=(R/'simulate.log').read_text(errors='replace')
        assert 'RADIX_RTL_ALL_PASS cases=13' in log and log.count('RADIX_CASE_PASS index=')==13
        for name,h in plan['source_sha256'].items():assert sha(mapped(name))==h,name
        state['state']='SELECTOR_RTL_COMPLETE_AWAITING_REVIEW'
    except BaseException as ex:
        state['state']='FAILED_NO_AUTOMATIC_RETRY';state['error']=repr(ex);raise
    finally:
        state['finished']=now();write(workflow,state);lock.unlink()
    print(json.dumps(state))
if __name__=='__main__':main()
