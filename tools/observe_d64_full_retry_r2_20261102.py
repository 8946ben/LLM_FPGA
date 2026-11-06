"""Bounded static snapshot of this exact full run; no process or EDA control."""
from pathlib import Path
import datetime,hashlib,json,os
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
R=ROOT/'module_14_lm_head_v4/reports/full_bank_cosim_20261102_r2'
V=ROOT/'.cache/p64_full_bank_cosim_20261102_r2/sim/verilog'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tail(p,size=10000):
 if not p.exists():return {'exists':False}
 n=p.stat().st_size
 with p.open('rb') as f:f.seek(max(0,n-size));text=f.read(size).decode(errors='replace')
 return {'exists':True,'bytes':n,'tail':text}
def main():
 now=datetime.datetime.now(datetime.timezone.utc)
 w=json.loads((R/'FULL_WORKFLOW.json').read_text());procs=[]
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   s=(p/'stat').read_text();v=s[s.rindex(')')+2:].split()
   if v[0]!='Z' and int(v[2])==w.get('child_pgid'):
    procs.append({'pid':int(p.name),'start_ticks':v[19],'rss_kib':int(v[21])*os.sysconf('SC_PAGE_SIZE')//1024,
     'cpu_ticks':int(v[11])+int(v[12]),'cmd':(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')[:1300]})
  except OSError:pass
 parent_match=False
 try:
  old=w['parent_proc_stat'];cur=(Path('/proc')/str(w['parent_pid'])/'stat').read_text()
  parent_match=cur[cur.rindex(')')+2:].split()[19]==old[old.rindex(')')+2:].split()[19]
 except OSError:pass
 plan=json.loads((R/'PLAN.json').read_text());reuse=R/'RTL_AND_STALL_REUSE.json'
 result={'observed_utc':now.isoformat(),'host':os.uname().nodename,'workflow':w,'parent_creation_matches':parent_match,
  'active_lock':(R/'ACTIVE.lock').exists(),'processes':procs,'current_group_rss_kib':sum(p['rss_kib'] for p in procs),
  'available_kib':next(int(x.split()[1]) for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')),
  'reuse_matches_plan':reuse.exists() and json.loads(reuse.read_text())==plan['reuse_sources'],
  'reuse_count':len(plan['reuse_sources']),'plan_sha256':sha(R/'PLAN.json'),
  'qualified_model_sha256':sha(ROOT/'module_14_lm_head_v4/experiments/d64_stream_integration_20261102_r2/mem_model.sv'),
  'actual_model_sha256':sha(V/'file_agent/mem_model.sv') if (V/'file_agent/mem_model.sv').exists() else None,
  'logs':{name:tail(R/name) for name in ['launcher.log','elaborate.log','xsim.log','c_postcheck.log']},
  'stage_profile':tail(V/'stage_profile.csv',4000),
  'returned':{p.name:p.stat().st_size for p in (V.parent/'tv/rtldatafile').glob('*autotvout*.dat')},
  'board':'NOT_RUN','automatic_next_stage':False}
 dest=R/'observations'/now.strftime('%Y%m%d_%H%M%S');dest.mkdir(parents=True)
 (dest/'RUNTIME_SNAPSHOT.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'snapshot_path':str(dest/'RUNTIME_SNAPSHOT.json'),'state':w['state'],'parent_creation_matches':parent_match,
   'group_rss_gib':result['current_group_rss_kib']/1048576,'reuse_matches_plan':result['reuse_matches_plan'],
   'model_matches':result['qualified_model_sha256']==result['actual_model_sha256']}))
if __name__=='__main__':main()
