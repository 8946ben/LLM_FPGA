"""Finite original/streamed loader comparison; reuse bounded process runner."""
from pathlib import Path
import datetime,hashlib,json,os,shutil,signal,subprocess,time
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
M=ROOT/'module_14_lm_head_v4';E=M/'experiments/d64_stream_loader_20261102';R=M/'reports/d64_stream_loader_20261102_r1'
V=ROOT/'.cache/d64_stream_loader_20261102_r1'
OLD=ROOT/'.cache/p64_full_bank_cosim_20261026_r1/sim/verilog'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def members(group):
 rows=[]
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   stat=(p/'stat').read_text();v=stat[stat.rindex(')')+2:].split()
   if v[0]!='Z' and int(v[2])==group:rows.append({'pid':int(p.name),'start_ticks':v[19],'rss_kib':int(v[21])*os.sysconf('SC_PAGE_SIZE')//1024})
  except OSError:pass
 return rows
def main():
 plan=json.loads((R/'PLAN.json').read_text())
 for n,h in plan['source_sha256'].items():assert sha(ROOT/n)==h,n
 assert not V.exists() and not (R/'WORKFLOW.json').exists()
 assert not (M/'reports/d64_resource_recovery_20261102_r1/ACTIVE.lock').exists()
 V.mkdir();shutil.copytree(OLD/'file_agent',V/'file_agent');shutil.copy2(E/'mem_model.sv',V/'file_agent/mem_model.sv');shutil.copy2(E/'loader_tb.sv',V/'loader_tb.sv')
 (V/'loader.prj').write_text('sv xil_defaultlib "file_agent/file_agent_pkg.sv"\nsv xil_defaultlib "loader_tb.sv"\n')
 # Exact byte pattern permits independent expected-SHA and all-byte checks.
 n=4194304;pattern=bytes((i*17+3)&255 for i in range(256))
 data=pattern*(n//256)
 with (V/'input.dat').open('w') as f:
  f.write('[[[runtime]]]\n[[transaction]] 0\n')
  for i in range(0,n,16):f.write('0x'+data[i:i+16][::-1].hex()+'\n')
  f.write('[[/transaction]]\n[[[/runtime]]]\n')
 # Keep malformed fixtures tiny; expected errors must come from the DUT loader.
 goodword='0x'+data[:16][::-1].hex()+'\n'
 fixtures={
  'short':'[[[runtime]]]\n[[transaction]] 0\n[[/transaction]]\n[[[/runtime]]]\n',
  'long':'[[[runtime]]]\n[[transaction]] 0\n'+goodword*2+'[[/transaction]]\n[[[/runtime]]]\n',
  'badhex':'[[[runtime]]]\n[[transaction]] 0\n0xzz000000000000000000000000000000\n[[/transaction]]\n[[[/runtime]]]\n',
  'missing_trailer':'[[[runtime]]]\n[[transaction]] 0\n'+goodword+'[[/transaction]]\n'}
 for name,text in fixtures.items():(V/(name+'.dat')).write_text(text)
 state={'state':'PREPARING','started':stamp(),'parent_pid':os.getpid(),'parent_proc_stat':Path('/proc/self/stat').read_text(),'cases':{},'automatic_next_stage':False,'board':'NOT_RUN'}
 def save():(R/'WORKFLOW.json').write_text(json.dumps(state,indent=2)+'\n')
 def stop(p):
  try:os.killpg(p.pid,signal.SIGTERM)
  except ProcessLookupError:pass
  try:p.wait(timeout=10)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
 def run(name,command,negative=False):
  outdir=R/name;outdir.mkdir();state.update(state='EXECUTING_'+name.upper(),case=name);save()
  peak=0
  with (outdir/'tool.log').open('w') as out,(outdir/'resources.jsonl').open('w') as res:
   p=subprocess.Popen(['bash','-c','source /tools/Xilinx/Vitis/2022.2/settings64.sh >/dev/null 2>&1; exec '+command],cwd=V,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
   state.update(child_pid=p.pid,child_pgid=p.pid,command=command);save();start=time.monotonic()
   try:
    while True:
     procs=members(p.pid);rss=sum(x['rss_kib'] for x in procs);peak=max(peak,rss)
     avail=next(int(x.split()[1]) for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'));elapsed=time.monotonic()-start
     sample={'utc':stamp(),'elapsed_s':elapsed,'group_rss_kib':rss,'available_kib':avail,'members':procs};res.write(json.dumps(sample)+'\n');res.flush()
     reason=('STOP_REQUESTED' if (R/'STOP_REQUESTED').exists() else 'PHASE_TIMEOUT_600S' if elapsed>600 else 'MEM_AVAILABLE_BELOW_32GIB' if avail<32*1024*1024 else 'GROUP_RSS_ABOVE_48GIB' if rss>48*1024*1024 else None)
     if reason:state['stop_evidence']={'reason':reason,**sample};save();stop(p);raise RuntimeError(reason)
     if p.poll() is not None:break
     time.sleep(1)
    assert not members(p.pid),'group remains'
   except BaseException:stop(p);raise
  log=(outdir/'tool.log').read_text(errors='replace')
  if negative:
   assert any(x.startswith('UVM_FATAL') and '[stream_format]' in x for x in log.splitlines()),'not expected loader rejection'
   assert not any(x.startswith('LOADER_DIFF_PASS ') for x in log.splitlines())
  else:
   assert p.returncode==0,(name,p.returncode)
   if name!='elaborate':
    assert any(x.startswith('LOADER_DIFF_PASS ') for x in log.splitlines())
    assert not any(x.startswith(('UVM_FATAL','UVM_ERROR','ERROR:','Fatal:')) for x in log.splitlines())
    assert (V/'loaded.bin').read_bytes()==data,'independent full dump mismatch'
    shutil.copy2(V/'loaded.bin',outdir/'loaded.bin')
  state['cases'][name]={'returncode':p.returncode,'expected_rejection':negative,'elapsed_s':elapsed,'peak_group_rss_kib':peak};save()
 (R/'ACTIVE.lock').write_text(str(os.getpid()));save()
 try:
  run('elaborate','/tools/Xilinx/Vivado/2022.2/bin/xelab xil_defaultlib.loader_tb -prj loader.prj -L uvm -L xil_defaultlib -i ./file_agent -relax -debug all -s stream_loader_r1')
  for name,mode,offset in [('original_4MiB',0,0),('stream_4MiB',1,0),('stream_offset97',1,97)]:
   run(name,'/tools/Xilinx/Vivado/2022.2/bin/xsim stream_loader_r1 -runall -testplusarg MODE='+str(mode)+' -testplusarg OFFSET='+str(offset))
  for name in fixtures:
   run('reject_'+name,'/tools/Xilinx/Vivado/2022.2/bin/xsim stream_loader_r1 -runall -testplusarg MODE=1 -testplusarg NBYTES=16 -testplusarg INPUT='+name+'.dat',True)
  state.update(state='TOOL_PASS_AWAITING_INDEPENDENT_REVIEW',finished=stamp())
 except BaseException as e:state.update(state='FAILED_NO_AUTOMATIC_RETRY',error=repr(e),finished=stamp())
 finally:state['process_after']=members(state.get('child_pgid',-1));save();(R/'ACTIVE.lock').unlink(missing_ok=True)
 print(json.dumps(state,indent=2))
if __name__=='__main__':main()
