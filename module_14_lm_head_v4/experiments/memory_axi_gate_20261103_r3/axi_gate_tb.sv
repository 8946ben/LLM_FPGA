`timescale 1ns/1ps
`include "uvm_macros.svh"
module axi_gate_tb;
import uvm_pkg::*;import axi_pkg::*;
`include "original_latency.svh"
bit clk=0,rst=0;always #2.5 clk=~clk;
axi_if#(64,16,8,3,1) bus(clk,rst);misc_interface misc(clk,rst);
integer cycles=0,fd,ar_count=0,r_count=0,aw_count=0,w_count=0,b_count=0;
integer r_stalls=0,ar_stalls=0,w_stalls=0;
logic[127:0] patterns[16],changed[32];
always @(posedge clk)begin
 cycles++;
 if(rst)begin
  if(bus.ARVALID===1 && bus.ARREADY===1)begin ar_count++;$fwrite(fd,"AR,%0d,%0d,%0d,%0d\n",cycles,ar_count,bus.ARADDR,bus.ARLEN);end
  if(bus.RVALID===1 && bus.RREADY===1)begin r_count++;$fwrite(fd,"R,%0d,%0d,%032h,%0d\n",cycles,r_count,bus.RDATA,bus.RLAST);end
  if(bus.AWVALID===1 && bus.AWREADY===1)begin aw_count++;$fwrite(fd,"AW,%0d,%0d,%0d,%0d\n",cycles,aw_count,bus.AWADDR,bus.AWLEN);end
  if(bus.WVALID===1 && bus.WREADY===1)begin w_count++;$fwrite(fd,"W,%0d,%0d,%032h,%04h,%0d\n",cycles,w_count,bus.WDATA,bus.WSTRB,bus.WLAST);end
  if(bus.BVALID===1 && bus.BREADY===1)begin b_count++;$fwrite(fd,"B,%0d,%0d,%0d\n",cycles,b_count,bus.BRESP);end
  if(bus.RVALID===1 && bus.RREADY===0)r_stalls++;
  if(bus.ARVALID===1 && bus.ARREADY===0)ar_stalls++;
  if(bus.WVALID===1 && bus.WREADY===0)w_stalls++;
 end
end
always @(negedge clk)if(rst)begin bus.RREADY=(cycles%11>=4);bus.BREADY=(cycles%13>=3);end
class model_callback extends axi_state_cbs;
 file_agent_pkg::mem_model_pages_with_diffofst#(128,8) model;
 integer callbacks=0;
 virtual function void memmodel_read_fromar(ref logic[7:0] data[$],input longint addr,input longint len);
  model.read_elems_pipepage(data,addr,len);callbacks++;
 endfunction
endclass
class write_receiver extends uvm_component;
 `uvm_component_utils(write_receiver)
 uvm_analysis_imp#(axi_transfer,write_receiver) imp;
 file_agent_pkg::mem_model_pages_with_diffofst#(128,8) model;
 integer callbacks=0;
 function new(string name,uvm_component parent);super.new(name,parent);imp=new("imp",this);endfunction
 virtual function void write(axi_transfer tr);
  model.write_elems_pipepage(tr.data,tr.byte_addr);callbacks++;
 endfunction
