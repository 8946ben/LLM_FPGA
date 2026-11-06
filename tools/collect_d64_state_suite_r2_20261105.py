"""Collect this single terminal suite read-only; never launches/stops EDA."""
from pathlib import Path, PurePosixPath
import datetime,hashlib,io,json,os,shutil,subprocess,sys,tarfile,tempfile
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'module_14_lm_head_v4/reports/d64_state_suite_20261105_r2'
PROOF='_receipt/TERMINAL_EXPORT_PROOF.json'
REMOTE=r'''from pathlib import Path
import datetime,hashlib,io,json,os,sys,tarfile
root=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
r=root/'module_14_lm_head_v4/reports/d64_state_suite_20261105_r2'
def read(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
 return h.hexdigest()
def proc(pid):
 try:
  s=(Path('/proc')/str(pid)/'stat').read_text();a=s[s.rindex(')')+2:].split()
  return dict(pid=int(pid),state=a[0],group=int(a[2]),start_ticks=a[19])
 except FileNotFoundError:return None
w=read(r/'WORKFLOW.json');assert w['state'] in ['SUITE_RETURNED_AWAITING_INDEPENDENT_ARRAY_CONTROL_ADDRESS_REVIEW','FAILED_NO_AUTOMATIC_RETRY'],'Job not terminal: receipt forbidden'
def assert_launch_identity(work,launch):
 start=work['parent_proc_stat'].split(')')[-1].split()[19]
 launch_start=launch['proc_stat'].split(')')[-1].split()[19]
 assert work['parent_pid']==launch['pid']==42095 and start==launch_start=='347854432'
 return start
launch=read(r/'LAUNCH_IDENTITY.json');assert_launch_identity(w,launch)
identities={(42095,'347854432')}
for phase in ['elaborate','suite']:
 p=r/phase/'resources.jsonl'
 if p.exists():
  with p.open() as f:
   for line in f:
    for item in json.loads(line)['members']:identities.add((int(item['pid']),str(item['start_ticks'])))
current=[]
for p in Path('/proc').iterdir():
 if p.name.isdigit():
  try:
   item=proc(int(p.name))
   if item is not None and item['state']!='Z':current.append(item)
  except ProcessLookupError:pass
alive=[p for p in current if (p['pid'],p['start_ticks']) in identities]
owned=[p for p in current if p['group']==w.get('child_pgid',-1)]
assert not alive and not owned and not (r/'ACTIVE.lock').exists() and w['process_after']==[],('Not drained',alive,owned)
plan=read(r/'EXECUTION_PLAN.json');compiled=read(root/'module_14_lm_head_v4/reports/d64_state_compile_20261105_r2/COMPILED_SOURCES.json');cache=root/plan['compile_cache']
actual={n:sha(cache/n) for n in compiled};tv=sha(root/plan['tv']);assert actual==compiled and tv==plan['tv_sha256']
for n,h in {**plan['bindings'],**plan['input_sha256']}.items():assert sha(root/n)==h,n
files=[]
for p in sorted(r.rglob('*')):
 assert not p.is_symlink(),p
 if p.is_file() and p.suffix!='.gz':files.append(p)
proof=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),workflow_state=w['state'],original_parent_identity_absent=True,all_observed_identities_absent=True,observed_identities=[dict(pid=pid,start_ticks=start) for pid,start in sorted(identities)],final_owned_group_empty=True,final_owned_group=w.get('child_pgid'),active_lock_absent=True,compile_cache_current_matches=True,compile_cache_source_sha256=actual,tv_sha256=tv,artifact_sha256={p.relative_to(r).as_posix():sha(p) for p in files},launch_identity=launch,launch_identity_sha256=sha(r/'LAUNCH_IDENTITY.json'),scope='Actual r2 terminal inspection and static bytes only; not numerical acceptance')
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|gz') as tar:
 for p in files:
  before=p.stat();tar.add(p,arcname=p.relative_to(r).as_posix(),recursive=False);after=p.stat()
  assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns) and sha(p)==proof['artifact_sha256'][p.relative_to(r).as_posix()],p
 assert read(r/'WORKFLOW.json')==w and not (r/'ACTIVE.lock').exists()
 data=(json.dumps(proof,indent=2)+'\n').encode();item=tarfile.TarInfo('_receipt/TERMINAL_EXPORT_PROOF.json');item.size=len(data);tar.addfile(item,io.BytesIO(data))
'''

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
 return h.hexdigest()

