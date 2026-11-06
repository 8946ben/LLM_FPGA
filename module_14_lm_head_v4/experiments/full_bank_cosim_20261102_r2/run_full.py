"""Manual HLS-generated XSIM + unchanged generated C postcheck, one case.

No cosim_design regeneration: that would overwrite the qualified memory repair.
No synthesized RTL/float/parameter/FIFO changes. Parent reviews are hard gates.
"""
from pathlib import Path
import os,signal,subprocess,json,hashlib,shutil,datetime,time,re,csv
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
M=ROOT/'module_14_lm_head_v4';E=M/'experiments/full_bank_cosim_20261102_r2';R=M/'reports/full_bank_cosim_20261102_r2'
OLD=ROOT/'.cache/p64_rtl_full_r3/hls/solution1/sim';NEW=ROOT/'.cache/p64_full_bank_cosim_20261102_r2/sim';V=NEW/'verilog'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for data in iter(lambda:f.read(1048576),b''):h.update(data)
 return h.hexdigest()
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def members(group):
 result=[]
 for p in Path('/proc').iterdir():
  try:
   s=(p/'stat').read_text();v=s[s.rindex(')')+2:].split()
   if v[0]!='Z' and int(v[2])==group:result.append(int(p.name))
  except (ValueError,OSError):pass
 return result
plan=json.loads((R/'PLAN.json').read_text())
for path,digest in plan['source_sha256'].items():assert sha(ROOT/path)==digest,path
for path,expected in plan['gate_reviews'].items():
 p=ROOT/path;assert sha(p)==expected['sha256'] and json.loads(p.read_text())['state']==expected['state'],path
