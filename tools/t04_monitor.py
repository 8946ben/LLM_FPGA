"""Read-only T04 sampling and standalone offline charts. Never starts/stops EDA."""
from pathlib import Path
import argparse,csv,datetime,hashlib,io,json,re,subprocess,sys

ROOT=Path(__file__).resolve().parents[1]
JOB='memory_repaired_full_20261103_r1'
REPORT=ROOT/'module_14_lm_head_v4/reports'/JOB
OUT=ROOT/'module_14_lm_head_v4/reports/t04_half_hour_monitor_20261104'
HTML=ROOT/'doc/design/T04SimulationMonitor.html'
TEMPLATE=ROOT/'doc/design/templates/t04_monitor.template.html'
UTC=datetime.timezone.utc

def now():return datetime.datetime.now(UTC).isoformat()
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,data):
    p.parent.mkdir(parents=True,exist_ok=True)
    temp=p.with_suffix(p.suffix+'.tmp');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');temp.replace(p)
def read(p):return json.loads(p.read_text(encoding='utf-8'))

def snapshot_point(path,official):
    s=read(path);w=s['workflow'];members=s['owned_process_group_members'];res=s.get('latest_resource',{})
    phases=list(csv.DictReader(s.get('stage_profile.csv_tail',[])))
    completed=sorted({int(row['stage']) for row in phases if int(row['stage'])>=0})
    times=[];transactions=[]
    for line in s.get('xsim.log_tail',[]):
        m=re.search(r'RTL Simulation : (\d+) / (\d+).*@ "(\d+)"',line)
        if m:times.append(int(m[3])/1e9);transactions.append([int(m[1]),int(m[2])])
        # Simulator diagnostics also carry real simulation timestamps. A warning flood can push HLS progress lines out of the bounded log tail.
        diagnostic=re.match(r'\s*Time:\s*(\d+(?:\.\d+)?)\s*(ps|ns|us|ms)\b',line)
        if diagnostic:times.append(float(diagnostic[1])*{'ps':1e-9,'ns':1e-6,'us':1e-3,'ms':1}[diagnostic[2]])
        finish=re.search(r'\$finish called at time\s*:\s*(\d+)\s*ps',line)
        if finish:times.append(int(finish[1])/1e9)
    if s.get('last_vcd_times_ps'):times.extend(x/1e9 for x in s['last_vcd_times_ps'])
    sources_ok=not any(s.get(k,[]) for k in ['actual_compiled_source_mismatches','original_frozen_source_mismatches','original_reused_source_mismatches']) and s.get('actual_sources_identical_to_qualified_first5',False)
    return dict(utc=s['utc'],official=official,state=w['state'],parent_alive=s['parent_identity_alive'],
        lock=s['active_locks'],members=members,identity=str(w['parent_pid'])+':'+w['parent_proc_stat'].split(')')[-1].split()[19],
        rss_gib=sum(x['rss_kib'] for x in members)/1048576 if members else None,
        available_gib=res.get('available_kib',0)/1048576 if res.get('available_kib') is not None else None,
        elapsed_h=res.get('elapsed_s',0)/3600 if 'elapsed_s' in res else None,
        cpu_ticks=sum(x['cpu_ticks'] for x in members) if members and all('cpu_ticks' in x for x in members) else None,
        cpu_identity=';'.join('%s:%s'%(x['pid'],x['start_ticks']) for x in sorted(members,key=lambda x:x['pid'])),
        simulation_ms=max(times) if times else None,transactions=transactions[-1] if transactions else None,
        completed_stages=completed,tv_bytes=sum(s.get('returned_tv_sizes',{}).values()),tv_nonempty=sum(v>0 for v in s.get('returned_tv_sizes',{}).values()),
        tv_count=len(s.get('returned_tv_sizes',{})),sources_ok=sources_ok,source_count=s.get('actual_compiled_source_count'),
        terminal=not s['parent_identity_alive'] and not members and not s['active_locks'] and not w['state'].startswith(('EXECUTING','PREPARING')),
        snapshot=path.relative_to(ROOT).as_posix(),snapshot_sha256=digest(path),xsim_log_bytes=s.get('xsim.log_bytes'),dsp_warning_observed=any('OPMODE Input Warning' in line for line in s.get('xsim.log_tail',[])),log_tail=s.get('xsim.log_tail',[])[-5:])

