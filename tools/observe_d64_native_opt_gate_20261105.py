from pathlib import Path
import subprocess,json,datetime
ROOT=Path(__file__).resolve().parents[1]
REMOTE=r"""from pathlib import Path
import json,os,datetime
r=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1/module_14_lm_head_v4/reports/d64_native_opt_gate_20261105_r2');w=json.loads((r/'WORKFLOW.json').read_text());parts=lambda s:s[s.rindex(')')+2:].split();stat=Path('/proc')/str(w['parent_pid'])/'stat';alive=False
if stat.exists():a=parts(stat.read_text());alive=a[0]!='Z' and a[19]==parts(w['parent_proc_stat'])[19]
members=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  a=parts((p/'stat').read_text())
  if a[0]!='Z' and int(a[2])==w.get('child_pgid',-1):members.append(dict(pid=int(p.name),start_ticks=a[19],rss_kib=int(a[21])*os.sysconf('SC_PAGE_SIZE')//1024))
 except FileNotFoundError:pass
log=r/w.get('phase','elaborate')/'tool.log'
print(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),workflow=w,parent_identity_alive=alive,members=members,active_lock=(r/'ACTIVE.lock').exists(),phase_tail=log.read_text(errors='replace')[-1500:] if log.exists() else None)))
"""
def main():
 p=subprocess.run(['ssh','-p','7626','-o','BatchMode=yes','-o','ConnectTimeout=15','zhangben@124.16.71.7','/home/zhangben/anaconda3/bin/python','-'],input=REMOTE,text=True,capture_output=True,timeout=40);assert p.returncode==0,p.stderr;result=json.loads(p.stdout);folder=ROOT/'module_14_lm_head_v4/reports/d64_native_opt_gate_20261105_r2/observations'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S');folder.mkdir(parents=True);(folder/'RUNTIME_SNAPSHOT.json').write_text(json.dumps(result,indent=2)+chr(10),encoding='utf-8');print(json.dumps(dict(snapshot=str(folder/'RUNTIME_SNAPSHOT.json'),**result),indent=2))
if __name__=='__main__':main()
