"""Extract the exact new full-run supervisor and add finite live controls."""
from pathlib import Path
import ast,hashlib,json
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';E=M/'experiments/d64_guard_control_20261102_r2';R=M/'reports/d64_guard_control_20261102_r2'
def main():
 E.mkdir(exist_ok=True);R.mkdir(exist_ok=True);assert not (E/'run_controls.py').exists()
 source=ROOT/'tools/prepare_d64_full_retry_20261102.py'
 tree=ast.parse(source.read_text())
 monitor=next(ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='monitor' for x in n.targets))
 prefix='''from pathlib import Path
import datetime,json,os,signal,subprocess,time,threading
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
R=ROOT/'module_14_lm_head_v4/reports/d64_guard_control_20261102_r2'
assert not (R/'RESULT.json').exists()
state={'automatic_next_stage':False,'board':'NOT_RUN'}
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save():(R/'WORKFLOW.json').write_text(json.dumps(state,indent=2)+'\\n')
def members(group):return [x['pid'] for x in group_snapshot(group)]
'''
 suffix='''
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
(R/'RESULT.json').write_text(json.dumps(result,indent=2)+'\\n');print(json.dumps(result,indent=2))
'''
 (E/'monitor.py').write_text(monitor);(E/'run_controls.py').write_text(prefix+monitor+suffix)
 data={'state':'PREPARED_FINITE_LIVE_SUPERVISOR_CONTROLS','generator_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
  'monitor_sha256':hashlib.sha256(monitor.encode()).hexdigest(),'runner_sha256':hashlib.sha256((E/'run_controls.py').read_bytes()).hexdigest()}
 (R/'PLAN.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data))
if __name__=='__main__':main()
