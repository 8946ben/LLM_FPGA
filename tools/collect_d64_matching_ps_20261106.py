"""Collect final matching PS artifacts and raw earlier failures, never run firmware."""
from pathlib import Path
import subprocess,json,base64,hashlib
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'module_14_lm_head_v4/reports/d64_matching_ps_20261106_r6';OUT=R/'collected'
REMOTE=r'''
from pathlib import Path
import subprocess,json,base64,hashlib,datetime
root=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1');m=root/'module_14_lm_head_v4';r=m/'reports/d64_matching_ps_20261106_r6';b=m/'build/d64_matching_ps_20261106_r6';bsp=b/'bsp/psu_cortexa53_0';e=m/'experiments/d64_matching_ps_20261106_r6'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def parts(s):return s[s.rindex(')')+2:].split()
w=json.loads((r/'execution/WORKFLOW.json').read_text());launch=json.loads((r/'LAUNCH_IDENTITY.json').read_text());assert w['state']=='BSP_ELF_RETURNED_AWAITING_INDEPENDENT_REVIEW';assert w['parent_pid']==launch['pid']==21725 and parts(w['parent_proc_stat'])[19]==parts(launch['proc_stat'])[19]=='354960826'
assert not list((m/'reports').rglob('ACTIVE.lock'))
proof=[]
for i in range(1,7):
 rr=m/('reports/d64_matching_ps_20261106_r'+str(i));ww=json.loads((rr/'execution/WORKFLOW.json').read_text());ids={(ww['parent_pid'],parts(ww['parent_proc_stat'])[19])}
 for p in (rr/'execution').glob('*/resources.jsonl'):
  for line in p.open():
   x=json.loads(line);assert x['rss_kib']<=16*1048576 and x['available_kib']>=32*1048576
   ids.update((a['pid'],a['start_ticks']) for a in x['members'])
 for pid,start in ids:
  p=Path('/proc')/str(pid)/'stat'
  if p.exists():a=parts(p.read_text());assert a[19]!=start or a[0]=='Z'
 assert not ww['process_after'] and not (rr/'execution/ACTIVE.lock').exists()
 proof.append(dict(stage=i,state=ww['state'],observed_identities_absent=len(ids)))
plan=json.loads((e/'PLAN.json').read_text());assert all(sha(e/n)==h for n,h in plan['source_sha256'].items())
copy=json.loads((r/'BSP_COPY_RECEIPT.json').read_text());assert all(sha(b/n)==h for n,h in copy['files'].items())
files={str(p.relative_to(r)):p for p in r.rglob('*') if p.is_file() and p.suffix!='.o'}
for i in range(1,6):
 rr=m/('reports/d64_matching_ps_20261106_r'+str(i))
 for p in rr.rglob('*'):
  if p.is_file() and (p.suffix in ['.log','.json','.jsonl']):files['previous_r'+str(i)+'/'+str(p.relative_to(rr))]=p
for rel in ['include/xparameters.h','include/xtime_l.h','include/xlm_head_v4_partial_proto_hw.h','include/lwipopts.h','include/xlwipconfig.h','lib/libxil.a','lib/liblwip4.a']:
 files['bsp/'+rel]=bsp/rel
phy=list(bsp.glob('libsrc/lwip211*/src/contrib/ports/xilinx/netif/xemacpsif_physpeed.c'));assert len(phy)==1;files['bsp/xemacpsif_physpeed.c']=phy[0]
files['bsp/Makefile']=b/'bsp/Makefile';files['bsp/m14_d64_bsp.mss']=b/'bsp/m14_d64_bsp.mss'
for elf in ['m14_d64_loader.elf','m14_d64_test.elf']:
 p=subprocess.run(['/tools/Xilinx/Vitis/2022.2/gnu/aarch64/lin/aarch64-none/bin/aarch64-none-elf-nm','-u',str(r/'software'/elf)],capture_output=True);assert p.returncode==0 and not p.stdout.strip()
gcc='/tools/Xilinx/Vitis/2022.2/gnu/aarch64/lin/aarch64-none/bin/aarch64-none-elf-gcc';p=subprocess.run([gcc,'-E','-P','-x','c','-I'+str(bsp/'include'),'-'],input=b'#include "xparameters.h"\n#include "xtime_l.h"\nD64_FREQ COUNTS_PER_SECOND\nD64_GEM XPAR_XEMACPS_0_BASEADDR\n',capture_output=True);assert p.returncode==0
print(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),workflow=w,process_proof=proof,all_bsp_copy_hashes_match=True,all_frozen_ps_sources_match=True,undefined_symbols_empty=True,preprocessor=p.stdout.decode(),files={n:dict(base64=base64.b64encode(p.read_bytes()).decode(),sha256=sha(p)) for n,p in files.items()})))
'''
p=subprocess.run(['ssh','-p','7626','-o','BatchMode=yes','zhangben@124.16.71.7','/home/zhangben/anaconda3/bin/python','-'],input=REMOTE.encode(),capture_output=True,timeout=180);assert p.returncode==0,p.stderr.decode(errors='replace');v=json.loads(p.stdout);assert not OUT.exists();OUT.mkdir()
for name,item in v['files'].items():
 assert not Path(name).is_absolute() and '..' not in Path(name).parts
 data=base64.b64decode(item.pop('base64'));assert hashlib.sha256(data).hexdigest()==item['sha256'];target=OUT/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
(R/'COLLECTION.json').write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in v.items() if k not in ['files','preprocessor','workflow']},indent=2));print('\n'.join(x for x in v['preprocessor'].splitlines() if x.startswith('D64_')))
