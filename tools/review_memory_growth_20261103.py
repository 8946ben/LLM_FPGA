"""Independent replay of finite memory probes; never grants full RTL qualification."""
from pathlib import Path
import csv,hashlib,json,re,datetime
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';OUT=M/'reports/memory_growth_diagnosis_20261103_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ready(folder):
 r=M/'reports'/folder;p=json.loads((r/'PLAN.json').read_text());w=json.loads((r/'WORKFLOW.json').read_text())
 assert w['state']=='TOOL_PASS_AWAITING_INDEPENDENT_REVIEW',folder
 assert w['process_after']==[] and not (r/'ACTIVE.lock').exists(),folder
 for n,h in p['sources'].items():assert sha(ROOT/n)==h,n
 for phase,metrics in w['phases'].items():
  resource=r/phase/'resources.jsonl'
  data=[json.loads(line) for line in resource.read_text().splitlines() if line]
  assert data and max(x['rss_kib'] for x in data)==metrics['peak_group_rss_kib'],(folder,phase)
  for x in data:
   assert sum(member['rss_kib'] for member in x['members'])==x['rss_kib'],(folder,phase)
   assert len({member['pid'] for member in x['members']})==len(x['members'])
 return r,p,w
def rows(r,case):
 f=r/case/'allocation_samples.csv';result=[[int(x) for x in row] for row in csv.reader(f.open())]
 lines=(r/case/'tool.log').read_text(errors='replace').splitlines()
 assert any(x.startswith('ALLOCATION_MICRO_PASS ') for x in lines),case
 assert not any(x.startswith(('UVM_FATAL','UVM_ERROR','Fatal:','ERROR:')) and not re.fullmatch(r'UVM_(?:FATAL|ERROR)\s*:\s*0\s*',x) for x in lines)
 assert len(result)>=5,case
 return result
def simple(r,case,n,expected):
 data=rows(r,case)
 assert data[0][1]==0,case
 for mode,count,rss,total in data:
  assert 0<=count<=n+1 and rss>0
  assert total==expected(min(count,n),mode),(case,count,total)
 return {'start_kernel_rss_kib':data[0][2],'end_kernel_rss_kib':data[-1][2],
  'growth_mib':(data[-1][2]-data[0][2])/1024,'csv_sha256':sha(r/case/'allocation_samples.csv')}
def byte_sum(count):
 cycle=sum(range(256));q,rem=divmod(count,256)
 return q*cycle+sum(range(rem))
