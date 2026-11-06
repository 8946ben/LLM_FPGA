`timescale 1ns/1ps
`include "uvm_macros.svh"
module allocation_tb;
import uvm_pkg::*;import axi_pkg::*;
bit clk=0,rst=0;always #0.5 clk=~clk;
axi_if#(8,4,8,3,1) bus(clk,rst);misc_interface misc(clk,rst);
integer busfd,ar_count=0,r_count=0,cycles=0;
always @(posedge clk)begin
 cycles++;
 if(!rst)bus.RVALID<=0;
 else begin
  if(bus.ARVALID===1 && bus.ARREADY===1)begin
   if(bus.ARADDR!==0 || bus.ARLEN!==0 || bus.ARSIZE!==2)$fatal(1,"status AR format");
   ar_count++;$fwrite(busfd,"A,%0d,%0d,%0d\n",cycles,ar_count,bus.ARADDR);bus.RVALID<=1;
  end
  if(bus.RVALID===1 && bus.RREADY===1)begin
   if(bus.RDATA!==0 || bus.RRESP!==0 || bus.RLAST!==1)$fatal(1,"status R bits");
   r_count++;$fwrite(busfd,"R,%0d,%0d,%0d\n",cycles,r_count,bus.RDATA);bus.RVALID<=0;
  end
 end
end
class fixed_state extends axi_state;
 `uvm_component_utils(fixed_state)
 function new(string name,uvm_component parent);super.new(name,parent);endfunction
 virtual function void write_ar(axi_transfer tr);
  if(cfg.drv_type==SLAVE)super.write_ar(tr);
  else begin tr.ainfo_rx=1;tr.expected_read_latency=cfg.clatency.get_rd_lat();arq[tr.id].push_back(tr);end
 endfunction
endclass
class poll_test extends uvm_test;
 `uvm_component_utils(poll_test)
 axi_env#(8,4,8,3,1) env;axi_cfg cfg;virtual misc_interface mif;
 integer mode,n,fd,polls,interval;longint unsigned checksum;
 function new(string name="poll_test",uvm_component parent=null);super.new(name,parent);endfunction
 virtual function void build_phase(uvm_phase phase);
  super.build_phase(phase);
  if(!$value$plusargs("MODE=%d",mode))mode=0;
  if(!$value$plusargs("N=%d",n))n=200000;
  if(mode==2)uvm_factory::get().set_type_override_by_type(axi_state::get_type(),fixed_state::get_type());
  cfg=new("cfg");cfg.set_default();cfg.drv_type=MASTER;
  uvm_config_db#(axi_cfg)::set(this,"env","cfg",cfg);
  env=axi_env#(8,4,8,3,1)::type_id::create("env",this);
  if(!uvm_config_db#(virtual misc_interface)::get(this,"","misc",mif))`uvm_fatal("probe","misc missing")
 endfunction
 task sample();
  integer pf,rc,rss;string line;
  pf=$fopen("/proc/self/status","r");rss=-1;
  while(!$feof(pf))begin rc=$fgets(line,pf);if($sscanf(line,"VmRSS: %d kB",rss)==1)break;end
  $fclose(pf);if(rss<0)$fatal(1,"RSS read");
  $fwrite(fd,"%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d\n",mode,cycles,polls,rss,env.state.rq_from_model[0].size(),ar_count,r_count,env.state.rd_outstanding_cal());$fflush(fd);
  $display("POLL_SAMPLE mode=%0d cycle=%0d polls=%0d rss_kib=%0d model_q=%0d",mode,cycles,polls,rss,env.state.rq_from_model[0].size());
 endtask
 virtual task run_phase(uvm_phase phase);
  axi_busdatas_master_sequence#(8,32) seq;integer next_sample;
  phase.raise_objection(this);wait(mif.reset===1);repeat(3)@(posedge mif.clock);
  fd=$fopen("allocation_samples.csv","w");polls=0;interval=(mode==1)?2000:20;sample();next_sample=n/4;
  while(cycles<n)begin
   seq=axi_busdatas_master_sequence#(8,32)::type_id::create("poll_control");
   seq.isusr_delay=NO_DELAY;seq.misc_if=mif;seq.rd_addr.push_back(0);seq.start(env.vsqr);seq=null;polls++;
   if(env.state.rd_outstanding_cal()!=0)$fatal(1,"poll read not complete");
   repeat(interval)@(posedge mif.clock);
   if(cycles>=next_sample)begin sample();next_sample+=n/4;end
  end
  repeat(3)@(posedge mif.clock);sample();$fclose(fd);$fflush(busfd);
  if(ar_count!=polls || r_count!=polls)$fatal(1,"wire request count mismatch");
  if(mode<2 && env.state.rq_from_model[0].size()!=polls)$fatal(1,"retention absent");
  if(mode==2 && env.state.rq_from_model[0].size()!=0)$fatal(1,"fixed retained");
  $display("ALLOCATION_MICRO_PASS real_control_poll mode=%0d cycles=%0d polls=%0d interval=%0d",mode,cycles,polls,interval);
  phase.drop_objection(this);
 endtask
endclass
initial begin
 busfd=$fopen("wire_events.csv","w");if(!busfd)$fatal(1,"wire events open");
 bus.ARREADY=1;bus.RVALID=0;bus.RID=0;bus.RDATA=0;bus.RRESP=0;bus.RLAST=1;
 bus.AWREADY=1;bus.WREADY=1;bus.BVALID=0;bus.BID=0;bus.BRESP=0;
 uvm_config_db#(virtual axi_if#(8,4,8,3,1))::set(null,"uvm_test_top.*","vif",bus);
 uvm_config_db#(virtual misc_interface)::set(null,"uvm_test_top","misc",misc);
 run_test("poll_test");
end
initial begin #10;rst=1;end
endmodule