def sample():
    OUT.mkdir(parents=True,exist_ok=True)
    stamp=datetime.datetime.now(UTC).strftime('%Y%m%d_%H%M%S')
    event=dict(utc=now(),kind='scheduled_sample',job=JOB)
    try:
        p=subprocess.run([sys.executable,str(ROOT/'tools/observe_memory_repaired_20261103.py'),JOB,'--compact'],cwd=ROOT,capture_output=True,text=True,timeout=110)
        assert p.returncode==0,(p.stderr+p.stdout)[-2400:]
        result=json.loads(p.stdout);path=Path(result['snapshot']);raw=read(path)
        assert raw['workflow']['parent_pid']==7002 and raw['workflow']['parent_proc_stat'].split(')')[-1].split()[19]=='332138782','Unexpected job identity'
        event.update(utc=raw['utc'],ok=True,snapshot=path.relative_to(ROOT).as_posix(),sha256=digest(path))
        # Small independent OS metadata read. It never connects to a simulator console.
        if not (OUT/'CPU_CLOCK.json').exists():
            meta=subprocess.run(['ssh','-p','7626','-o','BatchMode=yes','-o','ConnectTimeout=15','zhangben@124.16.71.7',
                '/home/zhangben/anaconda3/bin/python','-c',"'import os,json; print(json.dumps(dict(hz=os.sysconf(\"SC_CLK_TCK\"),logical_cpus=os.cpu_count())))'"],capture_output=True,text=True,timeout=30)
            if meta.returncode==0:
                cpu=json.loads(meta.stdout);assert cpu['hz']>0;cpu.update(utc=now(),bound_parent='7002:332138782');dump(OUT/'CPU_CLOCK.json',cpu)
            else:event['cpu_metadata_error']='CPU clock query unavailable; CPU percent remains blank'
    except Exception as error:
        event.update(ok=False,error=str(error)[-2400:])
    dump(OUT/'samples'/(stamp+'.json'),event)
    return event

def render():
    OUT.mkdir(parents=True,exist_ok=True)
    events=[read(p) for p in sorted((OUT/'samples').glob('*.json'))]
    official={x['snapshot'] for x in events if x.get('ok')}
    points=[];rejected=[]
    for path in sorted((REPORT/'observations').glob('*/RUNTIME_SNAPSHOT.json')):
        try:points.append(snapshot_point(path,path.relative_to(ROOT).as_posix() in official))
        except Exception as error:rejected.append(dict(path=path.relative_to(ROOT).as_posix(),error=str(error)))
    # One actual snapshot per timestamp; do not interpolate missing samples.
    points=list({p['utc']:p for p in points}.values());points.sort(key=lambda p:p['utc'])
    cpu=read(OUT/'CPU_CLOCK.json') if (OUT/'CPU_CLOCK.json').exists() else None
    previous=None
    for p in points:
        p['cpu_percent']=None;p['cpu_window_s']=None
        if cpu and previous and p['identity']==previous['identity'] and p['cpu_identity']==previous['cpu_identity'] and p['cpu_ticks'] is not None and previous['cpu_ticks'] is not None:
            dt=(datetime.datetime.fromisoformat(p['utc'])-datetime.datetime.fromisoformat(previous['utc'])).total_seconds()
            delta=p['cpu_ticks']-previous['cpu_ticks']
            if dt>0 and delta>=0:p['cpu_percent']=delta/cpu['hz']/dt*100;p['cpu_window_s']=dt
        previous=p
    dataset=dict(job=JOB,generated_utc=now(),cadence_minutes=30,cpu_clock=cpu,points=points,events=events,rejected=rejected,
        acceptance=read(OUT/'ACCEPTANCE.json') if (OUT/'ACCEPTANCE.json').exists() else None,
        guard_group_gib=64,guard_available_gib=32,guard_runtime_h=48,
        scope='Single original old_chinese/d64/T4096/B1024/dual BF16/debug1 strong-delay RTL call. No FPGA throughput or numerical/FIFO PASS inferred.',
        note='Historical points are irregular observations. Official half-hour records start at monitor creation. CPU100%=one core, averaged between adjacent same-identity snapshots. Logged simulation time is a last-observed lower bound, not completion percentage.')
    dump(OUT/'DATA.json',dataset)
    safe=json.dumps(dataset,ensure_ascii=False).replace('<','\\u003c')
    template=TEMPLATE.read_text(encoding='utf-8');assert template.count('__T04_DATA__')==1
    temp=HTML.with_suffix('.html.tmp');temp.write_text(template.replace('__T04_DATA__',safe),encoding='utf-8');temp.replace(HTML)
    latest=points[-1] if points else None
    return dict(html=str(HTML),points=len(points),official_samples=sum(p['official'] for p in points),last=latest,
        last_sample_ok=events[-1].get('ok') if events else None,terminal=latest['terminal'] if latest else False)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--sample',action='store_true');args=parser.parse_args()
    event=sample() if args.sample else None
    result=render();result.pop('last',None)
    if event:result['sampling']=event
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if event and not event['ok']:sys.exit(2)
if __name__=='__main__':main()
