"""Single finite stage on user-authorized STHL. Python3.9 compatible."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,platform,shutil,socket,subprocess,sys
E=Path(__file__).resolve().parent;ROOT=E.parents[2];R=ROOT/'module_14_lm_head_v4/reports/partial_hw_20261024_r1'
TOOL=Path('/tools/Xilinx/Vitis_HLS/2022.2/bin/vitis_hls')
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');tmp.replace(p)
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def version():
    result=subprocess.run(['bash','-c','source /tools/Xilinx/Vitis/2022.2/settings64.sh >/dev/null 2>&1; exec /tools/Xilinx/Vitis_HLS/2022.2/bin/vitis_hls -version'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,check=True)
    assert 'v2022.2' in result.stdout;return result.stdout
def prepare():
    import numpy as np
    lock=R/'REMOTE_ENV_LOCK.json';assert not lock.exists(),'Preserve existing environment entry'
    assert socket.gethostname()=='nvidia-Super-Server'
    plan=read(R/'PLAN.json');key='module_14_lm_head_v4/reports/layout_topk_20261024_r1/assets/tiled_W_B1024.bin'
    w=ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin';p=ROOT/key
    assert sha(w)==plan['source_sha256']['artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin']
    assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True)
    raw=np.memmap(w,dtype='<u2',mode='r',shape=(151936,896));tiled=np.memmap(p,dtype='<u2',mode='w+',shape=(149,896,1024))
    for n in range(149):
        size=min(1024,151936-n*1024);tiled[n]=0;tiled[n,:,:size]=raw[n*1024:n*1024+size].T
    tiled.flush();assert sha(p)==plan['source_sha256'][key]
    for name,expected in plan['source_sha256'].items():assert sha(ROOT/name)==expected,name
    paths=E/'fixtures/weight_paths.txt';before=sha(paths);shutil.copy2(paths,R/'weight_paths_before_rebind.txt')
    paths.write_text(str(p)+'\n'+str(w)+'\n',encoding='ascii')
    rebound=sha(paths)
    write(lock,dict(created=now(),host=socket.gethostname(),user=os.environ.get('USER'),root=str(ROOT),
        platform=platform.platform(),python=sys.version,numpy=np.__version__,tool=str(TOOL),tool_sha256=sha(TOOL),tool_version=version(),
        source_plan_sha256=sha(R/'PLAN.json'),all110_transferred_or_rebuilt_sources_verified=True,
        only_path_rebind=dict(path=paths.relative_to(ROOT).as_posix(),before_sha256=before,after_sha256=rebound),
        remote_script_sha256=sha(Path(__file__)),canonical_and_tiled_bit_sha_unchanged=True,
        source_tool='2021.1 Windows native functional',execution_tool='2022.2 Linux HLS separately qualified',
        system_config_changed=False,container_access=False,board='NOT_RUN'))
    print(json.dumps(dict(state='REMOTE_PREPARED_SHA_PASS',root=str(ROOT),tool='2022.2',files=len(plan['source_sha256']))))
def run(phase):
    assert phase in ['csim','csynth'];plan=read(R/'PLAN.json');lock=read(R/'REMOTE_ENV_LOCK.json')
    assert socket.gethostname()=='nvidia-Super-Server'
    assert sha(Path(__file__))==lock['remote_script_sha256'] and sha(R/'PLAN.json')==lock['source_plan_sha256']
    if (R/'STOP_REQUESTED').exists():raise InterruptedError('Stop requested')
    for name,expected in plan['source_sha256'].items():
        if name==lock['only_path_rebind']['path']:expected=lock['only_path_rebind']['after_sha256']
        assert sha(ROOT/name)==expected,name
    if phase=='csynth':assert read(R/'CSIM_QUALIFICATION.json')['state']=='PASS_FULL_CSIM_ARRAYS'
    workflow=R/(phase+'_WORKFLOW.json');assert not workflow.exists(),'Preserve prior run'
    active=R/'ACTIVE.lock';fd=os.open(str(active),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
    state=dict(phase=phase,state='EXECUTING',started=now(),parent_pid=os.getpid(),parent_proc_stat=Path('/proc/self/stat').read_text(),
        cwd=str(ROOT),host=socket.gethostname(),tool_version='2022.2',board='NOT_RUN',automatic_next_stage=False,
        source_plan_sha256=sha(R/'PLAN.json'),remote_env_lock_sha256=sha(R/'REMOTE_ENV_LOCK.json'))
    write(workflow,state);write(active,state)
    try:
        os.nice(10);env=os.environ.copy();env['PARTIAL_PROTO_MODE']=phase;env['OMP_NUM_THREADS']='4';env['MKL_NUM_THREADS']='4'
        cwd=R/('run_'+phase);cwd.mkdir()
        command=['bash','-c','source /tools/Xilinx/Vitis/2022.2/settings64.sh >/dev/null 2>&1; exec /tools/Xilinx/Vitis_HLS/2022.2/bin/vitis_hls -f "$1"','partial-hls',str(E/'proto.tcl')]
        with (R/(phase+'.log')).open('w') as log:
            proc=subprocess.Popen(command,cwd=str(cwd),env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            state['child_pid']=proc.pid;state['child_pgid']=proc.pid;state['command']=command;write(workflow,state);write(active,state)
            code=proc.wait()
        text=(R/(phase+'.log')).read_text(errors='replace');state['wrapper_exit_code']=code
        assert 'PARTIAL_PROTO_'+phase+'=PASS' in text,'Actual Tcl completion marker absent'
        if phase=='csim':
            assert 'PARTIAL_PROTO_CSIM_ALL_PASS valid=11 unique=9 negative=6' in text
            target=R/'csim_actual';target.mkdir()
            for _,label,_ in plan['expected_cases']:shutil.copy2(E/('fixtures/actual_'+label+'.bin'),target/('actual_'+label+'.bin'))
        state['state']='TOOL_COMPLETE_AWAITING_INDEPENDENT_REVIEW'
    except BaseException as exc:
        state['state']='FAILED_NO_AUTOMATIC_RETRY';state['error']=repr(exc);raise
    finally:
        state['finished']=now();write(workflow,state);active.unlink()
    print(json.dumps(dict(phase=phase,state=state['state'])))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=['prepare','csim','csynth'],required=True);args=ap.parse_args()
    if args.phase=='prepare':prepare()
    else:run(args.phase)
