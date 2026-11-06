"""Real frozen AXI slave VIP + packed memory callbacks, bounded wire gate."""
from pathlib import Path
import json,hashlib,tarfile,shutil
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';NAME='memory_axi_gate_20261103_r8'
E=M/'experiments'/NAME;R=M/'reports'/NAME;S=M/'reports/memory_growth_diagnosis_20261103_r1/sources'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 E.mkdir(exist_ok=True);R.mkdir(exist_ok=True);assert not (R/'PLAN.json').exists()
 C=M/'experiments/memory_burst_model_20261103_r3'
 shutil.copy2(C/'mem_model.sv',E/'mem_model.sv');shutil.copy2(M/'experiments/memory_full_startup_20261103_r1/memory_probe_pkg.sv',E/'memory_probe_pkg.sv')
 env=(S/'lm_head_v4_partial_proto_subsystem/lm_head_v4_partial_proto_env.sv').read_text();a=env.index('    class axi_latency_weights ');b=env.index('endclass',a)+len('endclass')
 (E/'original_latency.svh').write_text(env[a:b]+'\n')
 transfer=(S/'axivip/axi_transfer.sv').read_text()
 old='''        this.data = {this.data, tr.data};
        this.data_delay = {this.data_delay,tr.data_delay};
        this.rresp = {this.rresp, tr.rresp};
        this.strb  = {this.strb,  tr.strb };'''
 new='''        // Preserve self-append value semantics; avoid recopying every burst prefix.
        if(this==tr)begin
            this.data = {this.data, tr.data};
            this.data_delay = {this.data_delay,tr.data_delay};
            this.rresp = {this.rresp, tr.rresp};
            this.strb = {this.strb,tr.strb};
        end else begin
            foreach(tr.data[i])this.data.push_back(tr.data[i]);
            foreach(tr.data_delay[i])this.data_delay.push_back(tr.data_delay[i]);
            foreach(tr.rresp[i])this.rresp.push_back(tr.rresp[i]);
            foreach(tr.strb[i])this.strb.push_back(tr.strb[i]);
        end'''
 assert transfer.count(old)==1;transfer=transfer.replace(old,new);(E/'axi_transfer.sv').write_text(transfer)
 (E/'TRANSFER_CHANGES.json').write_text(json.dumps({'original_sha256':sha(S/'axivip/axi_transfer.sv'),'candidate_sha256':sha(E/'axi_transfer.sv'),'edits':[[old,new]]},indent=2)+'\n')
 state=(S/'axivip/axi_state.sv').read_text()
 old='''            for(int j=0; j<=tr.len; j++) begin
                if(tr.len+1-j==left_len) begin
                    for(int i=0; i<tr.bus_bytenum; i++) begin
                        if(addrcnt>=addrlow && addrcnt<addrlow/bytenum*bytenum+bytenum) begin
                            tr.data.push_back(rq_from_model[id][0].data.pop_front());
                            tr.data_delay.push_back(rq_from_model[id][0].data_delay.pop_front());
                            tr.rresp.push_back(rq_from_model[id][0].rresp.pop_front());
                        end else begin
                            tr.data.push_back(8'h0);
                        end
                        addrcnt++;
                    end
                end
                addrlow = addrlow/bytenum*bytenum+bytenum;
                addrcnt = addrlow/tr.bus_bytenum*tr.bus_bytenum;
            end'''
 new='''            begin : direct_read_beat
                int beat_index;
                beat_index=tr.len+1-left_len;
                if(beat_index>0)begin
                    addrlow=(tr.addr/bytenum+beat_index)*bytenum;
                    addrcnt=addrlow/tr.bus_bytenum*tr.bus_bytenum;
                end
                if(beat_index>=0 && beat_index<=tr.len)begin
                    for(int i=0;i<tr.bus_bytenum;i++)begin
                        if(addrcnt>=addrlow && addrcnt<addrlow/bytenum*bytenum+bytenum)begin
                            tr.data.push_back(rq_from_model[id][0].data.pop_front());
                            tr.data_delay.push_back(rq_from_model[id][0].data_delay.pop_front());
                            tr.rresp.push_back(rq_from_model[id][0].rresp.pop_front());
                        end else tr.data.push_back(8'h0);
                        addrcnt++;
                    end
                end
            end'''
 assert state.count(old)==1;state=state.replace(old,new);(E/'axi_state.sv').write_text(state)
 (E/'STATE_CHANGES.json').write_text(json.dumps({'original_sha256':sha(S/'axivip/axi_state.sv'),'candidate_sha256':sha(E/'axi_state.sv'),'edits':[[old,new]]},indent=2)+'\n')
 sequence=(S/'axivip/axi_slave_seq_lib.sv').read_text()
 old="                void'(std::randomize(idx) with { idx inside {[0:ids.size-1]}; });"
 new="""                begin
                    int final_index;
                    final_index=ids.size()-1;
                    void'(std::randomize(idx) with {idx inside {[0:final_index]};});
                end"""
 assert sequence.count(old)==2;sequence=sequence.replace(old,new);(E/'axi_slave_seq_lib.sv').write_text(sequence)
 seq_edits=[[old,new,2]]
 old='''            forever begin
                int ids[$];
                int idx;
                int div;
                axi_transfer axi_rtr, tmp;
                `uvm_create_on(axi_rtr, p_sequencer.slave_rsqr);
                wait(state.rq_from_model_num>0);'''
 new='''            begin : reusable_r_sequence_item
                axi_transfer axi_rtr, tmp;
                `uvm_create_on(axi_rtr, p_sequencer.slave_rsqr);
                forever begin
                int ids[$];
                int idx;
                int div;
                // uvm_send returns only after driver's item_done; no response is posted.
                axi_rtr.init();
                axi_rtr.set_transaction_id(-1);
                wait(state.rq_from_model_num>0);'''
 assert sequence.count(old)==1;sequence=sequence.replace(old,new);seq_edits.append([old,new,1])
 old='''                `uvm_send(axi_rtr);
            end
            begin
                @finish;'''
 new='''                `uvm_send(axi_rtr);
                end
            end
            begin
                @finish;'''
 assert sequence.count(old)==1;sequence=sequence.replace(old,new);seq_edits.append([old,new,1])
 # r7 is a burst-length causal control: revert R-sequence reuse from r6.
 for before,after,occ in reversed(seq_edits[1:]):
  assert sequence.count(after)==occ;sequence=sequence.replace(after,before)
 seq_edits=seq_edits[:1]
 (E/'axi_slave_seq_lib.sv').write_text(sequence)
 (E/'SEQUENCE_CHANGES.json').write_text(json.dumps({'original_sha256':sha(S/'axivip/axi_slave_seq_lib.sv'),'candidate_sha256':sha(E/'axi_slave_seq_lib.sv'),'edits':seq_edits,'scope':'Only SLAVE R sequence item reused after item_done; monitor/AR and rq model objects remain fresh'},indent=2)+'\n')
 monitor=(S/'axivip/axi_monitor.sv').read_text();monitor_edits=[]
 for label in ['aw2b','ar2r']:
  before='''    virtual protected task collect_%s_transfer();
        axi_transfer %s_tr;'''%(label,label)
  after=before+'\n        int j,k; // One task-lifetime index pair; same original per-clock loop.'
  assert monitor.count(before)==1;monitor=monitor.replace(before,after);monitor_edits.append([before,after])
  before='''                for(int j=0; j<cfg.id_num; j++) begin
                    for(int k=0; k<%s_delay[j].size; k++) %s_delay[j][k]++;
                end'''%(label,label)
  after=before.replace('for(int j=','for(j=').replace('for(int k=','for(k=')
  assert monitor.count(before)==1;monitor=monitor.replace(before,after);monitor_edits.append([before,after])
 (E/'axi_monitor.sv').write_text(monitor)
 (E/'MONITOR_CHANGES.json').write_text(json.dumps({'original_sha256':sha(S/'axivip/axi_monitor.sv'),'candidate_sha256':sha(E/'axi_monitor.sv'),'edits':monitor_edits},indent=2)+'\n')
 shutil.copy2(M/'reports/memory_burst_full_input_20261103_r1/INDEPENDENT_REVIEW.json',E/'gate_input.json')
 tb=r'''`timescale 1ns/1ps
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
  env.vsqr.slave_awsqr.disable_auto_item_recording();env.vsqr.slave_wsqr.disable_auto_item_recording();env.vsqr.slave_bsqr.disable_auto_item_recording();
  env.vsqr.slave_arsqr.disable_auto_item_recording();env.vsqr.slave_rsqr.disable_auto_item_recording();
  if(env.vsqr.slave_rsqr.is_auto_item_recording_enabled())`uvm_fatal("recording","automatic item recording still enabled")
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
'''
 (E/'axi_gate_tb.sv').write_text(tb)
 # Reuse the bounded runner, retaining exact original AXI sources from the full job.
 s=(ROOT/'tools/run_memory_allocation_micro_20261103.py').read_text().replace('memory_allocation_micro_20261103_r2',NAME)
 s=s.replace("assert not (M/'reports/full_bank_cosim_20261102_r2/ACTIVE.lock').exists()", "assert not (M/'reports/full_bank_cosim_20261102_r2/ACTIVE.lock').exists()\n assert not list((M/'reports').glob('memory_*/ACTIVE.lock'))\n assert json.loads((E/'gate_input.json').read_text())['state']=='PASS_INDEPENDENT_BURST_REAL_FULL_INPUT_INIT_AND_ALL_WORDS'")
 a=s.index(" V.mkdir();shutil.copytree(OLD/'axivip'");b=s.index(" state={'state':",a)
 s=s[:a]+''' V.mkdir();shutil.copytree(OLD/'axivip',V/'axivip');shutil.copytree(OLD/'file_agent',V/'file_agent')
 shutil.copy2(OLD/'svtb/misc_interface.sv',V/'misc_interface.sv')
 for n in ['axi_gate_tb.sv','memory_probe_pkg.sv','original_latency.svh']:shutil.copy2(E/n,V/n)
 shutil.copy2(E/'mem_model.sv',V/'file_agent/mem_model.sv')
 (V/'micro.prj').write_text('sv xil_defaultlib "memory_probe_pkg.sv"\\nsv xil_defaultlib "misc_interface.sv"\\nsv xil_defaultlib "axivip/axi_if.sv"\\nsv xil_defaultlib "axivip/axi_pkg.sv"\\nsv xil_defaultlib "file_agent/file_agent_pkg.sv"\\nsv xil_defaultlib "axi_gate_tb.sv"\\n')
 actual={str(p.relative_to(V)):sha(p) for p in V.rglob('*') if p.is_file() and p.suffix in ['.sv','.svh']}
 (R/'COMPILED_SOURCES.json').write_text(json.dumps(actual,indent=2)+'\\n')
'''+s[b:]
 s=s.replace("if phase.startswith('mode_'):","if phase=='mode_axi':").replace("x.startswith('ALLOCATION_MICRO_PASS ')","x.startswith('AXI_GATE_PASS ')")
 s=s.replace("shutil.copy2(V/'allocation_samples.csv',d/'allocation_samples.csv')", "\n   for n in ['axi_epoch_samples.csv','axi_wire.csv']:shutil.copy2(V/n,d/n)")
 s=s.replace("shutil.copy2(E/'mem_model.sv',V/'file_agent/mem_model.sv')", "shutil.copy2(E/'mem_model.sv',V/'file_agent/mem_model.sv');shutil.copy2(E/'axi_transfer.sv',V/'axivip/axi_transfer.sv');shutil.copy2(E/'axi_state.sv',V/'axivip/axi_state.sv');shutil.copy2(E/'axi_slave_seq_lib.sv',V/'axivip/axi_slave_seq_lib.sv')")
 s=s.replace("shutil.copy2(E/'axi_transfer.sv',V/'axivip/axi_transfer.sv')", "shutil.copy2(E/'axi_transfer.sv',V/'axivip/axi_transfer.sv');shutil.copy2(E/'axi_monitor.sv',V/'axivip/axi_monitor.sv')")
 a=s.index("  run('elaborate',");b=s.index("  state.update(state='TOOL_PASS",a)
 s=s[:a]+'''  run('elaborate','/tools/Xilinx/Vivado/2022.2/bin/xelab xil_defaultlib.axi_gate_tb -prj micro.prj -L uvm -L xil_defaultlib -i ./axivip -i ./file_agent -i . -relax -debug all -s axi_gate')
  run('mode_axi','/tools/Xilinx/Vivado/2022.2/bin/xsim axi_gate -runall -testplusarg UVM_VERBOSITY=UVM_LOW')
'''+s[b:]
 compile(s,'run_gate.py','exec');(E/'run_micro.py').write_text(s)
 plan={'state':'FROZEN_REAL_AXI_PACKED_MODEL_GATE','sources':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in E.iterdir() if p.is_file()},'model_sha256':sha(E/'mem_model.sv'),
 'scope':'Frozen AXI slave drivers/state/monitor/sequence, exact original weights latency class, native bounded master, 4 outstanding reads, WSTRB, 2MiB repeated read;no M14 DUT',
 'data_width_bits':128,'memory_bytes':1048576,'read_bursts':1026,'read_beats':131104,'write_bursts':2,'write_beats':32,'epochs':4,'causal_control':'same original wire workload; monitor per-clock loop indices task lifetime instead of inner-block lifetime','full_m14':'NOT_RUN','board':'NOT_RUN','automatic_next_stage':False}
 (R/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
 with tarfile.open(R/'entry.tar.gz','w:gz') as t:
  for p in list(E.iterdir())+[R/'PLAN.json']:t.add(p,arcname=str(p.relative_to(ROOT)))
 bootstrap=(ROOT/'tools/bootstrap_memory_control_regression_20261103.py').read_text().replace('memory_control_regression_20261103_r1',NAME).replace('816b17f29cea5a90f3562e3fdbeea06a8731b673860b66ec947faf2849cf4948',sha(R/'entry.tar.gz'))
 (ROOT/'tools/bootstrap_memory_axi_gate_20261103.py').write_text(bootstrap)
 print(json.dumps({'archive':str(R/'entry.tar.gz'),'sha256':sha(R/'entry.tar.gz')}))
if __name__=='__main__':main()
