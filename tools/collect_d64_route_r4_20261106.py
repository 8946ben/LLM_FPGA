"""Collect immutable r4 reports via raw bytes after independent terminal checks."""
from pathlib import Path
import subprocess, json, io, tarfile, hashlib
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'module_14_lm_head_v4/reports/d64_system_200m_20261106_r4'
OUT=R/'terminal_collection_r1'
REMOTE=r'''
from pathlib import Path
import json,os,hashlib,datetime,io,tarfile,sys
root=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
r=root/'module_14_lm_head_v4/reports/d64_system_200m_20261106_r4'
project=root/'module_14_lm_head_v4/board/build/m14_d64_200m_r4'
def parts(s):return s[s.rindex(')')+2:].split()
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
w=json.loads((r/'route/WORKFLOW.json').read_text());launch=json.loads((r/'LAUNCH_IDENTITY.json').read_text())
assert w['parent_pid']==launch['pid']==7321 and parts(w['parent_proc_stat'])[19]==parts(launch['proc_stat'])[19]=='353578131'
assert w['state']=='FAILED_NO_AUTOMATIC_RETRY' and w['error']=='AssertionError()'
identities={(7321,'353578131')};samples=0;peak=0;spare=10**30
with (r/'route/route/resources.jsonl').open() as f:
 for line in f:
  row=json.loads(line);samples+=1;peak=max(peak,row['rss_kib']);spare=min(spare,row['available_kib'])
  assert row['rss_kib']<=16*1048576 and row['available_kib']>=32*1048576 and row['elapsed_s']<=21600
  identities.update((m['pid'],m['start_ticks']) for m in row['members'])
for pid,start in identities:
 p=Path('/proc')/str(pid)/'stat'
 if p.exists():
  a=parts(p.read_text());assert a[19]!=start or a[0]=='Z',(pid,start)
group=[]
for p in Path('/proc').iterdir():
 if p.name.isdigit():
  try:
   a=parts((p/'stat').read_text())
   if int(a[2])==w['child_pgid'] and a[0]!='Z':group.append(int(p.name))
  except (FileNotFoundError,ProcessLookupError):pass
assert not group and not (r/'route/ACTIVE.lock').exists()
assert not list((root/'module_14_lm_head_v4/reports').rglob('ACTIVE.lock'))
plan=json.loads((r/'PLAN.json').read_text())
assert all(sha(root/p)==h for p,h in plan['source_sha256'].items())
original=root/'.cache/p64_r3/csynth/hls/solution1/syn/verilog'
assert all(sha(original/p)==h for p,h in plan['syn_verilog_sha256'].items())
bd=project/'m14_d64_200m.srcs/sources_1/bd/m14_d64_system/m14_d64_system.bd'
assert sha(bd)==plan['bd_sha256']==sha(r/'hardware/implemented_bd.json')
paths=[r/'PLAN.json',r/'LAUNCH_IDENTITY.json',r/'COPIED_PROJECT.json',r/'route/WORKFLOW.json',r/'route/route/tool.log',r/'route/route/resources.jsonl']
paths+=sorted(p for p in (r/'hardware').iterdir() if p.is_file() and p.suffix in ['.rpt','.json','.txt'])
paths+=sorted(project.glob('m14_d64_200m.runs/*/runme.log'))
paths+=sorted((root/'module_14_lm_head_v4/experiments/d64_system_200m_20261106_r4').glob('*'))
paths+=[root/'module_14_lm_head_v4/experiments/d64_system_200m_20261105_r1/lm_head_v4_ddr4_pins.xdc',bd]
paths=sorted(set(p for p in paths if p.is_file()))
manifest={str(p.relative_to(root)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in paths}
dcp=r/'hardware/post_route.dcp'
receipt=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent_pid=7321,start_ticks='353578131',observed_identities_checked=len(identities),all_observed_identities_absent=True,group_empty=True,lock_absent=True,source_sha_match=True,original_73_sha_match=True,bd_sha256=sha(bd),resources=dict(samples=samples,peak_group_gib=peak/1048576,min_available_gib=spare/1048576),post_route_dcp=dict(path=str(dcp),bytes=dcp.stat().st_size,sha256=sha(dcp)),files=manifest)
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|gz') as t:
 for p in paths:t.add(p,arcname=str(p.relative_to(root)),recursive=False)
 data=(json.dumps(receipt,indent=2)+'\n').encode();info=tarfile.TarInfo('TERMINAL_RECEIPT.json');info.size=len(data);t.addfile(info,io.BytesIO(data))
'''
assert not OUT.exists(),OUT
v=subprocess.run(['ssh','-p','7626','-o','BatchMode=yes','-o','ConnectTimeout=15','zhangben@124.16.71.7','/home/zhangben/anaconda3/bin/python','-'],input=REMOTE.encode(),capture_output=True,timeout=180)
assert v.returncode==0,v.stderr.decode(errors='replace')
assert len(v.stdout)<64*1024**2
with tarfile.open(fileobj=io.BytesIO(v.stdout),mode='r:gz') as t:
 members=t.getmembers();names=[m.name for m in members]
 assert len(names)==len(set(names))
 assert all(m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts for m in members)
 receipt=json.load(t.extractfile('TERMINAL_RECEIPT.json'))
 for name,expected in receipt['files'].items():
  b=t.extractfile(name).read();assert len(b)==expected['bytes'] and hashlib.sha256(b).hexdigest()==expected['sha256'],name
 OUT.mkdir();t.extractall(OUT)
(R/'TERMINAL_COLLECTION_R1.tar.gz').write_bytes(v.stdout)
receipt['archive_sha256']=hashlib.sha256(v.stdout).hexdigest();receipt['archive_bytes']=len(v.stdout)
(R/'TERMINAL_COLLECTION_R1.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in receipt.items() if k!='files'},indent=2))
