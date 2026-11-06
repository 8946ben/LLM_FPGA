"""Freeze a new full entry only after manual independent memory qualification.

Preparation only. No upload, launch, board access or modification of old reports.
"""
from pathlib import Path
import hashlib,json,tarfile
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4'
E=M/'experiments/full_bank_cosim_20261102_r2';R=M/'reports/full_bank_cosim_20261102_r2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 E.mkdir(exist_ok=True);R.mkdir(exist_ok=True);assert not (R/'PLAN.json').exists()
 old=M/'experiments/full_bank_cosim_20261026/run_full.py'
 text=old.read_text()
 for a,b in [
  ("E=M/'experiments/full_bank_cosim_20261026';R=M/'reports/full_bank_cosim_20261026_r1'", "E=M/'experiments/full_bank_cosim_20261102_r2';R=M/'reports/full_bank_cosim_20261102_r2'"),
  ("NEW=ROOT/'.cache/p64_full_bank_cosim_20261026_r1/sim'", "NEW=ROOT/'.cache/p64_full_bank_cosim_20261102_r2/sim'"),
  ("shutil.copy2(patch/'mem_model.sv',V/'file_agent/mem_model.sv')", "shutil.copy2(M/'experiments/d64_stream_integration_20261102_r2/mem_model.sv',V/'file_agent/mem_model.sv')"),
  ('full_bank_cosim_r1','full_bank_cosim_20261102_r2'),
 ]:
  assert a in text,a;text=text.replace(a,b)
 # Each new run has a separate resource trace and disjoint guard reasons.
 begin=text.index('def tool(phase,command,cwd,timeout):')
 end=text.index("(R/'ACTIVE.lock').write_text",begin)
 monitor='''def group_snapshot(group):
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
    resources.write(json.dumps(sample)+'\\n');resources.flush()
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
'''
 assert (M/'experiments/d64_guard_control_20261102_r2/monitor.py').read_text()==monitor
 text=text[:begin]+monitor+text[end:]
 # The outer finalizer records process state even on a failed gate.
 text=text.replace("finally:save();(R/'ACTIVE.lock').unlink(missing_ok=True)","finally:state['process_after']=members(state.get('child_pgid',-1));save();(R/'ACTIVE.lock').unlink(missing_ok=True)")
 compile(text,str(E/'run_full.py'),'exec');(E/'run_full.py').write_text(text)
 oldE=M/'experiments/full_bank_cosim_20261026'
 for name in ['range_observer.sv','range_bind.sv']:(E/name).write_bytes((oldE/name).read_bytes())
 plan=json.loads((M/'reports/full_bank_cosim_20261026_r1/PLAN.json').read_text())
 gates={
  'd64_resource_recovery_20261102_r1':'PASS_PACKED_BANK_SEMANTICS_AND_FINITE_BENCHMARK',
  'd64_stream_loader_20261102_r1':'PASS_FINITE_STREAM_LOADER_ALL_BYTES_AND_FOUR_NEGATIVES',
  'd64_full_input_preflight_20261102_r2':'PASS_NO_DUT_FULL_INPUT_ALL_BYTES_AND_SENTINELS',
  'd64_stream_integration_20261102_r2':'PASS_ORIGINAL_OFFSET_SUBCLASS_STREAM_AND_PIPE_CALLBACKS',
 }
 for folder,state in gates.items():
  p=M/'reports'/folder/'INDEPENDENT_REVIEW.json'
  assert json.loads(p.read_text())['state']==state,folder
  plan['gate_reviews'][str(p.relative_to(ROOT)).replace('\\','/')]={'state':state,'sha256':sha(p)}
 guard=M/'reports/d64_guard_control_20261102_r2/RESULT.json'
 assert json.loads(guard.read_text())['state']=='PASS_ACTUAL_STOP_TIMEOUT_AND_SUCCESS_CONTROLS'
 plan['gate_reviews'][str(guard.relative_to(ROOT)).replace('\\','/')]={'state':'PASS_ACTUAL_STOP_TIMEOUT_AND_SUCCESS_CONTROLS','sha256':sha(guard)}
 for p in list(E.iterdir())+list((M/'experiments/d64_stream_integration_20261102_r2').iterdir()):
  if p.is_file():plan['source_sha256'][str(p.relative_to(ROOT)).replace('\\','/')]=sha(p)
 plan.update(state='FROZEN_FULL_RETRY_WITH_QUALIFIED_PACKED_STREAM_STORAGE',
  predecessor='20261026 protected stop and 20261102_r1 manually stopped integration review preserved',
  storage_change='Packed16; base loader opts into streaming for weights TV suffix; original offset subclass and original virtual reference-model call retained',
  resource_guards={'min_available_gib':32,'max_group_rss_gib':128,'full_phase_seconds':172800,'sample_seconds':5,'stop_file':'STOP_REQUESTED'},
  automatic_next_stage=False,board='NOT_RUN')
 plan['safety'].update(minimum_running_available_gib=32,maximum_group_rss_gib=128,sample_seconds=5)
 (R/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
 paths=list(E.iterdir())+[R/'PLAN.json']
 for n in plan['gate_reviews']:
  if '20261102' in n:paths.append(ROOT/n)
 paths.extend(p for p in (M/'experiments/d64_stream_integration_20261102_r2').iterdir() if p.is_file())
 with tarfile.open(R/'entry.tar.gz','w:gz') as a:
  for p in paths:a.add(p,arcname=str(p.relative_to(ROOT)))
 print(json.dumps({'archive':str(R/'entry.tar.gz'),'sha256':sha(R/'entry.tar.gz'),'launch':'NOT_RUN'}))
if __name__=='__main__':main()
