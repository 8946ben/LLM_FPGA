`timescale 1ns/1ps
// Passive bounds observer for this zero-based generated CoSim memory map.
module lmh_range_observer(
 input clk,rst_n,
 input m_arvalid,m_arready,m_awvalid,m_awready,w_arvalid,w_arready,w_awvalid,w_awready,
 input [63:0] m_araddr,m_awaddr,w_araddr,w_awaddr,
 input [7:0] m_arlen,m_awlen,w_arlen,w_awlen,
 input [2:0] m_arsize,m_awsize,w_arsize,w_awsize,
 input [1:0] m_arburst,m_awburst,w_arburst,w_awburst
);
longint unsigned mr=0,mw=0,wr=0;
task check(input[63:0]address,input[7:0]len,input[2:0]size,input[1:0]burst,input[64:0]limit);
reg[64:0] ending;
begin
 if($isunknown({address,len,size,burst}))$fatal(1,"RANGE_OBSERVER_REJECT unknown address/control");
 ending={1'b0,address}+65'd16*({1'b0,len}+1);
 if(address[3:0]!=0||size!=4||burst!=1||len>=128||ending>limit)$fatal(1,"RANGE_OBSERVER_REJECT bounds/alignment addr=%h len=%0d",address,len);
 if({1'b0,address[11:0]}+16*({1'b0,len}+1)>4096)$fatal(1,"RANGE_OBSERVER_REJECT 4KiB addr=%h len=%0d",address,len);
end endtask
always @(posedge clk)if(rst_n)begin
 if(m_arvalid&&m_arready)begin check(m_araddr,m_arlen,m_arsize,m_arburst,65'd1289456);mr=mr+1;end
 if(m_awvalid&&m_awready)begin check(m_awaddr,m_awlen,m_awsize,m_awburst,65'd1289456);mw=mw+1;end
 if(w_arvalid&&w_arready)begin check(w_araddr,w_arlen,w_arsize,w_arburst,65'd545685504);wr=wr+1;end
 if(w_awvalid&&w_awready)$fatal(1,"RANGE_OBSERVER_REJECT immutable weights write addr=%h",w_awaddr);
end
final $display("LMH_RANGE_GUARD_SUMMARY meta_read_bursts=%0d meta_write_bursts=%0d weight_read_bursts=%0d",mr,mw,wr);
endmodule
