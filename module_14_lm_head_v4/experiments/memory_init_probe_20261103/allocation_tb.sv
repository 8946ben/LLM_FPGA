`timescale 1ns/1ps
module allocation_tb;
import uvm_pkg::*;import file_agent_pkg::*;
mem_model_pages#(128,8) base;
mem_model_pages_with_diffofst#(128,8) derived;
string paths[$];integer mode,n,fd,i,rc;logic[7:0] value;longint unsigned checksum;
task automatic sample(input integer phase,input integer count);
 integer pf,rss;string line;
 pf=$fopen("/proc/self/status","r");rss=-1;
 while(!$feof(pf))begin rc=$fgets(line,pf);if($sscanf(line,"VmRSS: %d kB",rss)==1)break;end
 $fclose(pf);if(rss<0)$fatal(1,"RSS missing");
 $fwrite(fd,"%0d,%0d,%0d,%0d,%0d\n",mode,phase,count,rss,checksum);$fflush(fd);
 $display("INIT_SAMPLE mode=%0d phase=%0d bytes=%0d rss_kib=%0d checksum=%0d",mode,phase,count,rss,checksum);
endtask
initial begin
 if(!$value$plusargs("MODE=%d",mode))mode=0;
 n=67108864;checksum=0;fd=$fopen("allocation_samples.csv","w");sample(0,0);
 if(mode==0)begin
  base=new("base");base.tvinload_hex128_single("c.lm_head_v4_partial_proto.autotvin_weights.dat",n,0);
 end else begin
  derived=new("derived");derived.whole_page_size=n+256;
  derived.maxi_bundlevar_fpath["tiled_weight"]="tiled_offset.dat";
  derived.maxi_bundlevar_fpath["canonical_weight"]="canonical_offset.dat";
  paths.push_back("c.lm_head_v4_partial_proto.autotvin_weights.dat");
  derived.tvinload_pagechk_atinit(paths,n,0);
  if(derived.maxi_bundlevar_offset.num()!=2 || derived.page_ofst.size()!=1)$fatal(1,"metadata missing");
  base=derived;
 end
 sample(1,n);
 for(i=0;i<n;i++)begin
  rc=base.pages[0].read_one_elem(value,i);
  if(rc || value!==((i*17+3)&255))$fatal(1,"input data mismatch");
  checksum+=value;
  if((i+1)%16777216==0)sample(2,i+1);
 end
 if(checksum!=64'd8556380160)$fatal(1,"all byte checksum");
 sample(3,n);$fclose(fd);$display("ALLOCATION_MICRO_PASS input_init mode=%0d bytes=%0d checksum=%0d",mode,n,checksum);$finish;
end
endmodule
