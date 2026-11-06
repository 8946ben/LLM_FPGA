`timescale 1ns/1ps
// Test model: one bounded read and one bounded write; legal deterministic stalls.
// NOT a MIG, physical DDR model, or bandwidth benchmark.
module axi_stall_memory #(parameter [63:0] BASE=0,parameter N=1)(
input clk,rst,
input AWVALID,output AWREADY,input[63:0] AWADDR,input AWID,input[7:0] AWLEN,input[2:0] AWSIZE,input[1:0] AWBURST,
input WVALID,output WREADY,input[127:0] WDATA,input[15:0] WSTRB,input WLAST,
output reg BVALID=0,input BREADY,output reg BID=0,output[1:0] BRESP,
input ARVALID,output ARREADY,input[63:0] ARADDR,input ARID,input[7:0] ARLEN,input[2:0] ARSIZE,input[1:0] ARBURST,
output reg RVALID=0,input RREADY,output reg[127:0] RDATA=0,output reg RLAST=0,output reg RID=0,output[1:0] RRESP
);
reg[127:0] data[0:N-1];reg[31:0] lfsr=32'h1a2b3c4d;
reg ractive=0,wactive=0,resp_pending=0;reg rid_saved=0,wid_saved=0;
reg[63:0] ra=0,wa=0;integer rn=0,wn=0,delay_b=0;
integer tick=0,rdbeats=0,wrbeats=0,arstall=0,awstall=0,wstall=0,rgap=0,bdelay=0,boundary=0;
integer idx,b;reg held_ar=0,held_aw=0,held_w=0;reg[77:0] prev_ar=0,prev_aw=0;reg[144:0] prev_w=0;
wire long_pause=(tick%32768)<700;
assign ARREADY=!rst&&!ractive&&!RVALID&&lfsr[0]&&lfsr[2]&&!long_pause;
assign AWREADY=!rst&&!wactive&&!resp_pending&&!BVALID&&lfsr[3]&&!long_pause;
assign WREADY=!rst&&wactive&&lfsr[4]&&lfsr[7]&&!long_pause;
assign BRESP=0;assign RRESP=0;
task check_addr(input[63:0] a,input[7:0] len,input[2:0] size,input[1:0] burst);
begin
if(a<BASE||a+16*({1'b0,len}+1)>BASE+16*N||a[3:0]!=0||size!=4||burst!=1||len>=128)$fatal(1,"AXI address/size/burst %h len%0d",a,len);
if({1'b0,a[11:0]}+16*({1'b0,len}+1)>4096)$fatal(1,"AXI crossed4KiB %h len%0d",a,len);
end endtask
always @(posedge clk)begin
if(rst)begin
RVALID<=0;BVALID<=0;ractive<=0;wactive<=0;resp_pending<=0;tick<=0;lfsr<=32'h1a2b3c4d;
rdbeats<=0;wrbeats<=0;arstall<=0;awstall<=0;wstall<=0;rgap<=0;bdelay<=0;boundary<=0;held_ar<=0;held_aw<=0;held_w<=0;
end else begin
tick<=tick+1;lfsr<={lfsr[30:0],lfsr[31]^lfsr[21]^lfsr[1]^lfsr[0]};
if(held_ar&&(!ARVALID||{ARADDR,ARLEN,ARSIZE,ARBURST,ARID}!==prev_ar))$fatal(1,"AR unstable during stall");
if(held_aw&&(!AWVALID||{AWADDR,AWLEN,AWSIZE,AWBURST,AWID}!==prev_aw))$fatal(1,"AW unstable during stall");
if(held_w&&(!WVALID||{WDATA,WSTRB,WLAST}!==prev_w))$fatal(1,"W unstable during stall");
held_ar<=ARVALID&&!ARREADY;held_aw<=AWVALID&&!AWREADY;held_w<=WVALID&&!WREADY;
prev_ar<={ARADDR,ARLEN,ARSIZE,ARBURST,ARID};prev_aw<={AWADDR,AWLEN,AWSIZE,AWBURST,AWID};prev_w<={WDATA,WSTRB,WLAST};
if(ARVALID&&!ARREADY)arstall<=arstall+1;if(AWVALID&&!AWREADY)awstall<=awstall+1;if(WVALID&&!WREADY)wstall<=wstall+1;
if(ARVALID&&ARREADY)begin check_addr(ARADDR,ARLEN,ARSIZE,ARBURST);ractive<=1;ra<=ARADDR;rn<=ARLEN+1;rid_saved<=ARID;if(ARADDR[11:0]==0)boundary<=boundary+1;end
if(RVALID&&RREADY)begin RVALID<=0;rdbeats<=rdbeats+1;end
if(ractive&&(!RVALID||RREADY))begin
if(lfsr[5]&&!long_pause)begin
idx=(ra-BASE)>>4;RDATA<=data[idx];RID<=rid_saved;RLAST<=(rn==1);RVALID<=1;ra<=ra+16;rn<=rn-1;if(rn==1)ractive<=0;
end else rgap<=rgap+1;
end
if(AWVALID&&AWREADY)begin check_addr(AWADDR,AWLEN,AWSIZE,AWBURST);wactive<=1;wa<=AWADDR;wn<=AWLEN+1;wid_saved<=AWID;end
if(WVALID&&WREADY)begin
if(WLAST!==(wn==1))$fatal(1,"WLAST mismatch");idx=(wa-BASE)>>4;
for(b=0;b<16;b=b+1)if(WSTRB[b])data[idx][b*8+:8]<=WDATA[b*8+:8];
wa<=wa+16;wn<=wn-1;wrbeats<=wrbeats+1;
if(wn==1)begin wactive<=0;resp_pending<=1;delay_b<=11;end
end
if(resp_pending)begin
if(delay_b==0&&!BVALID)begin BVALID<=1;BID<=wid_saved;resp_pending<=0;end else begin delay_b<=delay_b-1;bdelay<=bdelay+1;end
end
if(BVALID&&BREADY)BVALID<=0;
end
end
endmodule
