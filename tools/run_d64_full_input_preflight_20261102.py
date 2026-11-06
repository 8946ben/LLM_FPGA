from pathlib import Path
import datetime,hashlib,json,os,shutil,signal,subprocess,time
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
M=ROOT/'module_14_lm_head_v4';E=M/'experiments/d64_full_input_preflight_20261102_r2';R=M/'reports/d64_full_input_preflight_20261102_r2'
V=ROOT/'.cache/d64_full_input_preflight_20261102_r2'
OLD=ROOT/'.cache/p64_full_bank_cosim_20261026_r1/sim'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for data in iter(lambda:f.read(1048576),b''):h.update(data)
 return h.hexdigest()
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def members(group):
 result=[]
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   s=(p/'stat').read_text();v=s[s.rindex(')')+2:].split()
   if v[0]!='Z' and int(v[2])==group:result.append({'pid':int(p.name),'start_ticks':v[19],'rss_kib':int(v[21])*os.sysconf('SC_PAGE_SIZE')//1024})
  except OSError:pass
 return result
def main():
 plan=json.loads((R/'PLAN.json').read_text())
 for n,h in plan['source_sha256'].items():assert sha(ROOT/n)==h,n
 assert not V.exists() and not (R/'WORKFLOW.json').exists()
 for name in ['full_bank_cosim_20261026_r1','d64_resource_recovery_20261102_r1','d64_stream_loader_20261102_r1']:
  assert not (M/'reports'/name/'ACTIVE.lock').exists(),name
 tv=OLD/'tv/cdatafile/c.lm_head_v4_partial_proto.autotvin_weights.dat'
 assert sha(tv)==plan['full_tv_sha256']
 for n,h in plan['weight_sha256'].items():assert sha(ROOT/n)==h,n
 V.mkdir();shutil.copytree(OLD/'verilog/file_agent',V/'file_agent')
 for name in ['mem_model.sv','weights_preflight.svh','full_input_tb.sv']:
  shutil.copy2(E/name,V/('file_agent/mem_model.sv' if name=='mem_model.sv' else name))
 (V/'full_input.prj').write_text('sv xil_defaultlib "file_agent/file_agent_pkg.sv"\nsv xil_defaultlib "full_input_tb.sv"\n')
 state={'state':'PREPARING','started':stamp(),'parent_pid':os.getpid(),'parent_proc_stat':Path('/proc/self/stat').read_text(),'phases':{},'automatic_next_stage':False,'board':'NOT_RUN','dut':'NOT_INSTANTIATED','source_before':'SHA_PASS'}
 def save():(R/'WORKFLOW.json').write_text(json.dumps(state,indent=2)+'\n')
 def stop(p):
  try:os.killpg(p.pid,signal.SIGTERM)
  except ProcessLookupError:pass
  try:p.wait(timeout=10)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
 def run(phase,command):
  state.update(state='EXECUTING_'+phase.upper(),phase=phase);save();peak=0
  with (R/(phase+'.log')).open('w') as out,(R/(phase+'_resources.jsonl')).open('w') as res:
   p=subprocess.Popen(['bash','-c','source /tools/Xilinx/Vitis/2022.2/settings64.sh >/dev/null 2>&1; exec '+command],cwd=V,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
   state.update(child_pid=p.pid,child_pgid=p.pid,command=command);save();start=time.monotonic()
   try:
    while True:
     procs=members(p.pid);rss=sum(x['rss_kib'] for x in procs);peak=max(peak,rss);elapsed=time.monotonic()-start
     avail=next(int(x.split()[1]) for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'))
     sample={'utc':stamp(),'elapsed_s':elapsed,'group_rss_kib':rss,'available_kib':avail,'members':procs};res.write(json.dumps(sample)+'\n');res.flush()
     reason=('STOP_REQUESTED' if (R/'STOP_REQUESTED').exists() else 'PHASE_TIMEOUT_900S' if elapsed>900 else 'MEM_AVAILABLE_BELOW_32GIB' if avail<32*1024*1024 else 'GROUP_RSS_ABOVE_32GIB' if rss>32*1024*1024 else None)
     if reason:state['stop_evidence']={'reason':reason,**sample};save();stop(p);raise RuntimeError(reason)
     if p.poll() is not None:break
     time.sleep(2)
    assert p.returncode==0,(phase,p.returncode)
    assert not members(p.pid)
   except BaseException:stop(p);raise
  state['phases'][phase]={'elapsed_s':elapsed,'peak_group_rss_kib':peak,'returncode':p.returncode};save()
 (R/'ACTIVE.lock').write_text(str(os.getpid()));save()
 try:
  run('elaborate','/tools/Xilinx/Vivado/2022.2/bin/xelab xil_defaultlib.full_input_tb -prj full_input.prj -L uvm -L xil_defaultlib -i ./file_agent -i . -relax -debug all -s full_input_r1')
  run('simulate','/tools/Xilinx/Vivado/2022.2/bin/xsim full_input_r1 -runall')
  log=(R/'simulate.log').read_text(errors='replace');lines=log.splitlines()
  for marker in ['BANK_FULL_INPUT_SENTINEL_PASS checked=1522','FULL_INPUT_BINARY_PASS base=0 bytes=273416192','FULL_INPUT_BINARY_PASS base=273416192 bytes=272269312','FULL_INPUT_MEMORY_PASS bytes=545685504 words=34105344 sentinel=1522 all_bytes=1 dut=0']:
   assert marker in lines,marker
  assert not any(x.startswith(('UVM_FATAL','UVM_ERROR','Fatal:','ERROR:')) for x in lines)
  shutil.copy2(V/'weights_readback.csv',R/'weights_readback.csv')
  assert sha(tv)==plan['full_tv_sha256']
  for n,h in plan['weight_sha256'].items():assert sha(ROOT/n)==h,n
  for n,h in plan['source_sha256'].items():assert sha(ROOT/n)==h,n
  state.update(state='TOOL_PASS_AWAITING_INDEPENDENT_REVIEW',source_after='SHA_PASS',finished=stamp())
 except BaseException as e:state.update(state='FAILED_NO_AUTOMATIC_RETRY',error=repr(e),finished=stamp())
 finally:state['process_after']=members(state.get('child_pgid',-1));save();(R/'ACTIVE.lock').unlink(missing_ok=True)
 print(json.dumps(state,indent=2))
if __name__=='__main__':main()
