"""Read-only observation of the one bounded12case suite; no EDA launch/stop."""
from pathlib import Path
import json,subprocess,datetime
ROOT=Path(__file__).resolve().parents[1]
REMOTE=r"""from pathlib import Path
import json,os,datetime,hashlib,csv,io
root=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1');r=root/'module_14_lm_head_v4/reports/d64_state_suite_20261105_r2';w=json.loads((r/'WORKFLOW.json').read_text());parts=lambda s:s[s.rindex(')')+2:].split()
p=Path('/proc')/str(w['parent_pid'])/'stat';s=p.read_text() if p.exists() else None
members=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  a=parts((p/'stat').read_text())
  if a[0]!='Z' and int(a[2])==w.get('child_pgid',-1):members.append(dict(pid=int(p.name),start_ticks=a[19],cpu_ticks=int(a[11])+int(a[12]),rss_kib=int(a[21])*os.sysconf('SC_PAGE_SIZE')//1024))
 except OSError:pass
phase=r/w.get('phase','elaborate');log=phase/'tool.log';tail=[]
if log.exists():
 with log.open('rb') as f:f.seek(max(0,log.stat().st_size-8192));tail=f.read().decode(errors='replace').splitlines()[-12:]
resource=phase/'resources.jsonl';latest=None
if resource.exists():
 with resource.open('rb') as source:
  source.seek(max(0,resource.stat().st_size-16384));last_rows=source.read().decode(errors='replace').splitlines()
 for line in reversed(last_rows):
  try:latest=json.loads(line);break
  except json.JSONDecodeError:pass
metrics=r/'suite/case_metrics.csv';cases=[]
if metrics.exists():
 lines=metrics.read_text().splitlines();cases=[x for x in csv.DictReader(lines) if None not in x and all(v is not None for v in x.values())]
profile=r/'suite/stage_profile.csv'
v=root/'.cache/d64_state_suite_20261105_r2';actual=json.loads((root/'module_14_lm_head_v4/reports/d64_state_compile_20261105_r2/COMPILED_SOURCES.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();mismatches=[n for n,h in actual.items() if sha(v/n)!=h]
traces={}
for name in ['address_requests.csv','control_trace.csv']:
 path=r/'suite'/name;rows=[];stat=None
 if path.exists():
  stat=path.stat()
  with path.open('rb') as stream:
   offset=max(0,stat.st_size-16384);stream.seek(offset);data=stream.read()
  lines=data.decode(errors='replace').splitlines()
  if offset and lines:lines=lines[1:]
  if data and not data.endswith(b'\n') and lines:lines=lines[:-1]
  rows=[line for line in lines if len(line.split(','))==5][-4:]
 traces[name]=dict(bytes=stat.st_size if stat else None,mtime_ns=stat.st_mtime_ns if stat else None,last_complete_rows=rows)
print(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),cpu_hz=os.sysconf('SC_CLK_TCK'),workflow=w,parent_identity_alive=s is not None and parts(s)[0]!='Z' and parts(s)[19]==parts(w['parent_proc_stat'])[19],members=members,active_lock=(r/'ACTIVE.lock').exists(),latest_resource=latest,reported_cases=cases,stage_profile_tail=profile.read_text().splitlines()[-8:] if profile.exists() else [],tool_tail=tail,passive_trace_tails=traces,source_mismatches=mismatches,source_count=len(actual))))
"""
def main():
 p=subprocess.run(['ssh','-p','7626','-o','BatchMode=yes','-o','ConnectTimeout=15','zhangben@124.16.71.7','/home/zhangben/anaconda3/bin/python','-'],input=REMOTE,text=True,capture_output=True,timeout=45)
 assert p.returncode==0,p.stderr
 result=json.loads(p.stdout);assert not result['source_mismatches'];folder=ROOT/'module_14_lm_head_v4/reports/d64_state_suite_20261105_r2/observations'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S');folder.mkdir(parents=True)
 (folder/'RUNTIME_SNAPSHOT.json').write_text(json.dumps(result,indent=2)+chr(10),encoding='utf-8')
 print(json.dumps(dict(snapshot=str(folder/'RUNTIME_SNAPSHOT.json'),**result),indent=2))
if __name__=='__main__':main()