endclass
class gate_test extends uvm_test;
 `uvm_component_utils(gate_test)
 axi_env#(64,16,8,3,1) env;axi_cfg cfg;axi_latency_weights latency;
 file_agent_pkg::mem_model_pages_with_diffofst#(128,8) model;
 model_callback cb;write_receiver wr;
 integer samples,issued,completed,samplefd;
 function new(string name="gate_test",uvm_component parent=null);super.new(name,parent);endfunction
 virtual function void build_phase(uvm_phase phase);
  super.build_phase(phase);cfg=new("cfg");cfg.set_default();cfg.drv_type=SLAVE;latency=new("original_weights_latency");cfg.clatency=latency;
  uvm_config_db#(axi_cfg)::set(this,"env","cfg",cfg);env=axi_env#(64,16,8,3,1)::type_id::create("env",this);
  model=new("memory");cb=new();cb.model=model;wr=write_receiver::type_id::create("wr",this);wr.model=model;
 endfunction
 virtual function void connect_phase(uvm_phase phase);
  super.connect_phase(phase);uvm_callbacks#(axi_state,axi_state_cbs)::add(env.state,cb);env.state.item_wtr_port.connect(wr.imp);
 endfunction
 task sample(input integer epoch);
  integer pf,rc,rss;string line;
  repeat(4)@(posedge clk);#0.1;
  if(env.state.rd_outstanding_cal()!=0 || env.state.wr_outstanding_cal()!=0 || env.state.rq_from_model_num!=0 || env.state.rq_from_model[0].size()!=0)$fatal(1,"residual transactions");
  pf=$fopen("/proc/self/status","r");rss=-1;
  while(!$feof(pf))begin rc=$fgets(line,pf);if($sscanf(line,"VmRSS: %d kB",rss)==1)break;end
  $fclose(pf);if(rss<0)$fatal(1,"rss missing");
  $fwrite(samplefd,"%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d\n",epoch,cycles,rss,ar_count,r_count,aw_count,w_count,b_count,env.state.rq_from_model_num);$fflush(samplefd);
  $display("AXI_GATE_EPOCH epoch=%0d cycles=%0d rss_kib=%0d AR=%0d R=%0d model_queue=%0d",epoch,cycles,rss,ar_count,r_count,env.state.rq_from_model_num);
 endtask
 task send_ar(input longint addr,input integer len);
  @(negedge clk);bus.ARADDR=addr;bus.ARLEN=len;bus.ARVALID=1;
  do @(posedge clk);while(bus.ARREADY!==1);
  @(negedge clk);bus.ARVALID=0;
 endtask
 task receive_burst(input longint addr,input integer len,input bit changed_region=0);
  logic[127:0] actual_word,expected_word;
  for(int beat=0;beat<=len;beat++)begin
   do @(posedge clk);while(!(bus.RVALID===1 && bus.RREADY===1));
   actual_word=bus.RDATA;expected_word=changed_region?changed[(addr-524288)/16+beat]:patterns[((addr/16)+beat)%16];
   if(bus.RRESP!==0 || bus.RID!==0 || bus.RLAST!==(beat==len) || actual_word!==expected_word)begin
    $display("AXI_GATE_DATA_MISMATCH addr=%0d beat=%0d actual=%h expected=%h last=%b resp=%b",addr,beat,actual_word,expected_word,bus.RLAST,bus.RRESP);$fatal(1,"wire read mismatch");
   end
  end
 endtask
 task masked_write(input integer block_index);
  logic[127:0] data;logic[15:0] mask;integer before_b;
  before_b=b_count;
  @(negedge clk);bus.AWADDR=524288+block_index*256;bus.AWLEN=15;bus.AWVALID=1;
  do @(posedge clk);while(bus.AWREADY!==1);
  @(negedge clk);bus.AWVALID=0;
  for(int beat=0;beat<16;beat++)begin
   data=~patterns[beat];mask=(beat%2)?16'haaaa:16'h5555;
   for(int j=0;j<16;j++)if(mask[j])changed[block_index*16+beat][j*8+:8]=data[j*8+:8];
   @(negedge clk);bus.WVALID=1;bus.WDATA=data;bus.WSTRB=mask;bus.WLAST=(beat==15);
   do @(posedge clk);while(bus.WREADY!==1);
   @(negedge clk);bus.WVALID=0;
  end
  wait(b_count==before_b+1);repeat(4)@(posedge clk);#0.1;
  if(wr.callbacks!=block_index+1)$fatal(1,"write callback missing");
 endtask
 virtual task run_phase(uvm_phase phase);
  axi_slave_sequence#(64,16,8,3,1) seq;integer rc;
  phase.raise_objection(this);samplefd=$fopen("axi_epoch_samples.csv","w");
  model.whole_page_size=1048576;model.min_offset=0;model.init_pages(1,1048576,0);
  for(int i=0;i<65536;i++)begin rc=model.pages[0].write_packed16(patterns[i%16],i*16);if(rc)$fatal(1,"model init");end
  wait(rst);repeat(3)@(posedge clk);
  seq=axi_slave_sequence#(64,16,8,3,1)::type_id::create("real_slave_sequence");seq.misc_if=misc;seq.isusr_delay=NO_DELAY;
  fork seq.start(env.vsqr);join_none
  sample(0);
  for(int block_index=0;block_index<2;block_index++)begin
   masked_write(block_index);
   fork send_ar(524288+block_index*256,15);receive_burst(524288+block_index*256,15,1);join
  end
  for(int epoch=1;epoch<=4;epoch++)begin
   issued=0;completed=0;
   fork
    begin
     for(int j=0;j<256;j++)begin
      wait(issued-completed<4);send_ar((j%128)*2048,127);issued++;
     end
    end
    begin
     for(int j=0;j<256;j++)begin receive_burst((j%128)*2048,127);completed++;end
    end
   join
   sample(epoch);
  end
  if(ar_count!=1026 || r_count!=131104 || aw_count!=2 || w_count!=32 || b_count!=2 || cb.callbacks!=1026 || wr.callbacks!=2)$fatal(1,"final wire counts");
  if(r_stalls==0 || w_stalls==0)$fatal(1,"backpressure not exercised");
  $fclose(samplefd);$fclose(fd);
  $display("AXI_GATE_PASS AR=%0d R=%0d AW=%0d W=%0d B=%0d rstalls=%0d arstalls=%0d wstalls=%0d",ar_count,r_count,aw_count,w_count,b_count,r_stalls,ar_stalls,w_stalls);
  phase.drop_objection(this);
 endtask
endclass
initial begin
 fd=$fopen("axi_wire.csv","w");if(!fd)$fatal(1,"wire open");
 for(int i=0;i<16;i++)for(int j=0;j<16;j++)patterns[i][j*8+:8]=((i*16+j)*17+3)&255;
 for(int i=0;i<32;i++)changed[i]=patterns[i%16];
 bus.ARID=0;bus.ARADDR=0;bus.ARLEN=0;bus.ARSIZE=4;bus.ARBURST=1;bus.ARLOCK=0;bus.ARCACHE=0;bus.ARPROT=0;bus.ARQOS=0;bus.ARREGION=0;bus.ARUSER=0;bus.ARVALID=0;
 bus.AWID=0;bus.AWADDR=0;bus.AWLEN=0;bus.AWSIZE=4;bus.AWBURST=1;bus.AWLOCK=0;bus.AWCACHE=0;bus.AWPROT=0;bus.AWQOS=0;bus.AWREGION=0;bus.AWUSER=0;bus.AWVALID=0;
 bus.WID=0;bus.WUSER=0;bus.WDATA=0;bus.WSTRB=0;bus.WVALID=0;bus.WLAST=0;bus.RREADY=0;bus.BREADY=0;
 uvm_config_db#(virtual axi_if#(64,16,8,3,1))::set(null,"uvm_test_top.env.*","vif",bus);
 run_test("gate_test");
end
initial begin #50;rst=1;end
initial begin #500000000;$fatal(1,"simulation watchdog");end
endmodule
