`timescale 1ns/1ps
module range_tb;
reg clk=0;always #2.5 clk=~clk;
reg rst_n=0,m_arvalid=0,m_arready=1,m_awvalid=0,m_awready=1,w_arvalid=0,w_arready=1,w_awvalid=0,w_awready=1;
reg[63:0]m_araddr=0,m_awaddr=0,w_araddr=0,w_awaddr=0;
reg[7:0]m_arlen=0,m_awlen=0,w_arlen=0,w_awlen=0;
reg[2:0]m_arsize=4,m_awsize=4,w_arsize=4,w_awsize=4;
reg[1:0]m_arburst=1,m_awburst=1,w_arburst=1,w_awburst=1;
integer mode=0;
lmh_range_observer probe(.*);
initial begin
 if(!$value$plusargs("MODE=%d",mode))mode=0;
 repeat(2)@(negedge clk);rst_n=1;
 @(negedge clk);
 if(mode==0)begin
  m_arvalid=1;m_araddr=0;
  @(negedge clk);m_araddr=1289440;m_awvalid=1;m_awaddr=1289440;w_arvalid=1;w_araddr=536870896;
  @(negedge clk);m_arvalid=0;m_awvalid=0;w_araddr=536870912;
  @(negedge clk);w_araddr=545685488;
  @(negedge clk);w_arvalid=0;
 end else begin
  case(mode)
   1:begin w_arvalid=1;w_araddr=64'h100000000;end
   2:begin m_awvalid=1;m_awaddr=1289456;end
   3:begin w_arvalid=1;w_araddr=4080;w_arlen=1;end
   4:begin w_awvalid=1;end
   5:begin w_arvalid=1;w_araddr=64'hfffffffffffffff0;w_arlen=1;end
   6:begin w_arvalid=1;w_araddr=64'hx;end
  endcase
 end
 repeat(3)@(negedge clk);$display("RANGE_UNIT_DONE mode=%0d",mode);$finish;
end
endmodule
