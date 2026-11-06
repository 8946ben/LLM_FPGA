`timescale 1ns/1ps
module lmh_memory_prefix(input wire clk,rst_n,start,done,idle,
 input wire carvalid,carready,crvalid,crready,warvalid,warready,m_arvalid,m_arready);
 bit begun=0;integer clocks=0,control_ar=0,control_r=0,weight_ar=0,meta_ar=0;
 initial lmh_memory_probe_pkg::sample("top_initial",0);
 always @(posedge clk)begin
  if(rst_n)begin
   if(carvalid && carready)control_ar++;
   if(crvalid && crready)control_r++;
   if(warvalid && warready)weight_ar++;
   if(m_arvalid && m_arready)meta_ar++;
   if(!begun && start===1)begin begun=1;clocks=0;lmh_memory_probe_pkg::sample("dut_start",0);end
   else if(begun)begin
    clocks++;
    if(done===1 || idle===1)$fatal(1,"unexpected complete/idle within bounded prefix");
    if(clocks%5000==0)lmh_memory_probe_pkg::sample("running_prefix",clocks);
    if(clocks==20000)begin
     $display("MEMORY_PREFIX_PASS cycles=%0d control_ar=%0d control_r=%0d master_guard_ar=%0d weight_ar=%0d meta_ar=%0d",clocks,control_ar,control_r,lmh_memory_probe_pkg::master_ar_seen,weight_ar,meta_ar);
     $finish;
    end
   end
  end
 end
 initial begin #1000000;$fatal(1,"prefix simulation watchdog");end
endmodule
bind lm_head_v4_partial_proto lmh_memory_prefix memory_prefix_observer(
 .clk(ap_clk),.rst_n(ap_rst_n),.start(ap_start),.done(ap_done),.idle(ap_idle),
 .carvalid(s_axi_control_ARVALID),.carready(s_axi_control_ARREADY),.crvalid(s_axi_control_RVALID),.crready(s_axi_control_RREADY),
 .warvalid(m_axi_weights_ARVALID),.warready(m_axi_weights_ARREADY),.m_arvalid(m_axi_meta_ARVALID),.m_arready(m_axi_meta_ARREADY));
