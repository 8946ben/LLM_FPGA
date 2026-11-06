"""Bounded read-only remote snapshot; never follows or copies a live VCD."""
from pathlib import Path
import subprocess,json,datetime,sys
ROOT=Path(__file__).resolve().parents[1]
name=sys.argv[1] if len(sys.argv)>1 else 'memory_repaired_preview_20261103_r1'
assert name in ['memory_repaired_preview_20261103_r1','memory_repaired_full_20261103_r1']
probe=r'''
from pathlib import Path
import json,datetime,os,hashlib
root=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1');name=NAME
r=root/'module_14_lm_head_v4/reports'/name;v=root/'.cache'/name/'verilog';w=json.loads((r/'WORKFLOW.json').read_text())
def parts(s):return s[s.rindex(')')+2:].split()
parent=Path('/proc')/str(w['parent_pid'])/'stat';current=parent.read_text() if parent.exists() else None
match=current is not None and parts(current)[19]==parts(w['parent_proc_stat'])[19] and parts(current)[0]!='Z'
members=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  a=parts((p/'stat').read_text())
  if a[0]!='Z' and int(a[2])==w.get('child_pgid',-1):members.append(dict(pid=int(p.name),start_ticks=a[19],cpu_ticks=int(a[11])+int(a[12]),rss_kib=int(a[21])*os.sysconf('SC_PAGE_SIZE')//1024))
 except OSError:pass
out=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),workflow=w,parent_identity_alive=match,owned_process_group_members=members,active_locks=int((r/'ACTIVE.lock').exists()))
for file in ['xsim.log','elaborate.log','c_postcheck.log']:
 f=r/file
 if f.exists():
  out[file+'_bytes']=f.stat().st_size
  with f.open('rb') as h:h.seek(max(0,f.stat().st_size-8192));s=h.read().decode(errors='replace')
  out[file+'_tail']=s.splitlines()[-15:]
for file in ['memory_phases.csv','stage_profile.csv']:
 f=v/file
 if f.exists():out[file+'_tail']=f.read_text().splitlines()[-8:]
f=v/'preview5.vcd'
if f.exists():
 with f.open('rb') as h:h.seek(max(0,f.stat().st_size-8192));lines=h.read().splitlines()
 out['vcd_bytes']=f.stat().st_size;out['last_vcd_times_ps']=[int(x[1:]) for x in lines if x.startswith(b'#')][-3:]
f=r/'xsim_resources.jsonl'
if f.exists():out['latest_resource']=json.loads(f.read_text().splitlines()[-1])
out['returned_tv_sizes']={p.name:p.stat().st_size for p in (v.parent/'tv/rtldatafile').glob('*autotvout*.dat')}
plan=json.loads((root/'module_14_lm_head_v4/reports/full_bank_cosim_20261102_r2/PLAN.json').read_text());old=root/'.cache/p64_full_bank_cosim_20261102_r2/sim/verilog'
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out['original_frozen_source_mismatches']=[n for n,h in plan['source_sha256'].items() if digest(root/n)!=h]
out['original_reused_source_mismatches']=[n for n,h in plan['reuse_sources'].items() if digest(old/n)!=h]
out['original_frozen_source_count']=len(plan['source_sha256']);out['original_reused_source_count']=len(plan['reuse_sources'])
compiled=r/'COMPILED_SOURCES.json'
if compiled.exists():
 actual=json.loads(compiled.read_text())['actual'];out['actual_compiled_source_count']=len(actual)
 out['actual_compiled_source_mismatches']=[n for n,h in actual.items() if digest(v/n)!=h]
 if name=='memory_repaired_full_20261103_r1':
  prefix=json.loads((root/'module_14_lm_head_v4/reports/memory_repaired_preview_20261103_r1/COMPILED_SOURCES.json').read_text())['actual']
  out['actual_sources_identical_to_qualified_first5']=actual==prefix
print(json.dumps(out))
'''.replace('NAME',repr(name))
p=subprocess.run(['ssh','-p','7626','-o','BatchMode=yes','-o','ConnectTimeout=15','zhangben@124.16.71.7','/home/zhangben/anaconda3/bin/python','-'],input=probe,text=True,capture_output=True,timeout=90)
assert p.returncode==0,p.stderr
out=json.loads(p.stdout);assert not out['original_frozen_source_mismatches'] and not out['original_reused_source_mismatches']
assert not out.get('actual_compiled_source_mismatches',[])
if 'actual_sources_identical_to_qualified_first5' in out:assert out['actual_sources_identical_to_qualified_first5']
report=ROOT/'module_14_lm_head_v4/reports'/name;stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S');folder=report/'observations'/stamp;folder.mkdir(parents=True)
(folder/'RUNTIME_SNAPSHOT.json').write_text(json.dumps(out,indent=2)+'\n')
if not out['parent_identity_alive'] and not out['owned_process_group_members'] and out['active_locks']==0:
 (report/'PROCESS_AFTER.json').write_text(json.dumps(out,indent=2)+'\n')
if '--compact' in sys.argv:
 print(json.dumps(dict(snapshot=str(folder/'RUNTIME_SNAPSHOT.json'),utc=out['utc'],state=out['workflow']['state'],parent_identity_alive=out['parent_identity_alive'],members=out['owned_process_group_members'],active_locks=out['active_locks'],
  rss_gib=sum(x['rss_kib'] for x in out['owned_process_group_members'])/1048576,stages=out.get('stage_profile.csv_tail',[]),returned_tv_sizes=out.get('returned_tv_sizes',{}),compiled_sources_match=not out.get('actual_compiled_source_mismatches',[])),indent=2))
else:print(json.dumps({'snapshot':str(folder/'RUNTIME_SNAPSHOT.json'),**out},indent=2))
