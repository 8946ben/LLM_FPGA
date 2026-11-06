`timescale 1ns/1ps
`include "uvm_macros.svh"
module allocation_tb;
import uvm_pkg::*;import axi_pkg::*;
`include "original_latency.svh"
bit clk=0,rst=0;always #0.5 clk=~clk;
axi_if#(8,4,4,3,1) bus(clk,rst);misc_interface misc(clk,rst);
wire start,interrupt;wire[63:0] meta,tiled,canonical,workspace;
wire[31:0] capacity,debug_mode;
logic done=0,ready=0,idle=1,vld=0;
logic[31:0] status=0,token=0,score=0,crc=0,candidates=0;
logic[63:0] beats=0;
integer cycles=0,reads=0,writes=0,done_cycle=0,done_count=0,mode_global=0;
logic[31:0] last_read=0;integer wirefd;
always @(posedge clk)begin
 cycles++;
 if(rst && bus.ARVALID===1 && bus.ARREADY===1)begin
  if(bus.ARLEN!==0 || bus.ARSIZE!==2)$fatal(1,"AR format");
  $fwrite(wirefd,"AR,%0d,%0d,0\n",cycles,bus.ARADDR);
 end
 if(rst && bus.RVALID===1 && bus.RREADY===1)begin
  if(bus.RRESP!==0 || bus.RLAST!==1)$fatal(1,"R response");
  reads++;last_read=bus.RDATA;$fwrite(wirefd,"R,%0d,0,%0d\n",cycles,bus.RDATA);
 end
 if(rst && bus.AWVALID===1 && bus.AWREADY===1)$fwrite(wirefd,"AW,%0d,%0d,0\n",cycles,bus.AWADDR);
 if(rst && bus.WVALID===1 && bus.WREADY===1)$fwrite(wirefd,"W,%0d,0,%0d\n",cycles,bus.WDATA);
 if(rst && bus.BVALID===1 && bus.BREADY===1)begin
  if(bus.BRESP!==0)$fatal(1,"B response");writes++;$fwrite(wirefd,"B,%0d,0,0\n",cycles);
 end
end
assign bus.RID=0;assign bus.RLAST=1;assign bus.BID=0;
lm_head_v4_partial_proto_control_s_axi dut(
 .ACLK(clk),.ARESET(!rst),.ACLK_EN(1'b1),
 .AWADDR(bus.AWADDR),.AWVALID(bus.AWVALID),.AWREADY(bus.AWREADY),
 .WDATA(bus.WDATA),.WSTRB(bus.WSTRB),.WVALID(bus.WVALID),.WREADY(bus.WREADY),
 .BRESP(bus.BRESP),.BVALID(bus.BVALID),.BREADY(bus.BREADY),
 .ARADDR(bus.ARADDR),.ARVALID(bus.ARVALID),.ARREADY(bus.ARREADY),
 .RDATA(bus.RDATA),.RRESP(bus.RRESP),.RVALID(bus.RVALID),.RREADY(bus.RREADY),
 .interrupt(interrupt),.meta_offset(meta),.tiled_weight(tiled),.canonical_weight(canonical),
 .workspace(workspace),.capacity_beats(capacity),.debug(debug_mode),
 .status(status),.status_ap_vld(vld),.token(token),.token_ap_vld(vld),
 .score_bits(score),.score_bits_ap_vld(vld),.candidate_count(candidates),.candidate_count_ap_vld(vld),
 .output_crc(crc),.output_crc_ap_vld(vld),.preview_read_beats(beats),.preview_read_beats_ap_vld(vld),
 .ap_start(start),.ap_done(done),.ap_ready(ready),.ap_idle(idle));
// Fake bounded compute stimulus. Only the actual frozen control register RTL is tested.
initial begin
 wait(rst);forever begin
  @(posedge clk);
  if(start)begin
   idle=0;
   if(mode_global==2)wait(1'b0);
   if(capacity==0)repeat(3)@(posedge clk);else repeat(20000)@(posedge clk);
   @(negedge clk);
   status=(capacity==0)?1:0;token=(capacity==0)?32'hffffffff:(debug_mode?32'h2345:32'h1234);
   score=(capacity==0)?0:(debug_mode?32'h40000000:32'h3f800000);
   crc=(capacity==0)?0:(debug_mode?32'h22222222:32'h11111111);
   candidates=(capacity==0)?0:(debug_mode?17:11);beats=(capacity==0)?0:64'h100000002;
   vld=1;done=1;ready=1;idle=1;done_cycle=cycles;done_count++;
   $fwrite(wirefd,"DONE,%0d,%0d,%0d\n",cycles,done_count,status);
   @(negedge clk);vld=0;done=0;ready=0;wait(start==0);
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
class control_test extends uvm_test;
 `uvm_component_utils(control_test)
 axi_env#(8,4,4,3,1) env;axi_cfg cfg;axi_latency_control latency;
 virtual misc_interface mif;integer mode,interval,fd,resultfd,total_polls=0;
 function new(string name="control_test",uvm_component parent=null);super.new(name,parent);endfunction
 virtual function void build_phase(uvm_phase phase);
  super.build_phase(phase);if(!$value$plusargs("MODE=%d",mode))mode=0;mode_global=mode;
  if(mode!=0)uvm_factory::get().set_type_override_by_type(axi_state::get_type(),fixed_state::get_type());
  cfg=new("cfg");cfg.set_default();cfg.drv_type=MASTER;latency=new("original_control_latency");cfg.clatency=latency;
  uvm_config_db#(axi_cfg)::set(this,"env","cfg",cfg);env=axi_env#(8,4,4,3,1)::type_id::create("env",this);
  if(!uvm_config_db#(virtual misc_interface)::get(this,"","misc",mif))`uvm_fatal("regression","misc missing")
 endfunction
 task write32(input bit[7:0] addr,input bit[31:0] value);
  axi_busdatas_master_sequence#(8,32) seq;
  seq=axi_busdatas_master_sequence#(8,32)::type_id::create("write_control");
  seq.misc_if=mif;seq.isusr_delay=NO_DELAY;seq.wr_addr_data.push_back({addr,value});seq.start(env.vsqr);
  repeat(3)@(posedge mif.clock);
 endtask
 task read32(input bit[7:0] addr,output logic[31:0] value);
  axi_busdatas_master_sequence#(8,32) seq;integer before_reads;
  before_reads=reads;seq=axi_busdatas_master_sequence#(8,32)::type_id::create("read_control");
  seq.misc_if=mif;seq.isusr_delay=NO_DELAY;seq.rd_addr.push_back(addr);seq.start(env.vsqr);
  repeat(3)@(posedge mif.clock);
  if(reads!=before_reads+1 || env.state.rd_outstanding_cal()!=0)$fatal(1,"read completion");value=last_read;
 endtask
 task sample(input integer call_index);
  integer pf,rc,rss;string line;pf=$fopen("/proc/self/status","r");rss=-1;
  while(!$feof(pf))begin rc=$fgets(line,pf);if($sscanf(line,"VmRSS: %d kB",rss)==1)break;end
  $fclose(pf);if(rss<0)$fatal(1,"RSS missing");
  if(mode!=0 && (env.state.rq_from_model[0].size()!=0 || env.state.rq_from_model_num!=0))$fatal(1,"master retention");
  $fwrite(fd,"%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d\n",mode,call_index,cycles,rss,total_polls,env.state.rq_from_model[0].size(),reads,writes);$fflush(fd);
 endtask
 virtual task run_phase(uvm_phase phase);
  logic[31:0] value,st,tok,sc,cr,lo,hi,cnt;integer start_cycle,polls,detected_cycle;
  bit detected;integer dbg,cap;
  phase.raise_objection(this);wait(mif.reset===1);repeat(3)@(posedge mif.clock);
  fd=$fopen("allocation_samples.csv","w");resultfd=$fopen("results.csv","w");interval=(mode==0)?20:2000;sample(-1);
  for(int call_index=0;call_index<((mode==2)?1:4);call_index++)begin
   dbg=(call_index==1)?1:0;cap=(call_index==2)?0:1024;
   write32(8'h48,dbg);write32(8'h40,cap);read32(8'h48,value);if(value!==dbg)$fatal(1,"debug roundtrip");
   read32(8'h40,value);if(value!==cap)$fatal(1,"capacity roundtrip");
   read32(0,value);if(value[1]!==0)$fatal(1,"stale done before start");
   start_cycle=cycles;write32(0,1);detected=0;polls=0;detected_cycle=0;
   while(!detected && cycles-start_cycle<((mode==2)?10000:26000))begin
    read32(0,value);polls++;total_polls++;
    if(value[1]===1)begin detected=1;detected_cycle=cycles;end
    else repeat(interval)@(posedge mif.clock);
   end
   if(mode==2)begin
    if(detected || done_count!=0)$fatal(1,"false done on timeout");
    $fwrite(resultfd,"%0d,%0d,%0d,0,0,0,0,0,0,%0d,%0d\n",call_index,dbg,cap,cycles,polls);
   end else begin
    if(!detected || done_count!=call_index+1 || detected_cycle<done_cycle || detected_cycle-done_cycle>3000)$fatal(1,"lost or late done");
    read32(8'h50,st);read32(8'h60,tok);read32(8'h70,sc);read32(8'h90,cr);read32(8'ha0,lo);read32(8'ha4,hi);read32(8'h80,cnt);
    if(st!==(cap==0?1:0) || tok!==(cap==0?32'hffffffff:(dbg?32'h2345:32'h1234)))$fatal(1,"status/token");
    if(sc!==(cap==0?0:(dbg?32'h40000000:32'h3f800000)) || cr!==(cap==0?0:(dbg?32'h22222222:32'h11111111)))$fatal(1,"score/crc");
    if({hi,lo}!==(cap==0?64'd0:64'h100000002) || cnt!==(cap==0?0:(dbg?17:11)))$fatal(1,"64bit/count");
    read32(0,value);if(value[1]!==0)$fatal(1,"done clear on read");
    $fwrite(resultfd,"%0d,%0d,%0d,%0d,%0d,%0d,%0d,1,%0d,%0d,%0d\n",call_index,dbg,cap,st,tok,sc,cr,done_cycle,detected_cycle,polls);
   end
   sample(call_index);
  end
  repeat(3)@(posedge mif.clock);sample(4);$fclose(fd);$fclose(resultfd);$fclose(wirefd);
  $display("ALLOCATION_MICRO_PASS actual_control_register_regression mode=%0d polls=%0d calls=%0d",mode,total_polls,done_count);
  phase.drop_objection(this);
 endtask
endclass
initial begin
 wirefd=$fopen("wire_events.csv","w");
 uvm_config_db#(virtual axi_if#(8,4,4,3,1))::set(null,"uvm_test_top.*","vif",bus);
 uvm_config_db#(virtual misc_interface)::set(null,"uvm_test_top","misc",misc);run_test("control_test");
end
initial begin #10;rst=1;end
initial begin #200000;$fatal(1,"bounded simulation watchdog");end
endmodule
