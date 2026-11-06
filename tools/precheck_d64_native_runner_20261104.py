"""Exercise only the draft runner's owned-group cleanup; no EDA, model or DUT."""
from pathlib import Path
import ast,datetime,hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4'
E=M/'experiments/d64_native_memory_20261103_r1';R=M/'reports/d64_native_memory_20261103_r1'

def main():
    source=E/'run_gate.py';text=source.read_text();tree=ast.parse(text)
    main_node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    cleanup=next(n for n in main_node.body if isinstance(n,ast.FunctionDef) and n.name=='terminate_owned')
    fields=[next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name) for name in ['parts','members']]
    # Extract the actual implementation, not a substitute cleanup algorithm.
    extracted='\n\n'.join(ast.unparse(n) for n in [*fields,cleanup])
    remote='''from pathlib import Path
import os,signal,subprocess,sys,time,json,datetime
'''+extracted+'''
results=[];owned=[]
def create(code):
 p=subprocess.Popen([sys.executable,'-c',code],stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
 owned.append(p);return p
try:
 sentinel=create("import time;print('ready',flush=True);time.sleep(90)")
 assert sentinel.stdout.readline().strip()==b'ready'
 cases=[
  ('normal_tree',"import subprocess,sys,time;subprocess.Popen([sys.executable,'-c','import time;time.sleep(90)']);print('ready',flush=True);time.sleep(90)"),
  ('ignore_term_tree',"import subprocess,sys,time,signal;signal.signal(signal.SIGTERM,signal.SIG_IGN);subprocess.Popen([sys.executable,'-c','import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(90)']);time.sleep(.2);print('ready',flush=True);time.sleep(90)"),
  ('exited_parent_live_child',"import subprocess,sys,time;subprocess.Popen([sys.executable,'-c','import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(90)']);time.sleep(.2);print('ready',flush=True)"),
  ('already_exited',"print('ready',flush=True)")]
 for label,code in cases:
  p=create(code);assert p.stdout.readline().strip()==b'ready'
  if label in ['exited_parent_live_child','already_exited']:p.wait(timeout=3)
  before=members(p.pid);start=time.monotonic();terminate_owned(p)
  after=members(p.pid);assert not after
  assert sentinel.poll() is None and members(sentinel.pid)
  results.append(dict(case=label,elapsed_s=time.monotonic()-start,before=before,after=after,unrelated_sentinel_alive=True))
finally:
 for p in owned:
  if members(p.pid):
   try:os.killpg(p.pid,signal.SIGKILL)
   except ProcessLookupError:pass
  try:p.wait(timeout=3)
  except subprocess.TimeoutExpired:raise AssertionError('Precheck child did not terminate')
 for p in owned:assert not members(p.pid)
print(json.dumps(dict(state='PASS_OWNED_GROUP_CLEANUP_CONTROLS_ONLY',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),cases=results,all_precheck_owned_groups_empty=True,eda='NOT_RUN')))
'''
    # Explicit STHL7626 only; no board, sudo, package upload or tool launch.
    p=subprocess.run(['ssh','-p','7626','-o','BatchMode=yes','-o','ConnectTimeout=15','zhangben@124.16.71.7','/home/zhangben/anaconda3/bin/python','-'],input=remote,text=True,capture_output=True,timeout=75)
    assert p.returncode==0,(p.stdout,p.stderr)
    out=json.loads(p.stdout);assert out['state']=='PASS_OWNED_GROUP_CLEANUP_CONTROLS_ONLY'
    assert len(out['cases'])==4 and out['all_precheck_owned_groups_empty']
    out.update(runner_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
               actual_extracted_cleanup_sha256=hashlib.sha256(extracted.encode()).hexdigest(),
               not_proven=['End-to-end watcher/resource/STOP control','EDA compilation','Native AXI semantics','M14 RTL'])
    target=R/'RUNNER_CLEANUP_PRECHECK.json';assert not target.exists()
    target.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
