`timescale 1ns/1ps
// DRAFT additional simulation environment; NOT compiled or qualified yet.
// Single-outstanding, registered, no inserted random waits. Not MIG/physical DDR.
// Intended only AFTER the original strong-stress full-RTL gate independently passes.
// Preserve full memory and complete DUT work; never substitute precomputed outputs.
module d64_native_memory #(parameter [63:0] BASE=0,parameter integer N=1,
 parameter integer STORAGE_N=N,parameter bit READ_ONLY=0)(
input clk,rst,
input AWVALID,output AWREADY,input[63:0] AWADDR,input AWID,input[7:0] AWLEN,input[2:0] AWSIZE,input[1:0] AWBURST,
input WVALID,output WREADY,input[127:0] WDATA,input[15:0] WSTRB,input WLAST,
output reg BVALID=0,input BREADY,output reg BID=0,output[1:0] BRESP,
input ARVALID,output ARREADY,input[63:0] ARADDR,input ARID,input[7:0] ARLEN,input[2:0] ARSIZE,input[1:0] ARBURST,
output reg RVALID=0,input RREADY,output reg[127:0] RDATA=0,output reg RLAST=0,output reg RID=0,output[1:0] RRESP
);
// Backing is the independently qualified packed/banked four-state model.
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
reg held_r=0,held_b=0;reg[129:0] prev_r=0;reg prev_bid=0;
reg ractive=0,wactive=0,resp_pending=0;reg rid_saved=0,wid_saved=0;
reg[63:0] ra=0,wa=0;integer rn=0,wn=0,delay_b=0;
integer tick=0,rdbeats=0,wrbeats=0,arstall=0,awstall=0,wstall=0,rgap=0,bdelay=0,boundary=0;
integer idx,b;reg held_ar=0,held_aw=0,held_w=0;reg[77:0] prev_ar=0,prev_aw=0;reg[144:0] prev_w=0;
wire idle=!ractive&&!RVALID&&!wactive&&!resp_pending&&!BVALID;
assign ARREADY=!rst&&initialized&&!ractive&&!RVALID;
assign AWREADY=!rst&&initialized&&!READ_ONLY&&!wactive&&!resp_pending&&!BVALID;
assign WREADY=!rst&&initialized&&!READ_ONLY&&wactive;
assign BRESP=0;assign RRESP=0;
task check_addr(input[63:0] a,input[7:0] len,input[2:0] size,input[1:0] burst);
reg[64:0] ending;
begin
if($isunknown({a,len,size,burst}))$fatal(1,"NATIVE_MODEL_UNKNOWN_ADDRESS_CONTROL");
ending={1'b0,a}+65'd16*({1'b0,len}+1);
if(a<BASE||ending>LOGICAL_END||ending[64]||a[3:0]!=0||size!=4||burst!=1||len>=128)
 $fatal(1,"NATIVE_MODEL_RANGE_REJECT addr=%h len=%0d",a,len);
if({1'b0,a[11:0]}+16*({1'b0,len}+1)>4096)$fatal(1,"AXI crossed4KiB %h len%0d",a,len);
end endtask
always @(posedge clk)begin
if(rst)begin
RVALID<=0;BVALID<=0;ractive<=0;wactive<=0;resp_pending<=0;tick<=0;held_r<=0;held_b<=0;
rdbeats<=0;wrbeats<=0;arstall<=0;awstall<=0;wstall<=0;rgap<=0;bdelay<=0;boundary<=0;held_ar<=0;held_aw<=0;held_w<=0;
end else begin
tick<=tick+1;
if(!initialized || storage==null)$fatal(1,"NATIVE_MODEL_NOT_INITIALIZED");
if(READ_ONLY && (AWVALID===1'b1 || WVALID===1'b1))$fatal(1,"NATIVE_MODEL_READ_ONLY_WRITE");
if(held_r && (RVALID!==1'b1 || {RDATA,RLAST,RID}!==prev_r))$fatal(1,"NATIVE_MODEL_R_UNSTABLE");
if(held_b && (BVALID!==1'b1 || BID!==prev_bid))$fatal(1,"NATIVE_MODEL_B_UNSTABLE");
held_r<=RVALID&&!RREADY;prev_r<={RDATA,RLAST,RID};held_b<=BVALID&&!BREADY;prev_bid<=BID;
if(held_ar&&(!ARVALID||{ARADDR,ARLEN,ARSIZE,ARBURST,ARID}!==prev_ar))$fatal(1,"AR unstable during stall");
if(held_aw&&(!AWVALID||{AWADDR,AWLEN,AWSIZE,AWBURST,AWID}!==prev_aw))$fatal(1,"AW unstable during stall");
if(held_w&&(!WVALID||{WDATA,WSTRB,WLAST}!==prev_w))$fatal(1,"W unstable during stall");
held_ar<=ARVALID&&!ARREADY;held_aw<=AWVALID&&!AWREADY;held_w<=WVALID&&!WREADY;
prev_ar<={ARADDR,ARLEN,ARSIZE,ARBURST,ARID};prev_aw<={AWADDR,AWLEN,AWSIZE,AWBURST,AWID};prev_w<={WDATA,WSTRB,WLAST};
if(ARVALID&&!ARREADY)arstall<=arstall+1;if(AWVALID&&!AWREADY)awstall<=awstall+1;if(WVALID&&!WREADY)wstall<=wstall+1;
if(ARVALID&&ARREADY)begin if($isunknown(ARID))$fatal(1,"NATIVE_MODEL_UNKNOWN_ARID");check_addr(ARADDR,ARLEN,ARSIZE,ARBURST);ractive<=1;ra<=ARADDR;rn<=ARLEN+1;rid_saved<=ARID;if(ARADDR[11:0]==0)boundary<=boundary+1;end
if(RVALID&&RREADY)begin RVALID<=0;rdbeats<=rdbeats+1;end
if(ractive&&(!RVALID||RREADY))begin
begin
storage_error=storage.read_packed16(read_word,ra-BASE);
if(storage_error)$fatal(1,"NATIVE_MODEL_BACKING_READ_REJECT");
RDATA<=read_word;RID<=rid_saved;RLAST<=(rn==1);RVALID<=1;ra<=ra+16;rn<=rn-1;if(rn==1)ractive<=0;
end
end
if(AWVALID&&AWREADY)begin if($isunknown(AWID))$fatal(1,"NATIVE_MODEL_UNKNOWN_AWID");check_addr(AWADDR,AWLEN,AWSIZE,AWBURST);wactive<=1;wa<=AWADDR;wn<=AWLEN+1;wid_saved<=AWID;end
if(WVALID&&WREADY)begin
if(WLAST!==(wn==1))$fatal(1,"WLAST mismatch");idx=(wa-BASE)>>4;
if($isunknown(WSTRB))$fatal(1,"NATIVE_MODEL_UNKNOWN_WSTRB");
if(WSTRB==16'hffff)begin
 storage_error=storage.write_packed16(WDATA,wa-BASE);
 if(storage_error)$fatal(1,"NATIVE_MODEL_BACKING_WRITE_REJECT");
end else begin
 // A masked write must not mark untouched, uninitialized byte lanes as valid.
 for(b=0;b<16;b=b+1)if(WSTRB[b])begin
  storage_error=storage.write_one_elem(WDATA[b*8+:8],wa-BASE+b);
  if(storage_error)$fatal(1,"NATIVE_MODEL_BACKING_MASKED_WRITE_REJECT");
 end
end
wa<=wa+16;wn<=wn-1;wrbeats<=wrbeats+1;
if(wn==1)begin wactive<=0;resp_pending<=1;delay_b<=0;end
end
if(resp_pending)begin
if(delay_b==0&&!BVALID)begin BVALID<=1;BID<=wid_saved;resp_pending<=0;end else begin delay_b<=delay_b-1;bdelay<=bdelay+1;end
end
if(BVALID&&BREADY)BVALID<=0;
end
end
endmodule
