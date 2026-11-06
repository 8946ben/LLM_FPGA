"""Bounded XSim memory experiments; no full DUT and no automatic continuation."""
from pathlib import Path
import datetime,hashlib,json,os,shutil,signal,subprocess,time

ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
M=ROOT/'module_14_lm_head_v4';E=M/'experiments/d64_resource_recovery_20261102';R=M/'reports/d64_resource_recovery_20261102_r1'
OLD=ROOT/'.cache/p64_full_bank_cosim_20261026_r1/sim/verilog'
CACHE=ROOT/'.cache/d64_resource_recovery_20261102_r1'
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot(group):
    result=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            stat=(p/'stat').read_text();v=stat[stat.rindex(')')+2:].split()
            if v[0]!='Z' and int(v[2])==group:
                result.append({'pid':int(p.name),'start_ticks':v[19],'rss_kib':int(v[21])*os.sysconf('SC_PAGE_SIZE')//1024,
                  'cmd':(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')[:900]})
        except OSError:pass
    return result
def main():
    plan=json.loads((R/'PLAN.json').read_text())
    for n,h in plan['source_sha256'].items():assert sha(ROOT/n)==h,n
    assert sha(ROOT/plan['baseline_model'])==plan['baseline_sha256']
    assert not (R/'WORKFLOW.json').exists() and not CACHE.exists()
    assert not (M/'reports/full_bank_cosim_20261026_r1/ACTIVE.lock').exists()
    state={'state':'PREPARING','started':stamp(),'parent_pid':os.getpid(),'parent_proc_stat':Path('/proc/self/stat').read_text(),
      'plan_sha256':sha(R/'PLAN.json'),'automatic_next_stage':False,'board':'NOT_RUN','cases':{}}
    def save():(R/'WORKFLOW.json').write_text(json.dumps(state,indent=2)+'\n')
    def kill(p):
        if snapshot(p.pid):
            try:os.killpg(p.pid,signal.SIGTERM)
            except ProcessLookupError:pass
        try:p.wait(timeout=10)
        except subprocess.TimeoutExpired:
            try:os.killpg(p.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            p.wait()
    def run(case,phase,args,v):
        state.update(state='EXECUTING_'+case.upper()+'_'+phase.upper(),case=case,phase=phase);save()
        outdir=R/case;outdir.mkdir(exist_ok=True)
        with (outdir/(phase+'.log')).open('w') as out,(outdir/(phase+'_resources.jsonl')).open('w') as res:
            p=subprocess.Popen(['bash','-c','source /tools/Xilinx/Vitis/2022.2/settings64.sh >/dev/null 2>&1; exec '+args],cwd=v,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
            state.update(child_pid=p.pid,child_pgid=p.pid,command=args);save();start=time.monotonic();peak=0
            try:
                while True:
                    procs=snapshot(p.pid);rss=sum(x['rss_kib'] for x in procs);peak=max(peak,rss)
                    available=next(int(x.split()[1]) for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'))
                    elapsed=time.monotonic()-start
                    sample={'utc':stamp(),'elapsed_s':elapsed,'available_kib':available,'group_rss_kib':rss,'members':procs}
                    res.write(json.dumps(sample)+'\n');res.flush()
                    reason=None
                    if (R/'STOP_REQUESTED').exists():reason='STOP_REQUESTED'
                    elif elapsed>600:reason='PHASE_TIMEOUT_600S'
                    elif available<32*1024*1024:reason='MEM_AVAILABLE_BELOW_32GIB'
                    elif rss>48*1024*1024:reason='GROUP_RSS_ABOVE_48GIB'
                    if reason:
                        state['stop_evidence']={'reason':reason,**sample};save();kill(p);raise RuntimeError(reason)
                    if p.poll() is not None:break
                    time.sleep(1)
                assert p.returncode==0,(case,phase,p.returncode)
                assert not snapshot(p.pid),'Residual group members'
                state['cases'].setdefault(case,{})[phase]={'returncode':p.returncode,'elapsed_s':elapsed,'peak_group_rss_kib':peak}
                save()
            except BaseException:
                kill(p);raise
    (R/'ACTIVE.lock').write_text(str(os.getpid()));save()
    try:
        for case in plan['cases']:
            v=CACHE/case;v.mkdir(parents=True)
            shutil.copytree(OLD/'file_agent',v/'file_agent')
            model=ROOT/plan['baseline_model'] if case=='byte_bench' else E/'mem_model.sv'
            shutil.copy2(model,v/'file_agent/mem_model.sv')
            top='bank_memory_tb' if case=='packed_unit' else 'memory_bench_tb'
            shutil.copy2(E/(top+'.sv'),v/(top+'.sv'))
            (v/'unit.prj').write_text('sv xil_defaultlib "file_agent/file_agent_pkg.sv"\nsv xil_defaultlib "'+top+'.sv"\n')
            snapshot_name='resource_'+case
            run(case,'elaborate','/tools/Xilinx/Vivado/2022.2/bin/xelab xil_defaultlib.'+top+' -prj unit.prj -L uvm -L xil_defaultlib -i ./file_agent -relax -debug all -s '+snapshot_name,v)
            run(case,'simulate','/tools/Xilinx/Vivado/2022.2/bin/xsim '+snapshot_name+' -runall',v)
            log=(R/case/'simulate.log').read_text(errors='replace')
            marker='BANK_MEMORY_UNIT_PASS ' if case=='packed_unit' else 'MEMORY_BENCH_PASS '
            assert any(line.startswith(marker) for line in log.splitlines()),(case,'actual marker missing')
            if case=='packed_unit':assert any(x.startswith('PACKED_LANES_PASS ') for x in log.splitlines())
            assert not any(line.startswith(('UVM_ERROR','UVM_FATAL','Fatal:','ERROR:')) for line in log.splitlines())
            name='memory_events.csv' if case=='packed_unit' else 'bench_events.csv'
            shutil.copy2(v/name,R/case/name)
        for n,h in plan['source_sha256'].items():assert sha(ROOT/n)==h,n
        assert sha(ROOT/plan['baseline_model'])==plan['baseline_sha256']
        state.update(state='TOOL_PASS_AWAITING_INDEPENDENT_REVIEW',finished=stamp())
    except BaseException as e:state.update(state='FAILED_NO_AUTOMATIC_RETRY',error=repr(e),finished=stamp())
    finally:
        state['process_after']=snapshot(state.get('child_pgid',-1));save();(R/'ACTIVE.lock').unlink(missing_ok=True)
    print(json.dumps(state,indent=2))

if __name__=='__main__':main()