def unpack(archive,destination):
 destination=Path(destination);destination.mkdir(parents=True,exist_ok=True);names=set()
 with tarfile.open(archive,'r:gz') as tar:
  for entry in tar:
   name=PurePosixPath(entry.name)
   assert entry.isfile() and not name.is_absolute() and '..' not in name.parts and '\\' not in entry.name and ':' not in entry.name and entry.name not in names,'Unsafe/duplicate archive entry'
   names.add(entry.name);out=destination.joinpath(*name.parts);out.parent.mkdir(parents=True,exist_ok=True)
   with tar.extractfile(entry) as source,out.open('wb') as target:
    for chunk in iter(lambda:source.read(1048576),b''):target.write(chunk)
 proof=json.loads((destination/PROOF).read_text(encoding='utf-8'))
 assert names==set(proof['artifact_sha256'])|{PROOF},'Incomplete/unlisted receipt'
 for name,h in proof['artifact_sha256'].items():assert sha(destination/name)==h,name
 return proof

def self_test():
 with tempfile.TemporaryDirectory(prefix='d64_receipt_controls_') as temp:
  base=Path(temp);payload=b'raw\r\nbytes\x00\xff';proof=dict(artifact_sha256={'suite/bytes.bin':hashlib.sha256(payload).hexdigest()})
  def make(path,entries):
   with tarfile.open(path,'w:gz') as tar:
    for name,data in entries:
     item=tarfile.TarInfo(name);item.size=len(data);tar.addfile(item,io.BytesIO(data))
  good=[('suite/bytes.bin',payload),(PROOF,json.dumps(proof).encode())];archive=base/'good.tar.gz';make(archive,good);unpack(archive,base/'good');assert (base/'good/suite/bytes.bin').read_bytes()==payload
  cases=[('corrupt',[('suite/bytes.bin',payload+b'x'),good[1]]),('traversal',[('../escape',b'x'),*good]),('absolute',[('/escape',b'x'),*good]),('duplicate',[good[0],*good]),('extra',[('unlisted',b'x'),*good]),('missing',[good[1]])]
  rejected=[]
  for label,entries in cases:
   archive=base/(label+'.tar.gz');make(archive,entries)
   try:unpack(archive,base/label)
   except AssertionError:rejected.append(label)
  assert len(rejected)==len(cases)
  return dict(state='PASS_RECEIPT_BYTE_INTEGRITY_AND_PATH_CONTROLS_ONLY',positive_binary_crlf=True,rejected=rejected,scope='Local synthetic transport controls; no remote collection or RTL claim')

def main():
 if sys.argv[1:]==['--self-test']:print(json.dumps(self_test(),indent=2));return
 assert sys.argv[1:]==['--collect-terminal'],'Use --collect-terminal only after observed termination, or --self-test'
 assert not (R/'TERMINAL_EXPORT_PROOF.json').exists(),'Already collected; inspect existing evidence instead of replacing'
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S');archive=R/('terminal_receipt_'+stamp+'.tar.gz');archive.parent.mkdir(parents=True,exist_ok=True)
 with archive.open('xb') as output:
  result=subprocess.run(['ssh','-p','7626','-o','BatchMode=yes','-o','ConnectTimeout=15','zhangben@124.16.71.7','/home/zhangben/anaconda3/bin/python','-'],input=REMOTE.encode(),stdout=output,stderr=subprocess.PIPE,timeout=240)
 assert result.returncode==0,result.stderr.decode(errors='replace')[-4000:]
 with tempfile.TemporaryDirectory(prefix='d64_terminal_receipt_') as temp:
  folder=Path(temp);proof=unpack(archive,folder)
  for name in proof['artifact_sha256']:
   target=R/name
   if target.exists():assert sha(target)==proof['artifact_sha256'][name],('Local file collision',name)
  for name in proof['artifact_sha256']:
   target=R/name;target.parent.mkdir(parents=True,exist_ok=True)
   if not target.exists():shutil.copyfile(folder/name,target)
  (R/'TERMINAL_EXPORT_PROOF.json').write_bytes((folder/PROOF).read_bytes())
 receipt=dict(archive=archive.name,archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,artifact_count=len(proof['artifact_sha256']),workflow_state=proof['workflow_state'],numerical_acceptance='PENDING')
 (R/'TERMINAL_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
