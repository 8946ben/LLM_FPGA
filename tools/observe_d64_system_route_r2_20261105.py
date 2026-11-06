"""Readonlysame200MHzrouteattempt;no restart/config/boardactions."""
from pathlib import Path
import subprocess,json,datetime
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'module_14_lm_head_v4/reports/d64_system_200m_20261105_r2'
REMOTE=r'''from pathlib import Path
import json,datetime,os,hashlib
root=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1');r=root/'module_14_lm_head_v4/reports/d64_system_200m_20261105_r2'
w=json.loads((r/'route/WORKFLOW.json').read_text());launch=json.loads((r/'LAUNCH_IDENTITY.json').read_text())
def parts(s):return s[s.rindex(')')+2:].split()
assert w['parent_pid']==launch['pid']==21798 and parts(w['parent_proc_stat'])[19]==parts(launch['proc_stat'])[19]=='350755471'
allp={}
for p in Path('/proc').iterdir():
 if p.name.isdigit():
  try:
   x=parts((p/'stat').read_text());allp[int(p.name)]=dict(pid=int(p.name),ppid=int(x[1]),pgid=int(x[2]),start_ticks=x[19],state=x[0],rss_kib=int(x[21])*os.sysconf('SC_PAGE_SIZE')//1024)
  except OSError:pass
parent=allp.get(w['parent_pid']);live=bool(parent and parent['start_ticks']=='350755471' and parent['state']!='Z');desc={w['parent_pid']}
while True:
 new=desc|{k for k,p in allp.items() if p['ppid'] in desc}
 if new==desc:break
 desc=new
owned=[p for k,p in allp.items() if k in desc and p['state']!='Z'];group=[p for p in allp.values() if p['pgid']==w.get('child_pgid') and p['state']!='Z']
logs={}
for p in (root/'module_14_lm_head_v4/board/build/m14_d64_200m_r2/m14_d64_200m.runs').glob('*/runme.log'):
 hits=[];tail=[]
 with p.open(errors='replace') as f:
  for s in f:
   if any(x.lower() in s.lower() for x in ['ERROR:','got license','failed to get','synth_design completed','synthesis finished']):hits.append(s.strip())
   tail.append(s.rstrip())
   if len(tail)>8:tail.pop(0)
 logs[p.parent.name]=dict(markers=hits,tail=tail)
plan=json.loads((r/'PLAN.json').read_text());hash_ok=all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in plan['source_sha256'].items())
print(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),workflow=w,parent_identity_live=live,lock_exists=(r/'route/ACTIVE.lock').exists(),actual_phase_group=group,descendants_outside_phase_group=[p for p in owned if p['pid']!=w['parent_pid'] and p['pgid']!=w.get('child_pgid')],entry_sources_sha_match=hash_ok,run_logs=logs)))
'''
v=subprocess.run(['ssh','-p','7626','-o','BatchMode=yes','-o','ConnectTimeout=15','zhangben@124.16.71.7','/home/zhangben/anaconda3/bin/python','-'],input=REMOTE.encode(),capture_output=True,timeout=90)
assert v.returncode==0,v.stderr.decode(errors='replace');value=json.loads(v.stdout);name=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S');d=R/'observations'/name;d.mkdir(parents=True);(d/'SNAPSHOT.json').write_text(json.dumps(value,indent=2)+'\n');(R/'LATEST_SNAPSHOT.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps(dict(state=value['workflow']['state'],parent_identity_live=value['parent_identity_live'],lock_exists=value['lock_exists'],entry_sources_sha_match=value['entry_sources_sha_match'],rss_gib=sum(p['rss_kib'] for p in value['actual_phase_group'])/1048576,outside_phase_group=value['descendants_outside_phase_group'],logs=value['run_logs']),indent=2))
