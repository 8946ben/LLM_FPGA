"""Replay every actual AXI read/write of finite control-RTL regression."""
from pathlib import Path
import csv,hashlib,json,datetime
from review_memory_growth_20261103 import ready,rows,ROOT,M,sha
NAME='memory_control_regression_20261103_r1'
def main():
 r,p,w=ready(NAME);s=M/'reports/memory_growth_diagnosis_20261103_r1/sources';e=M/'experiments'/NAME
 collected=json.loads((r/'COLLECTION_REVIEW.json').read_text())
 assert collected['parent_identity_present'] is False and collected['process_after']==[] and not collected['active_lock']
 for n,h in collected['compiled_source_sha256'].items():
  if n=='micro.prj':continue
  local=e/n if (e/n).exists() else s/n if (s/n).exists() else s/'svtb'/n
  assert sha(local)==h,n
 env=(s/'lm_head_v4_partial_proto_subsystem/lm_head_v4_partial_proto_env.sv').read_text()
 start=env.index('    class axi_latency_control ');end=env.index('endclass',start)+len('endclass')
 assert (e/'original_latency.svh').read_text()==env[start:end]+'\n'
 assert p['control_rtl_sha256']==sha(s/'lm_head_v4_partial_proto_control_s_axi.v')
 out={'state':'PASS_INDEPENDENT_FINITE_CONTROL_REGISTER_REGRESSION','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'actual_compiled_sources_checked':len(collected['compiled_source_sha256'])-1,'cases':{},'full_m14':'NOT_RUN','board':'NOT_RUN'}
 for mode in range(3):
  case='mode_'+str(mode)
  samples=rows(r,case) if mode!=2 else [[int(x) for x in row] for row in csv.reader((r/case/'allocation_samples.csv').open())]
  # Negative control has three resource checkpoints rather than the normal six.
  log=(r/case/'tool.log').read_text().splitlines()
  assert any(x.startswith('ALLOCATION_MICRO_PASS actual_control_register_regression mode='+str(mode)) for x in log)
  for line in log:
   if line.startswith(('UVM_ERROR','UVM_FATAL','ERROR:','Fatal:')):
    assert line.strip() in ['UVM_ERROR :    0','UVM_FATAL :    0'],line
  results=[[int(x) for x in row] for row in csv.reader((r/case/'results.csv').open())]
  assert len(results)==(1 if mode==2 else 4)
  events=list(csv.reader((r/case/'wire_events.csv').open()));read_transactions=[];write_transactions=[];done_events=[]
  pending_r=None;pending_aw=None;pending_w=None
  for kind,cycle,addr,value in events:
   cycle,addr,value=int(cycle),int(addr),int(value)
   if kind=='AR':assert pending_r is None;pending_r=(cycle,addr)
   elif kind=='R':
    assert pending_r is not None and cycle>=pending_r[0]
    read_transactions.append((pending_r[1],value,cycle));pending_r=None
   elif kind=='AW':assert pending_aw is None;pending_aw=(cycle,addr)
   elif kind=='W':assert pending_w is None;pending_w=(cycle,value)
   elif kind=='B':
    assert pending_aw and pending_w and cycle>=max(pending_aw[0],pending_w[0]) and value==0
    write_transactions.append((pending_aw[1],pending_w[1]));pending_aw=pending_w=None
   elif kind=='DONE':done_events.append((cycle,addr,value))
   else:raise AssertionError(kind)
  assert pending_r is pending_aw is pending_w is None
  assert len(done_events)==(0 if mode==2 else 4)
  cursor=0;total_polls=0;delays=[]
  for row in results:
   index,dbg,cap,st,tok,sc,cr,detected,done_cycle,observed,polls=row
   assert dbg==(1 if index==1 else 0) and cap==(0 if index==2 else 1024)
   assert write_transactions[index*3:index*3+3]==[(0x48,dbg),(0x40,cap),(0,1)]
   rr=read_transactions[cursor:cursor+3]
   assert [(a,v) for a,v,_ in rr[:2]]==[(0x48,dbg),(0x40,cap)]
   assert rr[2][0]==0 and rr[2][1]&2==0;cursor+=3
   actual_polls=read_transactions[cursor:cursor+polls];cursor+=polls;total_polls+=polls
   assert len(actual_polls)==polls and all(a==0 for a,_,_ in actual_polls)
   assert all(v&2==0 for _,v,_ in actual_polls[:-1])
   if mode==2:
    assert detected==0 and done_cycle==0 and all(v&2==0 for _,v,_ in actual_polls)
    assert 10000<=observed<=13000
   else:
    expected=[(0x50,1 if cap==0 else 0),(0x60,0xffffffff if cap==0 else 0x2345 if dbg else 0x1234),
     (0x70,0 if cap==0 else 0x40000000 if dbg else 0x3f800000),
     (0x90,0 if cap==0 else 0x22222222 if dbg else 0x11111111),
     (0xa0,0 if cap==0 else 2),(0xa4,0 if cap==0 else 1),(0x80,0 if cap==0 else 17 if dbg else 11)]
    assert detected==1 and actual_polls[-1][1]&2==2
    assert done_events[index]==(done_cycle,index+1,expected[0][1])
    assert actual_polls[-1][2]>=done_cycle and 0<=observed-done_cycle<=3000
    assert [(a,v) for a,v,_ in read_transactions[cursor:cursor+7]]==expected;cursor+=7
    assert [st,tok,sc,cr]==[v for _,v in expected[:4]]
    a,v,_=read_transactions[cursor];assert a==0 and v&2==0;cursor+=1
    delays.append(observed-done_cycle)
  assert cursor==len(read_transactions)
  assert len(write_transactions)==3*len(results)
  for m,index,cycle,rss,polls,retained,rd,wr in samples:
   assert m==mode and rss>0 and retained==(rd if mode==0 else 0)
  assert samples[-1][4]==total_polls and samples[-1][6]==len(read_transactions) and samples[-1][7]==len(write_transactions)
  out['cases'][str(mode)]={'calls_completed':len(done_events),'polls':total_polls,'reads_checked':len(read_transactions),
   'writes_checked':len(write_transactions),'done_detection_delays_cycles':delays,
   'kernel_rss_growth_mib':(samples[-1][3]-samples[0][3])/1024,
   'peak_group_rss_kib':w['phases'][case]['peak_group_rss_kib'],
   'results_sha256':sha(r/case/'results.csv'),'wire_sha256':sha(r/case/'wire_events.csv'),
   'samples_sha256':sha(r/case/'allocation_samples.csv')}
 a=out['cases']['0']['kernel_rss_growth_mib'];b=out['cases']['1']['kernel_rss_growth_mib']
 out['finite_fixture_growth_reduction_percent']=100*(1-b/a)
 out['limits']=['Fake compute supplies fixed outputs/done; no actual M14 algorithm, DDR, FIFO or real error-path qualification',
  'Exact control RTL/LEN4/original latency class; changed poll schedule changes random call order; not the original full frozen stall stream',
  'Guard and cadence applied together: separate effects require earlier orthogonal probes, not attribution from this combined comparison',
  'No claim of stable asymptotic memory, completed full simulation or 16GiB budget; higher group peak in fixed variant is not lower peak qualification',
  'No sequence/transaction pooling applied; original allocation continues per poll']
 (r/'INDEPENDENT_REVIEW.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
