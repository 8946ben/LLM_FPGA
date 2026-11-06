"""Decode RLE streams and prove exact original per-cycle trace equivalence."""
from pathlib import Path
import json,csv,hashlib,datetime,itertools
from review_memory_growth_20261103 import ready,ROOT,M,sha
NAME='fifo_rle_monitor_20261103_r1';E=M/'experiments'/NAME
def decoded(path):
 for n,value in csv.reader(path.open()):
  n=int(n);value=int(value);assert n>0
  for _ in range(n):yield value
def main():
 r,p,w=ready(NAME);changes=json.loads((E/'MONITOR_CHANGES.json').read_text());text=(E/'df_fifo_monitor.svh').read_text()
 assert sha(E/'df_fifo_monitor.svh')==p['candidate_monitor_sha256']==changes['candidate_sha256']
 assert text.replace('DF_FIFO_MONITOR__SV','DF_FIFO_MONITOR_RLE__SV').replace('class df_fifo_monitor extends','class df_fifo_monitor_rle extends')==(E/'df_fifo_monitor_rle.svh').read_text()
 for a,b in reversed(changes['edits']):assert text.count(b)==1;text=text.replace(b,a)
 assert text==(E/'df_fifo_monitor_original.svh').read_text()
 original=r/'mode_0/old_depth.csv';depth=r/'mode_0/new_depth.csv.depth.rle';block=r/'mode_0/new_depth.csv.block.rle';count=0
 missing=object()
 for observed,a,b in itertools.zip_longest(csv.reader(original.open()),decoded(depth),decoded(block),fillvalue=missing):
  assert observed is not missing and a is not missing and b is not missing
  assert list(map(int,observed))==[a,b];count+=1
 assert count==20000
 assert (r/'mode_0/old_status.csv').read_bytes()==(r/'mode_0/new_status.csv').read_bytes()
 samples={}
 for mode,n in [(0,20000),(1,2000000)]:
  path=r/('mode_'+str(mode));rows=[[int(x) for x in row] for row in csv.reader((path/'allocation_samples.csv').open())]
  assert len(rows)==6 and rows[0][1]==0 and rows[-1][1]==n+1
  assert rows[-1][3:]==[n,n]
  assert sum(int(x[0]) for x in csv.reader((path/'new_depth.csv.depth.rle').open()))==n
  assert sum(int(x[0]) for x in csv.reader((path/'new_depth.csv.block.rle').open()))==n
  log=(path/'tool.log').read_text();assert ('ALLOCATION_MICRO_PASS fifo_rle mode=%d samples=%d retained=0'%(mode,n)) in log
  samples[str(mode)]={'samples':n,'kernel_rss_start_kib':rows[0][2],'kernel_rss_end_kib':rows[-1][2],'growth_mib':(rows[-1][2]-rows[0][2])/1024,'peak_group_rss_kib':w['phases']['mode_'+str(mode)]['peak_group_rss_kib']}
 stable=r/'mode_1';assert list(csv.reader((stable/'new_depth.csv.depth.rle').open()))==[['2000000','0']]
 assert list(csv.reader((stable/'new_depth.csv.block.rle').open()))==[['2000000','2']]
 assert samples['1']['growth_mib']<2,'Stable RLE stream still allocates significantly'
 out={'state':'PASS_INDEPENDENT_LOSSLESS_FIFO_RLE_TRACE','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'monitor_sha256':p['candidate_monitor_sha256'],
  'exact_original_cycles_compared':20000,'original_channel_status_byte_equal':True,'stable_cycles':2000000,'stable_rle_records':2,'samples':samples,
  'evidence_sha256':{str(x.relative_to(r)):sha(x) for x in r.rglob('*') if x.is_file() and x.suffix in ['.csv','.rle','.log','.jsonl']},
  'limits':['Monitor unit only; actual FIFO depth/occupancy/deadlock qualification requires completed full RTL',
   'Trace schema changes to separate lossless run_length,value columns; original channel-status fields preserved',
   'Long constant traces retain no per-cycle queue; high-activity trace disk size still depends on transitions'],
  'full_m14':'NOT_RUN','board':'NOT_RUN','automatic_next_stage':False}
 (r/'INDEPENDENT_REVIEW.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='evidence_sha256'},indent=2))
if __name__=='__main__':main()
