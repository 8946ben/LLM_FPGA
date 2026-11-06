"""Static compressed snapshots or terminal evidence, never advances execution."""
from pathlib import Path
import json,hashlib,sys,shutil,gzip,tarfile,datetime
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
R=ROOT/'module_14_lm_head_v4/reports/sim_memory_bank_20261026_r1';V=ROOT/'.cache/p64_bank_preview_20261026_r1/sim/verilog'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
mode,tag=sys.argv[1:];assert mode in ['snapshot','terminal'] and tag.replace('_','').isalnum()
work=json.loads((R/'PREVIEW_WORKFLOW.json').read_text())
if mode=='snapshot':
 D=R/'observations'/tag;assert not D.exists();D.mkdir(parents=True)
 wave=V/'preview5.vcd';size=wave.stat().st_size;h=hashlib.sha256();remaining=size
 with wave.open('rb') as source,gzip.open(D/'preview_partial.vcd.gz','wb') as out:
  while remaining:
   data=source.read(min(1048576,remaining));assert data;out.write(data);h.update(data);remaining-=len(data)
 for name,source in [('weights_readback.csv',V/'weights_readback.csv'),('preview_simulate.log',R/'preview_simulate.log')]:
  if source.exists():shutil.copy2(source,D/name)
 (D/'PREVIEW_WORKFLOW.json').write_text(json.dumps(work,indent=2)+'\n')
 meta=dict(state='SAVED_LIVE_PREFIX_NOT_TERMINAL',observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prefix_bytes=size,uncompressed_sha256=h.hexdigest(),compressed_sha256=sha(D/'preview_partial.vcd.gz'),original_job_untouched=True)
 (D/'SNAPSHOT.json').write_text(json.dumps(meta,indent=2)+'\n')
 folders=[D]
else:
 assert work['state']!='EXECUTING_PREVIEW_SIMULATE' and not (R/'ACTIVE.lock').exists()
 group=work.get('child_pgid');members=[]
 for p in Path('/proc').iterdir():
  try:
   stat=(p/'stat').read_text();parts=stat[stat.rindex(')')+2:].split()
   if parts[0]!='Z' and int(parts[2])==group:members.append(int(p.name))
  except (ValueError,OSError):pass
 assert not members
 parent=ROOT/'module_14_lm_head_v4/reports/partial_rtl_20261024_r1/full_r3/PLAN.json';plan=json.loads(parent.read_text())
 for name,h in plan['source_sha256'].items():
  if name==plan['only_path_rebind']['path']:h=plan['only_path_rebind']['remote_sha256']
  assert sha(ROOT/name)==h,name
 new=json.loads((R/'PREVIEW_PLAN.json').read_text())
 for name,h in new['source_sha256'].items():assert sha(ROOT/name)==h,name
 reuse=json.loads((R/'PREVIEW_RTL_AND_STALL_REUSE.json').read_text())
 for name,h in reuse.items():assert sha(V/name)==h,name
 after=dict(state='PASS_PREVIEW_JOB_STOPPED_AND_SOURCE_AUDIT',observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),workflow_state=work['state'],owned_process_group_members=members,active_locks=0,original_frozen_source_files=len(plan['source_sha256']),unchanged_rtl_and_model_sources=len(reuse),automatic_next_stage=False,board='NOT_RUN')
 (R/'PROCESS_AFTER.json').write_text(json.dumps(after,indent=2)+'\n');folders=[R]
archive=ROOT/('bank_preview_'+mode+'_'+tag+'.tar.gz')
assert not archive.exists()
with tarfile.open(archive,'w:gz') as t:
 for folder in folders:
  for p in folder.rglob('*'):
   if p.is_file() and p.name not in ['entry.tar.gz','preview_entry.tar.gz']:t.add(p,arcname=str(p.relative_to(ROOT)))
print(json.dumps(dict(archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),workflow=work['state'])))
