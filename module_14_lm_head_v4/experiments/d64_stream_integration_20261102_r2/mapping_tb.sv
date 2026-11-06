`timescale 1ns/1ps
module mapping_tb;
import uvm_pkg::*;import file_agent_pkg::*;
mem_model_pages_with_diffofst#(128,8) model, fallback;
string files[$];integer fd,rc,i,j;logic[7:0] data[$];
task automatic configure(input mem_model_pages_with_diffofst#(128,8) obj,input string path);
 string fp[$];
 obj.whole_page_size=8192;
 obj.maxi_bundlevar_fpath["tiled_weight"]="tiled_offset.dat";
 obj.maxi_bundlevar_fpath["canonical_weight"]="canonical_offset.dat";
 fp.push_back(path);obj.tvinload_pagechk_atinit(fp,8192,0);
 if(obj.page_ofst.size()!=1 || obj.page_ofst[0]!=0 || obj.rd_page_idx!=0 || obj.min_offset!=0)$fatal(1,"page mapping initialization");
 if(obj.maxi_bundlevar_offset.num()!=2 || obj.maxi_bundlevar_offset["tiled_weight"]!=0 || obj.maxi_bundlevar_offset["canonical_weight"]!=4096)$fatal(1,"pointer metadata initialization");
endtask
initial begin
 model=new("real_offset_subclass");
 configure(model,"c.lm_head_v4_partial_proto.autotvin_weights.dat");
 fd=$fopen("mapping_bytes.bin","wb");if(!fd)$fatal(1,"dump open");
 for(i=0;i<8192;i=i+16)begin
  model.read_elems_pipepage(data,i,16);if(data.size()!=16)$fatal(1,"actual pipe callback no memory");
  for(j=0;j<16;j=j+1)begin
   if(data[j]!==(((i+j)*17+3)&255))$fatal(1,"mapped read value");
   $fwrite(fd,"%c",data[j]);
  end
 end
 model.read_elems_pipepage(data,4088,16);
 for(j=0;j<16;j=j+1)if(data[j]!==(((4088+j)*17+3)&255))$fatal(1,"cross4KiB callback");
 $fclose(fd);
 fallback=new("ordinary_loader");configure(fallback,"ordinary.dat");
 fallback.read_elems_pipepage(data,4096,16);
 for(j=0;j<16;j=j+1)if(data[j]!==(((4096+j)*17+3)&255))$fatal(1,"fallback callback");
 $display("MAPPING_INTEGRATION_PASS bytes=8192 offsets=0,4096 page_ofst=0 pipe_reads=513 fallback=1");$finish;
end
endmodule