preview=M/'reports/sim_memory_bank_20261026_r1'
pw=json.loads((preview/'PREVIEW_WORKFLOW.json').read_text())
assert not members(pw['child_pgid']) and not (preview/'ACTIVE.lock').exists()
assert not V.exists() and not (R/'FULL_WORKFLOW.json').exists()
mem={x.split(':')[0]:int(x.split()[1]) for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')}
assert mem['MemAvailable']>=200*1024*1024,'Wait for memory; never start a competing full instance'
state=dict(state='PREPARING',started=stamp(),parent_pid=os.getpid(),parent_proc_stat=Path('/proc/self/stat').read_text(),plan_sha256=sha(R/'PLAN.json'),
 flow='Manual original HLS-generated XSIM and C postchecker; cosim_design report formatter NOT_RUN',automatic_next_stage=False,board='NOT_RUN')
def save():(R/'FULL_WORKFLOW.json').write_text(json.dumps(state,indent=2)+'\n')
def group_snapshot(group):
 rows=[]
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   stat=(p/'stat').read_text();v=stat[stat.rindex(')')+2:].split()
   if v[0]!='Z' and int(v[2])==group:
    rows.append(dict(pid=int(p.name),start_ticks=v[19],rss_kib=int(v[21])*os.sysconf('SC_PAGE_SIZE')//1024))
  except OSError:pass
 return rows

def tool(phase,command,cwd,timeout):
 state.update(state='EXECUTING_'+phase.upper(),phase=phase);save()
 def stop_owned(p):
  try:os.killpg(p.pid,signal.SIGTERM)
  except ProcessLookupError:pass
  try:p.wait(timeout=15)
  except subprocess.TimeoutExpired:
   try:os.killpg(p.pid,signal.SIGKILL)
   except ProcessLookupError:pass
   p.wait()
  deadline=time.monotonic()+15
  while members(p.pid) and time.monotonic()<deadline:time.sleep(0.1)
  if members(p.pid):
   try:os.killpg(p.pid,signal.SIGKILL)
   except ProcessLookupError:pass
   deadline=time.monotonic()+10
   while members(p.pid) and time.monotonic()<deadline:time.sleep(0.1)
  assert not members(p.pid),'Owned child group did not drain after stop'
 with (R/(phase+'.log')).open('w') as out,(R/(phase+'_resources.jsonl')).open('w') as resources:
  p=subprocess.Popen(['bash','-c','source /tools/Xilinx/Vitis/2022.2/settings64.sh >/dev/null 2>&1; exec '+command],cwd=cwd,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
  state.update(child_pid=p.pid,child_pgid=p.pid,command=command);save();start=time.monotonic();peak=0
  try:
   while True:
    procs=group_snapshot(p.pid);rss=sum(x['rss_kib'] for x in procs);peak=max(peak,rss)
    available=next(int(x.split()[1]) for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'))
    elapsed=time.monotonic()-start
    sample=dict(utc=stamp(),elapsed_s=elapsed,group_rss_kib=rss,available_kib=available,members=procs)
    resources.write(json.dumps(sample)+'\n');resources.flush()
    if p.poll() is not None:break
    reason=('STOP_REQUESTED' if (R/'STOP_REQUESTED').exists() else 'PHASE_TIMEOUT' if elapsed>timeout else 'MEM_AVAILABLE_BELOW_32GIB' if available<32*1024*1024 else 'GROUP_RSS_ABOVE_128GIB' if rss>128*1024*1024 else None)
    if reason:
     state['stop_evidence']=dict(reason=reason,phase=phase,timeout_seconds=timeout,**sample);save();stop_owned(p);raise RuntimeError(reason)
    time.sleep(5)
   assert p.returncode==0,(phase,p.returncode)
   assert not members(p.pid),'Residual owned group'
   state.setdefault('phase_resources',{})[phase]=dict(elapsed_s=elapsed,peak_group_rss_kib=peak,returncode=p.returncode);save()
  except BaseException:
   stop_owned(p);raise
(R/'ACTIVE.lock').write_text(str(os.getpid()));save()
try:
 shutil.copytree(OLD/'verilog',V,ignore=shutil.ignore_patterns('*.log','*.wdb','*.vcd','*.jou','*.rpt','*.csv','*.zip','.exit.err','.aesl_error'))
 patch=M/'experiments/sim_memory_bank_20261026'
 shutil.copy2(M/'experiments/d64_stream_integration_20261102_r2/mem_model.sv',V/'file_agent/mem_model.sv')
 ref=V/'lm_head_v4_partial_proto_subsystem/lm_head_v4_partial_proto_reference_model.sv'
 text=ref.read_text();needle='        mem_blk_pages_weights.tvinload_pagechk_atinit(fpath, 34105344*((128+7)/8), 0);'
 assert text.count(needle)==1;ref.write_text(text.replace(needle,needle+'\n'+(patch/'weights_preflight.svh').read_text()))
 obs=M/'experiments/perf_observer_20261026'
 for name in ['stage_observer.sv','stage_bind.sv']:shutil.copy2(obs/name,V/name)
 for name in ['range_observer.sv','range_bind.sv']:shutil.copy2(E/name,V/name)
 prj=(V/'lm_head_v4_partial_proto.prj').read_text()+'\nsv xil_defaultlib "stage_observer.sv"\nsv xil_defaultlib "stage_bind.sv"\nsv xil_defaultlib "range_observer.sv"\nsv xil_defaultlib "range_bind.sv"\n'
 (V/'full_bank.prj').write_text(prj)
 (V/'full_bank.tcl').write_text('run all\nquit\n')
 (NEW/'tv').mkdir();(NEW/'tv/cdatafile').symlink_to(OLD/'tv/cdatafile',target_is_directory=True);(NEW/'tv/rtldatafile').mkdir()
 (NEW/'wrapc_pc').mkdir();shutil.copy2(OLD/'wrapc_pc/cosim.pc.exe',NEW/'wrapc_pc/cosim.pc.exe')
 assert sha(NEW/'wrapc_pc/cosim.pc.exe')==plan['postchecker_sha256']
 F=R/'fixtures';F.mkdir()
 source=M/'experiments/partial_rtl_20261024/full_fixtures_r3'
 for p in source.iterdir():
  if p.is_file() and (p.name.startswith('old_chinese.') or p.name=='weight_paths.txt'):shutil.copy2(p,F/p.name)
 assert not (F/'actual_RTL_full_chinese.bin').exists(),'No C-reference actual file is allowed here'
 unchanged={}
 for p in (OLD/'verilog').rglob('*'):
  rel=p.relative_to(OLD/'verilog')
  if p.is_file() and p.suffix in ['.v','.sv'] and rel not in [Path('file_agent/mem_model.sv'),ref.relative_to(V)]:
   assert sha(V/rel)==sha(p),str(rel);unchanged[str(rel)]=sha(p)
 assert unchanged==plan['reuse_sources'],'RTL/model callbacks changed since the reviewed five-block run'
 (R/'RTL_AND_STALL_REUSE.json').write_text(json.dumps(unchanged,indent=2)+'\n')
 tv=NEW/'tv/cdatafile/c.lm_head_v4_partial_proto.autotvin_weights.dat';assert sha(tv)==plan['full_tv_sha256']
 first=next(x.strip() for x in (V/'run_xsim.sh').read_text().splitlines() if x.strip().startswith('/tools/Xilinx/Vivado/2022.2/bin/xelab '))
 assert first.endswith('-s lm_head_v4_partial_proto')
 tool('elaborate',first.replace('-prj lm_head_v4_partial_proto.prj','-prj full_bank.prj').replace('-s lm_head_v4_partial_proto','-debug all -s full_bank_cosim_20261102_r2'),V,300)
 tool('xsim','/tools/Xilinx/Vivado/2022.2/bin/xsim -testplusarg UVM_VERBOSITY=UVM_LOW -testplusarg UVM_TESTNAME=lm_head_v4_partial_proto_test_lib -testplusarg UVM_TIMEOUT=20000000000000 --noieeewarnings full_bank_cosim_20261102_r2 -tclbatch full_bank.tcl',V,172800)
 log=(R/'xsim.log').read_text(errors='replace');assert re.search(r'^BANK_FULL_INPUT_SENTINEL_PASS checked=1522$',log,re.M)
 assert not re.search(r'^(?:UVM_FATAL|UVM_ERROR|ERROR:|Fatal:)',log,re.M)
 assert re.search(r'^LMH_RANGE_GUARD_SUMMARY meta_read_bursts=\d+ meta_write_bursts=\d+ weight_read_bursts=\d+$',log,re.M)
 returned=list((NEW/'tv/rtldatafile').glob('*autotvout*.dat'));assert len(returned)==7
 for p in returned:assert p.stat().st_size>0 and '[[[/runtime]]]' in p.read_text(),p.name
 tool('c_postcheck','./cosim.pc.exe "'+str(F)+'"',NEW/'wrapc_pc',180)
 assert 'PARTIAL_FULL_RTL_REFERENCE_PASS calls=1 full_arrays=1' in (R/'c_postcheck.log').read_text()
 actual=F/'actual_RTL_full_chinese.bin';assert actual.exists();shutil.copy2(actual,R/actual.name)
 for p in [V/'weights_readback.csv',V/'stage_profile.csv']:shutil.copy2(p,R/p.name)
 with (R/'stage_profile.csv').open() as f:rows=list(csv.DictReader(f))
 assert len(rows)==6 and {int(x['stage']) for x in rows}=={-1,0,1,2,3,4}
 artifacts=R/'tool_artifacts';artifacts.mkdir()
 for p in V.iterdir():
  if p.is_file() and (p.suffix=='.csv' or p.name in ['lat.rpt','result.transaction.rpt']):shutil.copy2(p,artifacts/p.name)
 (R/'returned_tv').mkdir()
 for p in returned:shutil.copy2(p,R/'returned_tv'/p.name)
 assert sha(tv)==plan['full_tv_sha256']
 for path,digest in plan['source_sha256'].items():assert sha(ROOT/path)==digest,path
 state.update(state='GENERATED_XSIM_AND_C_POSTCHECK_PASS_AWAITING_NUMERIC_AND_FIFO_REVIEW',finished=stamp())
except BaseException as e:state.update(state='FAILED_NO_AUTOMATIC_RETRY',error=repr(e),finished=stamp())
finally:state['process_after']=members(state.get('child_pgid',-1));save();(R/'ACTIVE.lock').unlink(missing_ok=True)
print(json.dumps(state,indent=2))
