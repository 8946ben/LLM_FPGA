from pathlib import Path
import json,hashlib,tarfile,shutil,re,datetime
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
R=ROOT/'module_14_lm_head_v4/reports/partial_rtl_20261026_diagnosis_r1'
F=ROOT/'module_14_lm_head_v4/reports/partial_rtl_20261024_r1/full_r3'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
w=json.loads((R/'r6/WORKFLOW.json').read_text());log=(R/'r6/probe.log').read_text()
assert w['exit_code']==0
assert re.search(r'^PROBE_FIRST_PREVIEW_REACHED 2395162500 ps$',log,re.M)
assert re.search(r'^PROBE_STOPPED 2395162500 ps$',log,re.M)
assert not re.search(r'^PROBE_RANGE_GUARD_FAILURE$',log,re.M)
assert 'XSIM_DYNAMIC_BYTE_ARRAY_ALIAS_512M_REPRODUCED' in (R/'alias_minimal/r2.log').read_text()
groups=[]
for p in R.rglob('*WORKFLOW.json'):
 x=json.loads(p.read_text());g=x.get('child_pgid')
 if g:groups.append(g)
members=[]
for p in Path('/proc').iterdir():
 try:
  s=(p/'stat').read_text();v=s[s.rindex(')')+2:].split()
  if v[0]!='Z' and int(v[2]) in groups:members.append(int(p.name))
 except (OSError,ValueError):pass
assert not members
plan=json.loads((F/'PLAN.json').read_text())
for n,h in plan['source_sha256'].items():
 if n==plan['only_path_rebind']['path']:h=plan['only_path_rebind']['remote_sha256']
 assert sha(ROOT/n)==h,n
src=ROOT/'.cache/p64_rtl_full_r3/hls/solution1/sim/verilog'
model={}
for name in ['file_agent/mem_model.sv','lm_head_v4_partial_proto_subsystem/lm_head_v4_partial_proto_reference_model.sv','axivip/axi_state.sv']:
 p=src/name;q=R/'model_source'/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q);model[name]=sha(p)
review=dict(state='PASS_DIAGNOSTIC_OBSERVATION_AND_ALL_JOBS_STOPPED',time=datetime.datetime.now(datetime.timezone.utc).isoformat(),
 wrapper_state=w['state'],wrapper_classification_issue='Guard text appeared in echoed Tcl source; line-anchored review confirms guard did not fire',
 diagnostic_stop_ps=2395162500,first_preview_reached=True,range_guard_fired=False,
 source_files_unchanged=len(plan['source_sha256']),owned_process_group_members=members,
 active_locks=list(map(str,R.rglob('ACTIVE.lock'))),original_model_sha256=model,
 vcd_sha256=sha(R/'r6/signal_probe.vcd'),no_complete_cosim_qualification=True,board='NOT_RUN',automatic_next_stage=False)
assert not review['active_locks']
(R/'PROCESS_AFTER.json').write_text(json.dumps(review,indent=2)+'\n')
archive=ROOT/'partial_alias_diagnosis_20261026.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in R.rglob('*'):
  if p.is_file():t.add(p,arcname=str(p.relative_to(ROOT)))
print(json.dumps(dict(archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive))))
