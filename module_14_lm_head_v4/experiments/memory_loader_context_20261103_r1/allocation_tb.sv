`timescale 1ns/1ps
`include "uvm_macros.svh"
module allocation_tb;
import uvm_pkg::*;import file_agent_pkg::*;
integer mode,fd;longint unsigned checksum;string paths[$];logic[7:0] got;
mem_model_pages_with_diffofst#(128,8) model;
task automatic sample(input integer stage,input integer count);
 integer pf,rc,rss;string line;pf=$fopen("/proc/self/status","r");rss=-1;
 while(!$feof(pf))begin rc=$fgets(line,pf);if($sscanf(line,"VmRSS: %d kB",rss)==1)break;end
 $fclose(pf);if(rss<0)$fatal(1,"RSS missing");
 $fwrite(fd,"%0d,%0d,%0d,%0d,%0d\n",mode,stage,count,rss,checksum);$fflush(fd);
 $display("CONTEXT_SAMPLE mode=%0d stage=%0d count=%0d rss_kib=%0d checksum=%0d",mode,stage,count,rss,checksum);
endtask
task automatic load_case();
 integer rc;checksum=0;sample(0,0);
 if(mode%2==0)model=new("context_model");
 else model=mem_model_pages_with_diffofst#(128,8)::type_id::create("context_model");
 model.whole_page_size=8388864;
 model.maxi_bundlevar_fpath["tiled_weight"]="tiled_offset.dat";
 model.maxi_bundlevar_fpath["canonical_weight"]="canonical_offset.dat";
 paths.push_back("c.lm_head_v4_partial_proto.autotvin_weights.dat");
 model.tvinload_pagechk_atinit(paths,8388608,0);sample(1,8388608);
 if(model.pages[0].banks.size()!=8 || model.pages[0].banks[0].mem.size()!=65536 || $bits(model.pages[0].banks[0].mem[0])!=128)$fatal(1,"bank shape");
 $display("CONTEXT_BANK_SHAPE banks=%0d slots=%0d word_bits=%0d flag_bits=%0d",model.pages[0].banks.size(),model.pages[0].banks[0].mem.size(),$bits(model.pages[0].banks[0].mem[0]),$bits(model.pages[0].banks[0].IsWr[0]));
 for(int i=0;i<8388608;i++)begin
  rc=model.pages[0].read_one_elem(got,i);if(rc || got!==((i*17+3)&255))$fatal(1,"byte mismatch");checksum+=got;
 end
 if(checksum!=64'd1069547520)$fatal(1,"checksum");sample(2,8388608);
 for(int i=0;i<1000000;i++)begin
  rc=model.pages[0].write_one_elem(i&255,0);if(rc)$fatal(1,"overwrite failure");
 end
 rc=model.pages[0].read_one_elem(got,0);if(rc || got!==8'h3f)$fatal(1,"overwrite check");sample(3,1000000);
 sample(4,1000000);$fclose(fd);
 $display("ALLOCATION_MICRO_PASS loader_context mode=%0d bytes=8388608 repeated_writes=1000000 checksum=%0d",mode,checksum);
endtask
class context_test extends uvm_test;
 `uvm_component_utils(context_test)
 function new(string name="context_test",uvm_component parent=null);super.new(name,parent);endfunction
 virtual task run_phase(uvm_phase phase);
  phase.raise_objection(this);allocation_tb.load_case();phase.drop_objection(this);
 endtask
endclass
initial begin
 if(!$value$plusargs("MODE=%d",mode))mode=0;
 fd=$fopen("allocation_samples.csv","w");if(!fd)$fatal(1,"CSV open");
 if(mode<2)begin load_case();$finish;end
 else run_test("context_test");
end
endmodule
