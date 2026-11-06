from pathlib import Path
import datetime,hashlib,json,os,shutil,signal,subprocess,time,re
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1');M=ROOT/'module_14_lm_head_v4'
E=M/'experiments/memory_control_regression_20261103_r1';R=M/'reports/memory_control_regression_20261103_r1';V=ROOT/'.cache/memory_control_regression_20261103_r1'
OLD=ROOT/'.cache/p64_full_bank_cosim_20261102_r2/sim/verilog'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def members(group):
 out=[]
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   s=(p/'stat').read_text();a=s[s.rindex(')')+2:].split()
   if a[0]!='Z' and int(a[2])==group:out.append(dict(pid=int(p.name),start_ticks=a[19],rss_kib=int(a[21])*os.sysconf('SC_PAGE_SIZE')//1024))
  except OSError:pass
 return out
def main():
 plan=json.loads((R/'PLAN.json').read_text())
 assert not (M/'reports/full_bank_cosim_20261102_r2/ACTIVE.lock').exists()
 assert not list((M/'reports').glob('memory_*/ACTIVE.lock'))
 assert not V.exists() and not (R/'WORKFLOW.json').exists()
 for n,h in plan['sources'].items():assert sha(ROOT/n)==h,n
 V.mkdir();shutil.copytree(OLD/'axivip',V/'axivip');shutil.copy2(E/'allocation_tb.sv',V/'allocation_tb.sv');shutil.copy2(OLD/'svtb/misc_interface.sv',V/'misc_interface.sv')
 shutil.copy2(E/'original_latency.svh',V/'original_latency.svh');shutil.copy2(E/'lm_head_v4_partial_proto_control_s_axi.v',V/'lm_head_v4_partial_proto_control_s_axi.v')
 (V/'micro.prj').write_text('sv xil_defaultlib "misc_interface.sv"\nsv xil_defaultlib "axivip/axi_if.sv"\nsv xil_defaultlib "axivip/axi_pkg.sv"\nverilog xil_defaultlib "lm_head_v4_partial_proto_control_s_axi.v"\nsv xil_defaultlib "allocation_tb.sv"\n')
 state={'state':'PREPARING','started':stamp(),'parent_pid':os.getpid(),'parent_proc_stat':Path('/proc/self/stat').read_text(),'phases':{},'automatic_next_stage':False,'board':'NOT_RUN'}
 def save():(R/'WORKFLOW.json').write_text(json.dumps(state,indent=2)+'\n')
 def kill(p):
  try:os.killpg(p.pid,signal.SIGTERM)
  except ProcessLookupError:pass
  try:p.wait(timeout=10)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
  deadline=time.monotonic()+10
  while members(p.pid) and time.monotonic()<deadline:time.sleep(.1)
  if members(p.pid):os.killpg(p.pid,signal.SIGKILL)
 def run(phase,cmd):
  state.update(state='EXECUTING_'+phase.upper(),phase=phase);save();peak=0;d=R/phase;d.mkdir()
  with (d/'tool.log').open('w') as out,(d/'resources.jsonl').open('w') as res:
   p=subprocess.Popen(['bash','-c','source /tools/Xilinx/Vitis/2022.2/settings64.sh >/dev/null 2>&1; exec '+cmd],cwd=V,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
   state.update(child_pid=p.pid,child_pgid=p.pid,command=cmd);save();start=time.monotonic()
   try:
    while True:
     procs=members(p.pid);rss=sum(x['rss_kib'] for x in procs);peak=max(peak,rss);elapsed=time.monotonic()-start
     avail=next(int(x.split()[1]) for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'))
     sample=dict(utc=stamp(),elapsed_s=elapsed,rss_kib=rss,available_kib=avail,members=procs);res.write(json.dumps(sample)+'\n');res.flush()
     if p.poll() is not None:break
     reason='STOP_REQUESTED' if (R/'STOP_REQUESTED').exists() else 'TIMEOUT_300S' if elapsed>300 else 'GROUP_RSS_OVER_8GIB' if rss>8*1048576 else 'AVAILABLE_BELOW_32GIB' if avail<32*1048576 else None
     if reason:state['stop_evidence']={'reason':reason,**sample};save();kill(p);raise RuntimeError(reason)
     time.sleep(.5)
    assert p.returncode==0,(phase,p.returncode)
    assert not members(p.pid)
   except BaseException:kill(p);raise
  if phase.startswith('mode_'):
   lines=(d/'tool.log').read_text(errors='replace').splitlines()
   assert any(x.startswith('ALLOCATION_MICRO_PASS ') for x in lines)
   assert not any(x.startswith(('UVM_FATAL','UVM_ERROR','Fatal:','ERROR:')) and not re.fullmatch(r'UVM_(?:FATAL|ERROR)\s*:\s*0\s*',x) for x in lines)
   shutil.copy2(V/'allocation_samples.csv',d/'allocation_samples.csv');shutil.copy2(V/'results.csv',d/'results.csv');shutil.copy2(V/'wire_events.csv',d/'wire_events.csv')
  state['phases'][phase]={'elapsed_s':elapsed,'peak_group_rss_kib':peak};save()
 (R/'ACTIVE.lock').write_text(str(os.getpid()));save()
 try:
  run('elaborate','/tools/Xilinx/Vivado/2022.2/bin/xelab xil_defaultlib.allocation_tb -prj micro.prj -L uvm -L xil_defaultlib -i ./axivip -i . -relax -debug all -s allocation_micro')
  for mode in range(3):run('mode_'+str(mode),'/tools/Xilinx/Vivado/2022.2/bin/xsim allocation_micro -runall -testplusarg MODE='+str(mode)+' -testplusarg UVM_VERBOSITY=UVM_LOW')
  state.update(state='TOOL_PASS_AWAITING_INDEPENDENT_REVIEW',finished=stamp())
 except BaseException as e:state.update(state='FAILED_NO_AUTOMATIC_RETRY',error=repr(e),finished=stamp())
 finally:state['process_after']=members(state.get('child_pgid',-1));save();(R/'ACTIVE.lock').unlink(missing_ok=True)
 print(json.dumps(state,indent=2))
if __name__=='__main__':main()
