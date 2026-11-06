`timescale 1ns/1ps
`include "uvm_macros.svh"
module allocation_tb;
import uvm_pkg::*;import axi_pkg::*;
class fixed_master_state extends axi_state;
 function new(string name,uvm_component parent);super.new(name,parent);endfunction
 virtual function void write_ar(axi_transfer tr);
  if(cfg.drv_type==SLAVE)super.write_ar(tr);
  else begin
   tr.ainfo_rx=1;tr.expected_read_latency=cfg.clatency.get_rd_lat();
   arq[tr.id].push_back(tr);
  end
 endfunction
endclass
class four_bytes extends axi_state_cbs;
 virtual function void memmodel_read_fromar(ref logic[7:0] data[$],input longint addr,input longint len);
  for(int k=0;k<len;k++)data.push_back(k&255);
 endfunction
endclass
axi_state state;fixed_master_state corrected;axi_cfg cfg;four_bytes cb;
axi_transfer ar,rr,a2r,from_model;
integer mode,n,i,j,fd;longint unsigned checksum;
task automatic sample(input integer count);
 integer procfd,rc,rss;string line;
 procfd=$fopen("/proc/self/status","r");if(!procfd)$fatal(1,"proc open");rss=-1;
 while(!$feof(procfd))begin rc=$fgets(line,procfd);if($sscanf(line,"VmRSS: %d kB",rss)==1)break;end
 $fclose(procfd);if(rss<0)$fatal(1,"RSS missing");
 $fwrite(fd,"%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d\n",mode,count,rss,state.rq_from_model[0].size(),state.arq[0].size(),state.rq[0].size(),state.rq_from_model_num,checksum);$fflush(fd);
 $display("QUEUE_SAMPLE mode=%0d completed=%0d rss_kib=%0d retained_model=%0d arq=%0d rq=%0d checksum=%0d",mode,count,rss,state.rq_from_model[0].size(),state.arq[0].size(),state.rq[0].size(),checksum);
endtask
initial begin
 if(!$value$plusargs("MODE=%d",mode))mode=0;
 if(!$value$plusargs("N=%d",n))n=20000;
 cfg=new("cfg");cfg.set_default();cfg.drv_type=(mode%2==0)?MASTER:SLAVE;
 uvm_config_db#(axi_cfg)::set(null,"probe","cfg",cfg);
 if(mode>=2)begin corrected=new("probe",null);state=corrected;end else state=new("probe",null);
 state.build_phase(null);cb=new();uvm_callbacks#(axi_state,axi_state_cbs)::add(state,cb);
 fd=$fopen("allocation_samples.csv","w");if(!fd)$fatal(1,"out open");checksum=0;sample(0);
 for(i=0;i<n;i++)begin
  ar=new("ar");ar.id=0;ar.addr=0;ar.len=0;ar.size=2;ar.bus_bytenum=4;ar.rw=RD;ar.tr_type=AR_TR;
  for(j=0;j<4;j++)begin ar.rresp.push_back(OKAY);ar.data_delay.push_back(0);end
  state.write_ar(ar);
  if(mode%2==1)begin
   from_model=state.get_onedata_from_rqmodel(0);
   if(from_model.data.size()!=4 || from_model.data[3]!==3)$fatal(1,"slave model data");
   from_model=null;
  end
  rr=new("r");rr.id=0;rr.len=0;rr.size=2;rr.bus_bytenum=4;rr.last=1;rr.rw=RD;rr.tr_type=R_TR;
  for(j=0;j<4;j++)begin rr.data.push_back(j);rr.rresp.push_back(OKAY);rr.data_delay.push_back(0);checksum+=j;end
  state.write_r(rr);
  a2r=new("a2r");a2r.id=0;a2r.bus_bytenum=4;a2r.tr_type=AR2R_TR;state.write_ar2r(a2r);
  if(state.arq[0].size()!=0 || state.rq[0].size()!=0)$fatal(1,"protocol outstanding not drained");
  ar=null;rr=null;a2r=null;
  #1;
  if((i+1)%(n/4)==0)sample(i+1);
 end
 if(mode==0 && state.rq_from_model[0].size()!=n)$fatal(1,"baseline retention not reproduced");
 if(mode!=0 && state.rq_from_model[0].size()!=0)$fatal(1,"unexpected slave queue retention");
 sample(n+1);$fclose(fd);
 $display("ALLOCATION_MICRO_PASS queue_probe mode=%0d n=%0d retained=%0d checksum=%0d",mode,n,state.rq_from_model[0].size(),checksum);$finish;
end
endmodule
