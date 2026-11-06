"""Read-only12-case monitor and offline HTML. No launch/stop or EDA source changes."""
from pathlib import Path
import json,datetime,subprocess,sys,argparse,hashlib
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'module_14_lm_head_v4/reports/d64_state_suite_20261105_r1';OUT=R/'monitor';HTML=ROOT/'doc/design/D64StateSuiteMonitor.html'
def dump(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+chr(10),encoding='utf-8');tmp.replace(p)
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def main():
 args=argparse.ArgumentParser();args.add_argument('--sample',action='store_true');args=args.parse_args();OUT.mkdir(parents=True,exist_ok=True);event=None
 if args.sample:
  event=dict(utc=now(),ok=False)
  try:
   p=subprocess.run([sys.executable,str(ROOT/'tools/observe_d64_state_suite_20261105.py')],cwd=ROOT,capture_output=True,text=True,timeout=60);assert p.returncode==0,(p.stdout+p.stderr)[-2000:];result=json.loads(p.stdout)
   assert result['workflow']['parent_pid']==6752 and result['workflow']['parent_proc_stat'].split(')')[-1].split()[19]=='345222604'
   event.update(ok=True,utc=result['utc'],snapshot=Path(result['snapshot']).relative_to(ROOT).as_posix())
  except Exception as exc:event['error']=str(exc)[-2000:]
  dump(OUT/'events'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S.json'),event)
 events=[json.loads(p.read_text(encoding='utf-8')) for p in sorted((OUT/'events').glob('*.json'))];raw=[(p,json.loads(p.read_text(encoding='utf-8'))) for p in sorted((R/'observations').glob('*/RUNTIME_SNAPSHOT.json'))];hz=next((s['cpu_hz'] for p,s in reversed(raw) if s.get('cpu_hz')),None);points=[];previous=None
 for path,s in raw:
  w=s['workflow'];members=s['members'];res=s.get('latest_resource') or {};identity=str(w['parent_pid'])+':'+w['parent_proc_stat'].split(')')[-1].split()[19];member_id=';'.join(str(x['pid'])+':'+x['start_ticks'] for x in members)
  ticks=sum(x['cpu_ticks'] for x in members) if members and all('cpu_ticks' in x for x in members) else None;cpu=None
  if previous and hz and previous['member_id']==member_id and previous['identity']==identity and ticks is not None and previous['ticks'] is not None:
   seconds=(datetime.datetime.fromisoformat(s['utc'])-datetime.datetime.fromisoformat(previous['utc'])).total_seconds();delta=ticks-previous['ticks']
   if seconds>0 and delta>=0:cpu=delta/hz/seconds*100
  point=dict(utc=s['utc'],state=w['state'],phase=w.get('phase'),identity=identity,member_id=member_id,ticks=ticks,cpu=cpu,memory=sum(x['rss_kib'] for x in members)/1048576 if members else None,available=res.get('available_kib')/1048576 if res.get('available_kib') is not None else None,cases=len(s['reported_cases']),reported_cases=s['reported_cases'],stage_tail=s['stage_profile_tail'],source_count=s['source_count'],source_ok=not s['source_mismatches'],snapshot=path.relative_to(ROOT).as_posix(),snapshot_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),terminal=not s['parent_identity_alive'] and not members and not s['active_lock'] and not w['state'].startswith(('EXECUTING','PREPARING')),log_tail=s['tool_tail'])
  points.append(point);previous=point
 data=dict(job='d64_state_suite_20261105_r1',generated_utc=now(),guard_gib=16,guard_spare_gib=32,guard_hours=6,cpu_hz=hz,points=points,events=events,acceptance=json.loads((OUT/'ACCEPTANCE.json').read_text(encoding='utf-8')) if (OUT/'ACCEPTANCE.json').exists() else None)
 dump(OUT/'DATA.json',data);template=(ROOT/'doc/design/templates/d64_state_monitor.template.html').read_text(encoding='utf-8');assert template.count('__DATA__')==1;tmp=HTML.with_suffix('.html.tmp');tmp.write_text(template.replace('__DATA__',json.dumps(data,ensure_ascii=False).replace('<','\\u003c')),encoding='utf-8');tmp.replace(HTML)
 print(json.dumps(dict(html=str(HTML),points=len(points),latest=points[-1]['utc'] if points else None,state=points[-1]['state'] if points else None,reported_cases=points[-1]['cases'] if points else None,terminal=points[-1]['terminal'] if points else False,last_event_ok=events[-1]['ok'] if events else None)))
 if event and not event['ok']:sys.exit(2)
if __name__=='__main__':main()
