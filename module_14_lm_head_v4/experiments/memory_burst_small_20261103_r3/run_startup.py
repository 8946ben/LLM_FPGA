"""Remote bounded initialization/prefix runner. No C postcheck or full call."""
from pathlib import Path
import os,signal,subprocess,json,hashlib,shutil,datetime,time,re,csv
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1');M=ROOT/'module_14_lm_head_v4'
NAME='memory_burst_small_20261103_r3';E=M/'experiments'/NAME;R=M/'reports'/NAME
OLD=ROOT/'.cache/p64_full_bank_cosim_20261102_r2/sim/verilog';NEW=ROOT/'.cache'/NAME;V=NEW/'verilog'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def members(group):
 out=[]
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   a=(p/'stat').read_text().split(')')[-1].split()
   if a[0]!='Z' and int(a[2])==group:out.append(dict(pid=int(p.name),start_ticks=a[19],rss_kib=int(a[21])*os.sysconf('SC_PAGE_SIZE')//1024))
  except OSError:pass
 return out
def main():
 plan=json.loads((R/'PLAN.json').read_text());guard=plan['guards']
 assert json.loads((E/'predecessor_review.json').read_text())['state']=='PASS_INDEPENDENT_FULL_PROJECT_SMALL_LOADER_ACCESS_DIAGNOSIS'
 assert not NEW.exists() and not (R/'WORKFLOW.json').exists()
 assert not list((M/'reports').glob('memory_*/ACTIVE.lock'))
 assert not (M/'reports/full_bank_cosim_20261102_r2/ACTIVE.lock').exists()
 for p,h in plan['source_sha256'].items():assert sha(ROOT/p)==h,p
 fullplan=json.loads((M/'reports/full_bank_cosim_20261102_r2/PLAN.json').read_text())
 for p,h in fullplan['source_sha256'].items():assert sha(ROOT/p)==h,p
 for p,h in fullplan['reuse_sources'].items():assert sha(OLD/p)==h,p
 for p,h in plan['baseline_sources'].items():assert sha(OLD/p)==h,p
 avail=next(int(x.split()[1]) for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'))
 assert avail>=guard['initial_available_gib']*1048576,'Insufficient safe initial memory'
 state=dict(state='PREPARING',started=stamp(),parent_pid=os.getpid(),parent_proc_stat=Path('/proc/self/stat').read_text(),phases={},full_m14='NOT_RUN',board='NOT_RUN',automatic_next_stage=False)
 def save():(R/'WORKFLOW.json').write_text(json.dumps(state,indent=2)+'\n')
 def stop(p):
  try:os.killpg(p.pid,signal.SIGTERM)
  except ProcessLookupError:pass
  try:p.wait(timeout=10)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
  deadline=time.monotonic()+10
  while members(p.pid) and time.monotonic()<deadline:time.sleep(.1)
  if members(p.pid):os.killpg(p.pid,signal.SIGKILL)
  deadline=time.monotonic()+10
  while members(p.pid) and time.monotonic()<deadline:time.sleep(.1)
  assert not members(p.pid),'Owned group did not drain'
 def run(phase,command,timeout):
  state.update(state='EXECUTING_'+phase.upper(),phase=phase,command=command);save();peak=0
  with (R/(phase+'.log')).open('w') as out,(R/(phase+'_resources.jsonl')).open('w') as resource:
   p=subprocess.Popen(['bash','-c','source /tools/Xilinx/Vitis/2022.2/settings64.sh >/dev/null 2>&1; exec '+command],cwd=V,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
   state.update(child_pid=p.pid,child_pgid=p.pid);save();start=time.monotonic()
   try:
    while True:
     procs=members(p.pid);rss=sum(x['rss_kib'] for x in procs);peak=max(peak,rss);elapsed=time.monotonic()-start
     available=next(int(x.split()[1]) for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'))
     sample=dict(utc=stamp(),elapsed_s=elapsed,group_rss_kib=rss,available_kib=available,members=procs)
     resource.write(json.dumps(sample)+'\n');resource.flush()
     if p.poll() is not None:break
     reason='STOP_REQUESTED' if (R/'STOP_REQUESTED').exists() else 'PHASE_TIMEOUT' if elapsed>timeout else 'GROUP_RSS_OVER_LIMIT' if rss>guard['group_rss_gib']*1048576 else 'AVAILABLE_BELOW_32GIB' if available<guard['running_available_gib']*1048576 else None
     if reason:state['stop_evidence']=dict(reason=reason,**sample);save();stop(p);raise RuntimeError(reason)
     time.sleep(1)
    assert p.returncode==0,(phase,p.returncode);assert not members(p.pid)
   except BaseException:stop(p);raise
  state['phases'][phase]=dict(elapsed_s=elapsed,peak_group_rss_kib=peak);save()
 (R/'ACTIVE.lock').write_text(str(os.getpid()));save()
 try:
  V.mkdir(parents=True)
  for p in OLD.rglob('*'):
   if p.is_file() and p.suffix in ['.v','.sv','.vh','.svh','.prj','.sh']:
    rel=p.relative_to(OLD)
    if any(x in ['xsim.dir','.Xil'] for x in rel.parts):continue
    dest=V/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
  if (OLD/'ieee_proposed').exists():shutil.copytree(OLD/'ieee_proposed',V/'ieee_proposed',symlinks=True)
  replacements={'reference_model.sv':'lm_head_v4_partial_proto_subsystem/lm_head_v4_partial_proto_reference_model.sv',
   'mem_model.sv':'file_agent/mem_model.sv','axi_state.sv':'axivip/axi_state.sv',
   'lm_head_v4_partial_proto_subsys_test_sequence_lib.sv':'svtb/lm_head_v4_partial_proto_subsys_test_sequence_lib.sv'}
  for a,b in replacements.items():shutil.copy2(E/a,V/b)
  for name in ['memory_probe_pkg.sv','memory_prefix.sv']:shutil.copy2(E/name,V/name)
  actual={str(p.relative_to(V)):sha(p) for p in V.rglob('*') if p.is_file() and p.suffix in ['.v','.sv','.vh','.svh']}
  changes=json.loads((E/'CHANGES.json').read_text());changed=set(replacements.values())
  unchanged={}
  for p,h in fullplan['reuse_sources'].items():
   if p in changed:continue
   assert sha(V/p)==h,p;unchanged[p]=h
  assert len(unchanged)==119
  for a,b in replacements.items():assert sha(V/b)==sha(E/a)
  (R/'COMPILED_SOURCES.json').write_text(json.dumps(dict(actual=actual,unchanged_reused=unchanged),indent=2)+'\n')
  prj='sv xil_defaultlib "memory_probe_pkg.sv"\n'+(OLD/'full_bank.prj').read_text()+'\nsv xil_defaultlib "memory_prefix.sv"\n'
  (V/'startup.prj').write_text(prj);(V/'startup.tcl').write_text('run all\nquit\n')
  (NEW/'tv').mkdir();(NEW/'tv/cdatafile').mkdir();(NEW/'tv/rtldatafile').mkdir()
  private=NEW/'tv/cdatafile';names=['c.lm_head_v4_partial_proto.autotvin_'+n+'.dat' for n in ['weights','canonical_weight','tiled_weight']]
  for p in (OLD.parent/'tv/cdatafile').iterdir():
   if p.name not in names:(private/p.name).symlink_to(p)
  pattern=bytes((i*17+3)&255 for i in range(256));block=''.join('0x'+pattern[i:i+16][::-1].hex()+'\n' for i in range(0,256,16))
  with (private/names[0]).open('w') as f:
   f.write('[[[runtime]]]\n[[transaction]] 0\n')
   for i in range(8388608//256):f.write(block)
   f.write('[[/transaction]]\n[[[/runtime]]]\n')
  for n,value in [('canonical_weight',4194304),('tiled_weight',0)]:
   (private/('c.lm_head_v4_partial_proto.autotvin_'+n+'.dat')).write_text('[[[runtime]]]\n[[transaction]] 0\n0x%016x\n[[/transaction]]\n[[[/runtime]]]\n'%value)
  tv=NEW/'tv/cdatafile/c.lm_head_v4_partial_proto.autotvin_weights.dat';assert sha(tv)==plan['input_tv_sha256']
  cmd=next(x.strip() for x in (OLD/'run_xsim.sh').read_text().splitlines() if x.strip().startswith('/tools/Xilinx/Vivado/2022.2/bin/xelab '))
  assert cmd.endswith('-s lm_head_v4_partial_proto')
  cmd=cmd.replace('-prj lm_head_v4_partial_proto.prj','-prj startup.prj').replace('-s lm_head_v4_partial_proto','-debug all -s '+NAME)
  run('elaborate',cmd,guard['elaborate_seconds'])
  run('xsim','/tools/Xilinx/Vivado/2022.2/bin/xsim -testplusarg UVM_VERBOSITY=UVM_LOW -testplusarg UVM_TESTNAME=lm_head_v4_partial_proto_test_lib -testplusarg UVM_TIMEOUT=20000000000000 --noieeewarnings '+NAME+' -tclbatch startup.tcl',guard['simulate_seconds'])
  lines=(R/'xsim.log').read_text(errors='replace').splitlines()
  assert lines.count('BURST_FULL_CONTEXT_PASS bytes=8388608 scalar_writes=1000000 bulk_elements_written=1000000 checksum=1069547520')==1
  assert not any(x.startswith(('UVM_ERROR','UVM_FATAL','ERROR:','Fatal:')) and not re.fullmatch(r'UVM_(?:ERROR|FATAL)\s*:\s*0\s*',x) for x in lines)
  for name in ['memory_phases.csv']:shutil.copy2(V/name,R/name)
  assert sha(tv)==plan['input_tv_sha256']
  for p,h in fullplan['source_sha256'].items():assert sha(ROOT/p)==h,p
  for p,h in fullplan['reuse_sources'].items():assert sha(OLD/p)==h,p
  state.update(state='TOOL_PASS_BURST_SMALL_AWAITING_INDEPENDENT_REVIEW',finished=stamp())
 except BaseException as exc:state.update(state='FAILED_NO_AUTOMATIC_RETRY',error=repr(exc),finished=stamp())
 finally:
  state['process_after']=members(state.get('child_pgid',-1));save();(R/'ACTIVE.lock').unlink(missing_ok=True)
 print(json.dumps(state,indent=2))
if __name__=='__main__':main()
