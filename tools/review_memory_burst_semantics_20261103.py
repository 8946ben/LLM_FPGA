"""Host byte/bit replay of candidate events; full M14 remains unqualified."""
from pathlib import Path
import csv,json,hashlib,re,datetime,collections
from review_memory_growth_20261103 import ROOT,M,ready,sha
def replay_legacy(r):
 p=json.loads((r/'PLAN.json').read_text());w=json.loads((r/'WORKFLOW.json').read_text())
 assert 'mode_legacy' in w['phases'] and w['process_after']==[] and not (r/'ACTIVE.lock').exists()
 for n,h in p['sources'].items():assert sha(ROOT/n)==h
 log=(r/'mode_legacy/tool.log').read_text();assert re.search(r'^BANK_MEMORY_UNIT_PASS pairs=512 widths=8,32,128 ',log,re.M)
 assert not re.search(r'^(?:UVM_FATAL|UVM_ERROR|Fatal:|ERROR:)',log,re.M)
 mem={};depth=off=None;count=collections.Counter();bad=unknown=0
 for row in csv.reader((r/'mode_legacy/memory_events.csv').open()):
  kind=row[0];count[kind]+=1
  if kind=='INIT':depth,off=map(int,row[1:]);mem={};continue
  if kind=='BW':
   a,n,rc=map(int,row[1:]);errors=0
   for j in range(n):
    if 0<=a+j-off<depth:mem[a+j]=(0xa0+j)&255
    else:errors+=1
   assert rc==errors;continue
  a=int(row[1],16);a=a-(1<<64) if a&(1<<63) else a;valid=0<=a-off<depth;assert int(row[3])==(0 if valid else 1)
  if not valid:bad+=1
  if kind=='W':
   if valid:mem[a]=int(row[2],16)
  else:
   expected=mem.get(a) if valid else None
   if expected is None:assert row[2].lower()=='xx';unknown+=1
   else:assert int(row[2],16)==expected
 assert sum(count.values())==2093
 return dict(state='PASS_LEGACY_SUBPHASE_ONLY',overall_workflow_state=w['state'],events=2093,counts=dict(count),boundary_rejections=bad,unknown_reads=unknown,model_sha256=p['model_sha256'],event_sha256=sha(r/'mode_legacy/memory_events.csv'))
def main():
 old=M/'reports/memory_burst_semantics_20261103_r1';legacy=replay_legacy(old)
 (old/'LEGACY_REVIEW.json').write_text(json.dumps(legacy,indent=2)+'\n')
 r,p,w=ready('memory_burst_semantics_20261103_r4');assert p['model_sha256']==legacy['model_sha256']
 phase=r/'mode_pair';log=(phase/'tool.log').read_text();assert re.search(r'^ALLOCATION_MICRO_PASS burst_semantics alias_pairs=512 widths=8,32,128 four_state=1 pages=1$',log,re.M)
 assert not re.search(r'^(?:UVM_FATAL|UVM_ERROR|Fatal:|ERROR:)',log,re.M)
 assert 'BURST_NO_PAGE_CONTROL_PASS' in log
 memory={};depths={};offsets={};readflag={};counts=collections.Counter();unknown=invalid_reads=0
 def addr(s):
  x=int(s,16);return x-(1<<64) if x&(1<<63) else x
 for row in csv.reader((phase/'burst_events.csv').open()):
  kind=row[0];width=int(row[1]);counts[kind]+=1
  if kind=='I':depths[width]=int(row[2]);offsets[width]=int(row[3]);memory[width]={};readflag[width]=0;continue
  a=addr(row[2]);valid=0<=a-offsets[width]<depths[width]
  if kind in ['W','R']:
   bits=row[3].lower();assert len(bits)==width and set(bits)<=set('01xz')
   if kind=='W':
    if valid:memory[width][a]=bits
   else:
    expected=memory[width].get(a,'x'*width) if valid else 'x'*width
    assert bits==expected,(width,a,bits,expected)
    if valid:readflag[width]=1
    else:invalid_reads+=1
    if 'x' in bits or 'z' in bits:unknown+=1
  elif kind in ['WE','RE']:
   n,rc=map(int,row[3:5]);errors=sum(not (0<=a+j-offsets[width]<depths[width]) for j in range(n))
   assert rc==errors,(kind,a,n,rc,errors)
   if kind=='RE':assert int(row[5])==readflag[width]
  elif kind in ['PERR','PRERR']:
   relative=a-offsets[width];eligible=depths[width]>=16 and 0<=relative<=depths[width]-16 and relative%16==0
   assert not eligible and int(row[3])==1
  else:raise AssertionError(kind)
 warnings={'ref':collections.Counter(),'new':collections.Counter()}
 for line in (phase/'warning_events.tsv').read_text().splitlines():
  side,msg=line.split('\t',1);warnings[side][msg]+=1
 assert warnings['ref']==warnings['new'] and sum(warnings['ref'].values())>0
 compare=re.search(r'^CASE_COMPARE_DIAGNOSTIC_TOTAL count=(\d+)$',log,re.M);assert compare and int(compare.group(1))>0
 assert len(memory)==3 and set(memory)=={8,32,128}
 out=dict(state='PASS_INDEPENDENT_BURST_MODEL_SEMANTICS',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
  model_sha256=p['model_sha256'],legacy=legacy,paired_events=sum(counts.values()),paired_counts=dict(counts),unknown_or_z_read_events=unknown,invalid_read_events=invalid_reads,
  warnings_per_model=sum(warnings['ref'].values()),distinct_warning_messages=len(warnings['ref']),warnings_exact_multiset_equal=True,
  direct_expression_vs_typed_four_state_differences=int(compare.group(1)),
  evidence_sha256={n:sha(phase/n) for n in ['burst_events.csv','warning_events.tsv','tool.log','resources.jsonl']},
  limits=['Finite simulated-model semantics, not full RTL/FIFO/AXI pressure or decode qualification',
   'Typed 8/32/128-bit four-state comparisons and actual candidate bit records are used; original direct-expression failures retained',
   'Read flags/range errors/bits independently replayed; no-page unchanged-queue and generic/bank shape assertions executed in SV',
   'Paired aliases cross512MiB; original broader 2093 includes independent byte event replay and generic-width SV assertions'],full_m14='NOT_RUN',board='NOT_RUN',automatic_next_stage=False)
 (r/'INDEPENDENT_REVIEW.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
