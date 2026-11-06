from pathlib import Path
import datetime,json,os,signal,subprocess,time,threading
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
R=ROOT/'module_14_lm_head_v4/reports/d64_guard_control_20261102_r2'
assert not (R/'RESULT.json').exists()
state={'automatic_next_stage':False,'board':'NOT_RUN'}
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save():(R/'WORKFLOW.json').write_text(json.dumps(state,indent=2)+'\n')
def members(group):return [x['pid'] for x in group_snapshot(group)]
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

results=[]
for name in ['stop','timeout','exit','stop_tree']:
 if name=='stop':(R/'STOP_REQUESTED').write_text('Finite control only')
 try:
  command='/bin/true' if name=='exit' else '/home/zhangben/anaconda3/bin/python -c "import time;time.sleep(30)"'
  if name=='stop_tree':
   command='/home/zhangben/anaconda3/bin/python -c "import os,signal,time; n=os.fork(); signal.signal(signal.SIGTERM,signal.SIG_IGN) if n==0 else None; time.sleep(30)"'
   thread=threading.Thread(target=lambda:(time.sleep(1),(R/'STOP_REQUESTED').write_text('Finite stop-tree control')));thread.start()
  tool('control_'+name,command,R,0.1 if name=='timeout' else 60)
  assert name=='exit','Expected real stop was not raised'
  results.append({'case':name,'actual':'EXIT_0'})
 except RuntimeError as e:
  expected='STOP_REQUESTED' if name in ['stop','stop_tree'] else 'PHASE_TIMEOUT'
  assert str(e)==expected,(name,str(e))
  assert state['stop_evidence']['reason']==expected
  results.append({'case':name,'actual':str(e),'evidence':state['stop_evidence']})
 finally:
  (R/'STOP_REQUESTED').unlink(missing_ok=True)
  assert not members(state['child_pgid']),'Child group still alive'
result={'state':'PASS_ACTUAL_STOP_TIMEOUT_AND_SUCCESS_CONTROLS','cases':results,'process_after':[],
 'limits':['Resource branches record measurements but were not induced by exhausting shared server memory'],
 'board':'NOT_RUN','eda':'NOT_RUN'}
(R/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
