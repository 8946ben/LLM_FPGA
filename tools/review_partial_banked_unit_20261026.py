from pathlib import Path
import json,hashlib,re
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'module_14_lm_head_v4/reports/sim_memory_bank_20261026_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 workflow=json.loads((R/'UNIT_WORKFLOW.json').read_text());assert workflow['state']=='TOOL_PASS_AWAITING_INDEPENDENT_EVENT_REVIEW'
 log=(R/'simulate.log').read_text();assert re.search(r'^BANK_MEMORY_UNIT_PASS pairs=512 widths=8,32,128 ',log,re.M)
 assert not re.search(r'^(?:Fatal:|FATAL_ERROR:|ERROR:)',log,re.M)
 memory={};depth=offset=None;counts=dict(W=0,R=0,BW=0,INIT=0);bounds=0;unknown=0
 for line in (R/'memory_events.csv').read_text().splitlines():
  x=line.split(',');kind=x[0];counts[kind]+=1
  if kind=='INIT':depth,offset=map(int,x[1:]);memory={};continue
  if kind=='BW':
   addr,n,errors=map(int,x[1:]);bad=0
   for i in range(n):
    if 0<=addr+i-offset<depth:memory[addr+i]=(0xa0+i)&255
    else:bad+=1
   assert errors==bad;continue
  addr=int(x[1],16);addr=addr-(1<<64) if addr&(1<<63) else addr
  status=int(x[3]);valid=0<=addr-offset<depth
  assert status==(0 if valid else 1),(line,depth,offset)
  if not valid:bounds+=1
  if kind=='W':
   if valid:memory[addr]=int(x[2],16)
  else:
   expected=memory.get(addr) if valid else None
   if expected is None:assert x[2].lower()=='xx',line;unknown+=1
   else:assert int(x[2],16)==expected,(line,expected)
 result=dict(state='PASS_INDEPENDENT_MEMORY_EVENT_REPLAY',events=sum(counts.values()),counts=counts,boundary_rejections=bounds,unknown_reads_preserved=unknown,
  alias_pairs=512,tested_storage_widths=[8,32,128],original_int_depth_offset_semantics=True,
  four_state_and_generic_widths='Simulator assertions PASS; byte events independently replayed',
  events_sha256=sha(R/'memory_events.csv'),log_sha256=sha(R/'simulate.log'),
  independent_reviewer_sha256=sha(Path(__file__)),not_full_rtl_qualification=True,automatic_next_stage=False)
 (R/'UNIT_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
