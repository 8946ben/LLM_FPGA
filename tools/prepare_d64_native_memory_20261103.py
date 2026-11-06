"""Draft an additional normal-response AXI model. No EDA or remote execution."""
from pathlib import Path
import hashlib,json,datetime,shutil
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';NAME='d64_native_memory_20261103_r1'
E=M/'experiments'/NAME;R=M/'reports'/NAME
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 E.mkdir();R.mkdir();source=M/'experiments/partial_rtl_20261024/axi_stall_memory.sv';text=source.read_text();original=text;edits=[]
 selector=M/'reports/partial_rtl_20261024_r1/r4/PLAN.json';p=json.loads(selector.read_text())
 key=str(source.relative_to(ROOT)).replace('\\','/');assert p['source_sha256'][key]==sha(source)
 def edit(before,after):
  nonlocal text
  assert text.count(before)==1,before[:90];text=text.replace(before,after);edits.append([before,after])
 edit('// Test model: one bounded read and one bounded write; legal deterministic stalls.\n// NOT a MIG, physical DDR model, or bandwidth benchmark.',
 '''// DRAFT additional simulation environment; NOT compiled or qualified yet.
// Single-outstanding, registered, no inserted random waits. Not MIG/physical DDR.
// Intended only AFTER the original strong-stress full-RTL gate independently passes.
// Preserve full memory and complete DUT work; never substitute precomputed outputs.''')
 edit('module axi_stall_memory #(parameter [63:0] BASE=0,parameter N=1)(',
 '''module d64_native_memory #(parameter [63:0] BASE=0,parameter integer N=1,
 parameter integer STORAGE_N=N,parameter bit READ_ONLY=0)(''')
 edit("reg[127:0] data[0:N-1];reg[31:0] lfsr=32'h1a2b3c4d;",'''// Backing is the independently qualified packed/banked four-state model.
file_agent_pkg::mem_model#(8) storage;
bit initialized=0;
localparam logic[64:0] LOGICAL_END={1'b0,BASE}+65'd16*N;
initial begin
 if(N<=0 || STORAGE_N<N || 64'd16*STORAGE_N>64'd2147483647 || LOGICAL_END[64])
  $fatal(1,"NATIVE_MODEL_INVALID_CAPACITY");
 storage=new("native_memory_storage");storage.init(STORAGE_N*16,0);initialized=1;
end
integer storage_error;
logic[127:0] read_word;
reg held_r=0,held_b=0;reg[129:0] prev_r=0;reg prev_bid=0;''')
 edit('wire long_pause=(tick%32768)<700;', 'wire idle=!ractive&&!RVALID&&!wactive&&!resp_pending&&!BVALID;')
 edit('assign ARREADY=!rst&&!ractive&&!RVALID&&lfsr[0]&&lfsr[2]&&!long_pause;', 'assign ARREADY=!rst&&initialized&&!ractive&&!RVALID;')
 edit('assign AWREADY=!rst&&!wactive&&!resp_pending&&!BVALID&&lfsr[3]&&!long_pause;', 'assign AWREADY=!rst&&initialized&&!READ_ONLY&&!wactive&&!resp_pending&&!BVALID;')
 edit('assign WREADY=!rst&&wactive&&lfsr[4]&&lfsr[7]&&!long_pause;', 'assign WREADY=!rst&&initialized&&!READ_ONLY&&wactive;')
 edit('''begin
if(a<BASE||a+16*({1'b0,len}+1)>BASE+16*N||a[3:0]!=0||size!=4||burst!=1||len>=128)$fatal(1,"AXI address/size/burst %h len%0d",a,len);''', '''reg[64:0] ending;
begin
if($isunknown({a,len,size,burst}))$fatal(1,"NATIVE_MODEL_UNKNOWN_ADDRESS_CONTROL");
ending={1'b0,a}+65'd16*({1'b0,len}+1);
if(a<BASE||ending>LOGICAL_END||ending[64]||a[3:0]!=0||size!=4||burst!=1||len>=128)
 $fatal(1,"NATIVE_MODEL_RANGE_REJECT addr=%h len=%0d",a,len);''')
 edit("RVALID<=0;BVALID<=0;ractive<=0;wactive<=0;resp_pending<=0;tick<=0;lfsr<=32'h1a2b3c4d;", 'RVALID<=0;BVALID<=0;ractive<=0;wactive<=0;resp_pending<=0;tick<=0;held_r<=0;held_b<=0;')
 edit("tick<=tick+1;lfsr<={lfsr[30:0],lfsr[31]^lfsr[21]^lfsr[1]^lfsr[0]};", '''tick<=tick+1;
if(!initialized || storage==null)$fatal(1,"NATIVE_MODEL_NOT_INITIALIZED");
if(READ_ONLY && (AWVALID===1'b1 || WVALID===1'b1))$fatal(1,"NATIVE_MODEL_READ_ONLY_WRITE");
if(held_r && (RVALID!==1'b1 || {RDATA,RLAST,RID}!==prev_r))$fatal(1,"NATIVE_MODEL_R_UNSTABLE");
if(held_b && (BVALID!==1'b1 || BID!==prev_bid))$fatal(1,"NATIVE_MODEL_B_UNSTABLE");
held_r<=RVALID&&!RREADY;prev_r<={RDATA,RLAST,RID};held_b<=BVALID&&!BREADY;prev_bid<=BID;''')
 edit('if(ARVALID&&ARREADY)begin check_addr(ARADDR,ARLEN,ARSIZE,ARBURST);', 'if(ARVALID&&ARREADY)begin if($isunknown(ARID))$fatal(1,"NATIVE_MODEL_UNKNOWN_ARID");check_addr(ARADDR,ARLEN,ARSIZE,ARBURST);')
 edit('''if(lfsr[5]&&!long_pause)begin
idx=(ra-BASE)>>4;RDATA<=data[idx];RID<=rid_saved;RLAST<=(rn==1);RVALID<=1;ra<=ra+16;rn<=rn-1;if(rn==1)ractive<=0;
end else rgap<=rgap+1;''', '''begin
storage_error=storage.read_packed16(read_word,ra-BASE);
if(storage_error)$fatal(1,"NATIVE_MODEL_BACKING_READ_REJECT");
RDATA<=read_word;RID<=rid_saved;RLAST<=(rn==1);RVALID<=1;ra<=ra+16;rn<=rn-1;if(rn==1)ractive<=0;
end''')
 edit('if(AWVALID&&AWREADY)begin check_addr(AWADDR,AWLEN,AWSIZE,AWBURST);', 'if(AWVALID&&AWREADY)begin if($isunknown(AWID))$fatal(1,"NATIVE_MODEL_UNKNOWN_AWID");check_addr(AWADDR,AWLEN,AWSIZE,AWBURST);')
 edit('for(b=0;b<16;b=b+1)if(WSTRB[b])data[idx][b*8+:8]<=WDATA[b*8+:8];', '''if($isunknown(WSTRB))$fatal(1,"NATIVE_MODEL_UNKNOWN_WSTRB");
if(WSTRB==16'hffff)begin
 storage_error=storage.write_packed16(WDATA,wa-BASE);
 if(storage_error)$fatal(1,"NATIVE_MODEL_BACKING_WRITE_REJECT");
end else begin
 // A masked write must not mark untouched, uninitialized byte lanes as valid.
 for(b=0;b<16;b=b+1)if(WSTRB[b])begin
  storage_error=storage.write_one_elem(WDATA[b*8+:8],wa-BASE+b);
  if(storage_error)$fatal(1,"NATIVE_MODEL_BACKING_MASKED_WRITE_REJECT");
 end
end''')
 edit('delay_b<=11;', 'delay_b<=0;')
 # Exact reversal records every change from the previously used small AXI model.
 restored=text
 for before,after in reversed(edits):assert restored.count(after)==1;restored=restored.replace(after,before)
 assert restored==original and 'lfsr' not in text and 'data[idx]' not in text
 (E/'d64_native_memory.sv').write_text(text)
 backing=M/'experiments/memory_burst_model_20261103_r3/mem_model.sv';assert sha(backing)=='07e2f1b17f10b989bdb980cc208c463c914170c14fc598851f71aeba21e74c40'
 (E/'CHANGES.json').write_text(json.dumps(dict(original_path=key,original_sha256=sha(source),candidate_sha256=sha(E/'d64_native_memory.sv'),edits=edits),indent=2)+'\n')
 requirements=['Positive read/write and masked writes with strict host replay of every beat','R and B held stable under prolonged backpressure; master AR/AW/W stability checks','First/last legal beat,1MiB bank edge,512MiB separation and logical end guard','Explicit rejection controls: bounds/high address/4KiB/alignment/len/size/burst/X address/X strobe/read-only write','No response before an accepted request; ID/RLAST/WLAST ordering and quiescence','Reset cancels outstanding bus state without clearing storage; no reset between eventual M14 scenarios','Confirm actual bounded RSS over repeated fixed-capacity traffic and actual compiled source SHA','Only after this model gate passes may full persistent-DUT11-scenario test use it']
 out=dict(state='DRAFT_NATIVE_MEMORY_NOT_COMPILED_OR_QUALIFIED',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate_sha256=sha(E/'d64_native_memory.sv'),backing_model_sha256=sha(backing),original_model_sha256=sha(source),original_selector_plan_sha256=sha(selector),
  changes_reversible=True,explicit_scope='Additional normal-response simulation only. Current strong-random-delay full RTL must finish and pass independently; this draft is never a replacement.',
  response_contract=dict(data_bits=128,read_outstanding=1,write_outstanding=1,random_waits=False,registered_read_and_b_response=True,read_rate='One beat per cycle inside a burst if ready; address/response transitions still cost cycles',physical_DDR_model=False),
  must_qualify=requirements,current_execution='memory_repaired_full_20261103_r1 remains sole EDA job',eda='NOT_RUN',board='NOT_RUN',automatic_next_stage=False)
 (R/'PREPARATION.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='must_qualify'},indent=2))
if __name__=='__main__':main()
