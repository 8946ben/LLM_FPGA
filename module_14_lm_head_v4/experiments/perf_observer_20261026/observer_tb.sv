`timescale 1ns/1ps
module observer_tb;
reg clk=0;always #2.5 clk=~clk;
reg rst_n=0,top_start=0,top_done=1,top_idle=1;
reg[4:0]st_start=0,st_done=31,st_idle=31;
reg w_arvalid=0,w_arready=0,w_rvalid=0,w_rready=0;
reg m_arvalid=0,m_arready=0,m_rvalid=0,m_rready=0;
reg m_awvalid=0,m_awready=0,m_wvalid=0,m_wready=0;
reg[31:0]status=0;
lmh_stage_observer probe(.*);
initial begin
 repeat(2)@(negedge clk);rst_n=1;
 @(negedge clk);top_start=1;st_start[0]=1;
 // Two cycles of idle-high done must not complete either timer.
 repeat(2)@(negedge clk);top_idle=0;top_done=0;st_idle[0]=0;st_done[0]=0;w_arvalid=1;
 repeat(3)@(negedge clk);w_arready=1;w_rvalid=1;w_rready=1;m_rvalid=1;m_rready=1;m_wvalid=1;m_wready=1;
 @(negedge clk);st_done[0]=1;
 @(negedge clk);st_start[0]=0;st_idle[0]=1;w_arvalid=0;w_rvalid=0;m_rvalid=0;m_wvalid=0;
 @(negedge clk);top_done=1;
 @(negedge clk);top_start=0;top_idle=1;
 repeat(2)@(negedge clk);top_start=1;st_start[3]=1;
 @(negedge clk);top_idle=0;top_done=0;st_idle[3]=0;st_done[3]=0;w_rvalid=1;
 @(negedge clk);
 @(negedge clk);w_rvalid=0;st_done[3]=1;
 @(negedge clk);st_start[3]=0;st_idle[3]=1;
 @(negedge clk);top_done=1;
 @(negedge clk);top_start=0;top_idle=1;
 repeat(2)@(negedge clk);top_start=1;
 @(negedge clk);top_idle=0;top_done=0;status=1;
 @(negedge clk);top_done=1;
 @(negedge clk);top_start=0;top_idle=1;
 repeat(2)@(negedge clk);
 $display("OBSERVER_STIMULUS_DONE idle_high=2 calls=3 error_call=1");$finish;
end
endmodule
