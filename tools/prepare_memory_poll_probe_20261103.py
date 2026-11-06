"""Real original AXI control master, bounded fake status register, no lm_head."""
from pathlib import Path
import hashlib,json,tarfile
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';E=M/'experiments/memory_poll_probe_20261103_r3';R=M/'reports/memory_poll_probe_20261103_r3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 E.mkdir(exist_ok=True);R.mkdir(exist_ok=True);assert not (R/'PLAN.json').exists()
 tb='''`timescale 1ns/1ps
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
   ar_count++;$fwrite(busfd,"A,%0d,%0d,%0d\\n",cycles,ar_count,bus.ARADDR);bus.RVALID<=1;
  end
  if(bus.RVALID===1 && bus.RREADY===1)begin
   if(bus.RDATA!==0 || bus.RRESP!==0 || bus.RLAST!==1)$fatal(1,"status R bits");
   r_count++;$fwrite(busfd,"R,%0d,%0d,%0d\\n",cycles,r_count,bus.RDATA);bus.RVALID<=0;
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
  $fwrite(fd,"%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d\\n",mode,cycles,polls,rss,env.state.rq_from_model[0].size(),ar_count,r_count,env.state.rd_outstanding_cal());$fflush(fd);
  $display("POLL_SAMPLE mode=%0d cycle=%0d polls=%0d rss_kib=%0d model_q=%0d",mode,cycles,polls,rss,env.state.rq_from_model[0].size());
 endtask
 virtual task run_phase(uvm_phase phase);
  axi_busdatas_master_sequence#(8,32) seq;integer next_sample;
  phase.raise_objection(this);wait(mif.reset===1);repeat(3)@(posedge mif.clock);
  fd=$fopen("allocation_samples.csv","w");polls=0;interval=(mode==1)?2000:20;sample();next_sample=n/4;
  while(cycles<n)begin
   seq=axi_busdatas_master_sequence#(8,32)::type_id::create("poll_control");
   seq.isusr_delay=NO_DELAY;seq.misc_if=mif;seq.rd_addr.push_back(0);seq.start(env.vsqr);seq=null;polls++;
   repeat(interval)@(posedge mif.clock);
   if(env.state.rd_outstanding_cal()!=0)$fatal(1,"poll read not complete");
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
'''
 (E/'allocation_tb.sv').write_text(tb)
 s=(ROOT/'tools/run_memory_allocation_micro_20261103.py').read_text().replace('experiments/memory_allocation_micro_20261103_r2','experiments/memory_poll_probe_20261103_r3').replace('reports/memory_allocation_micro_20261103_r2','reports/memory_poll_probe_20261103_r3').replace('.cache/memory_allocation_micro_20261103_r2','.cache/memory_poll_probe_20261103_r3').replace('for mode in range(6)','for mode in range(3)').replace('-testplusarg N=100000','-testplusarg N=200000 -testplusarg UVM_VERBOSITY=UVM_LOW')
 s=s.replace("shutil.copy2(V/'allocation_samples.csv',d/'allocation_samples.csv')", "shutil.copy2(V/'allocation_samples.csv',d/'allocation_samples.csv');shutil.copy2(V/'wire_events.csv',d/'wire_events.csv')")
 compile(s,'run_poll.py','exec');(E/'run_micro.py').write_text(s)
 plan={'state':'FROZEN_REAL_AXI_CONTROL_POLL_CAUSAL_TEST','sources':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in E.iterdir() if p.is_file()},
 'cases':['original poll every20 cycles','original poll every2000 cycles','master queue guard every20 cycles'],'stop_cycles':200000,
 'scope':'Original AXI master/monitor/sequences and wire handshakes, fake constant status register, no DUT or weights',
 'full_m14':'NOT_RUN','board':'NOT_RUN','automatic_next_stage':False}
 (R/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
 with tarfile.open(R/'entry.tar.gz','w:gz') as a:
  for p in list(E.iterdir())+[R/'PLAN.json']:a.add(p,arcname=str(p.relative_to(ROOT)))
 print(json.dumps({'archive':str(R/'entry.tar.gz'),'sha256':sha(R/'entry.tar.gz')}))
if __name__=='__main__':main()