def main():
 out={'state':'PASS_INDEPENDENT_FINITE_MEMORY_CAUSAL_REVIEW','reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'experiments':{}}
 r,p,w=ready('memory_allocation_micro_20261103_r2');tab={}
 for mode in range(6):
  tab[str(mode)]=simple(r,'mode_'+str(mode),100000,lambda n,m:0 if m in [0,5] else n*15 if m==4 else byte_sum(n))
 out['experiments']['allocation']=tab
 r,p,w=ready('memory_queue_probe_20261103_r1');tab={}
 for mode in range(4):
  data=rows(r,'mode_'+str(mode))
  for m,count,rss,retained,arq,rq,num,total in data:
   count=min(count,20000);assert total==count*6 and arq==rq==0
   assert retained==num==(count if mode==0 else 0)
  tab[str(mode)]={'retained_after_20000':data[-1][3],'growth_mib':(data[-1][2]-data[0][2])/1024,'csv_sha256':sha(r/('mode_'+str(mode))/'allocation_samples.csv')}
 out['experiments']['queue_roles']=tab
 r,p,w=ready('memory_reuse_probe_20261103_r1');tab={}
 for dbg in ['all','default']:
  for mode in [2,6,7,8]:tab[dbg+'_'+str(mode)]=simple(r,'mode_'+dbg+'_'+str(mode),1000000,lambda n,m:byte_sum(n))
 out['experiments']['reuse_debug']=tab
 r,p,w=ready('memory_poll_probe_20261103_r3');tab={};traces={}
 for mode in range(3):
  case='mode_'+str(mode);data=rows(r,case)
  assert data[0][2]==0
  for m,cycles,polls,rss,retained,ar,rd,pending in data:
   assert polls==ar==rd and pending==0
   assert retained==(polls if mode<2 else 0)
  assert 200000<=data[-1][1]<=202100
  trace=list(csv.reader((r/case/'wire_events.csv').open()))
  assert len(trace)==data[-1][2]*2
  for i in range(0,len(trace),2):
   a,b=trace[i:i+2];assert a[0]=='A' and b[0]=='R' and int(a[2])==int(b[2])==i//2+1
   assert int(a[3])==int(b[3])==0 and int(a[1])<=int(b[1])
  traces[mode]=trace
  tab[str(mode)]={'cycles':data[-1][1],'polls':data[-1][2],'growth_mib':(data[-1][3]-data[0][3])/1024,
   'retained':data[-1][4],'wire_sha256':sha(r/case/'wire_events.csv'),'csv_sha256':sha(r/case/'allocation_samples.csv')}
 assert traces[0]==traces[2],'Master guard changed observed wire traffic'
 out['experiments']['real_control_poll']=tab
 out['real_control_poll_memory_growth_reduction_percent']=100*(1-tab['1']['growth_mib']/tab['0']['growth_mib'])
 out['master_guard_wire_trace_exact_equal']=True
 r,p,w=ready('memory_nested_queue_probe_20261103_r1');tab={}
 for mode in range(6):tab[str(mode)]=simple(r,'mode_'+str(mode),1000000,lambda n,m:0 if m==0 else n)
 out['experiments']['nested_queue']=tab
 r,p,w=ready('memory_init_probe_20261103_r1');tab={}
 for linking in ['default','all']:
  for mode in [0,1]:
   case='mode_'+linking+'_'+str(mode);data=rows(r,case)
   assert [(x[1],x[2]) for x in data]==[(0,0),(1,67108864)]+[(2,i*16777216) for i in range(1,5)]+[(3,67108864)]
   for m,phase,count,rss,total in data:
    assert m==mode and rss>0
    q,rem=divmod(count,256)
    expected=q*sum(range(256))+sum((i*17+3)&255 for i in range(rem))
    assert total==(expected if phase>=2 else 0),(case,phase,count,total)
   tab[linking+'_'+str(mode)]={'bytes_checked_by_sv':67108864,'independently_recomputed_checksum':data[-1][4],
    'start_kernel_rss_kib':data[0][3],'loaded_kernel_rss_kib':data[1][3],'end_kernel_rss_kib':data[-1][3],
    'peak_group_rss_kib':w['phases'][case]['peak_group_rss_kib'],'csv_sha256':sha(r/case/'allocation_samples.csv')}
 out['experiments']['exact_model_initialization']=tab
 r,p,w=ready('memory_random_probe_20261103_r2');tab={}
 for mode in range(4):
  case='mode_'+str(mode);data=rows(r,case)
  assert [x[1] for x in data]==[0,5000,10000,15000,20000,20001]
  for m,count,rss,total in data:
   assert m==mode and rss>0 and 0<=total<=min(count,20000)*256
   if mode==0:assert total==0
  for a,b in zip(data,data[1:]):assert 0<=b[3]-a[3]<=min(b[1]-a[1],5000)*256
  assert data[-1][3]==data[-2][3]
  lines=(r/case/'tool.log').read_text().splitlines()
  assert any(x.startswith('ALLOCATION_MICRO_PASS mode=%d n=20000 '%mode) and x.endswith('checksum='+str(data[-1][3])) for x in lines)
  tab[str(mode)]={'start_kernel_rss_kib':data[0][2],'end_kernel_rss_kib':data[-1][2],
   'growth_mib':(data[-1][2]-data[0][2])/1024,'checksum':data[-1][3],
   'peak_group_rss_kib':w['phases'][case]['peak_group_rss_kib'],'csv_sha256':sha(r/case/'allocation_samples.csv')}
 out['experiments']['randomization']=tab
 out['reviewed_case_count']=sum(len(x) for x in out['experiments'].values())
 assert out['reviewed_case_count']==35
 out['limits']=['Original full M14 remains protected-stop INCOMPLETE; no board/200MHz or decode qualification',
  'Real bus fixture uses no-delay constant status slave; full frozen control callback includes random stalls and LEN_WIDTH4 vs fixture8 (all requests length0)',
  'RSS is measured in xsimkernel through /proc/self/status; process group peak is a separate saved metric',
  'New/null growth does not by itself identify allocator internals as a general XSim defect; exact environment/workload only',
  'No claim that all128GiB or a full16GiB budget has been explained or qualified',
  'Initialization byte checks executed in SV; host recomputes checkpoint checksums, not an independent dump of all bytes',
  'Randomization audit checks recorded aggregate bounds and source assertions; individual draws not saved, distributions/streams not independently qualified']
 (OUT/'INDEPENDENT_REVIEW.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
