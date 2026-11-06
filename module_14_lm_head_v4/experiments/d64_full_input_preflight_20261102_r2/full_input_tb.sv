`timescale 1ns/1ps
`include "uvm_macros.svh"
module full_input_tb;
import uvm_pkg::*;import file_agent_pkg::*;
mem_model_pages#(128,8) mem_blk_pages_weights;
task check_binary(input string path,input integer base,input integer count);
 integer fd,rc,i,k; reg[127:0] original;logic[7:0] actual;
 fd=$fopen(path,"rb");if(!fd)$fatal(1,"reference binary open failed");
 for(i=0;i<count;i=i+16)begin
  rc=$fread(original,fd);if(rc!=16)$fatal(1,"reference binary read count");
  for(k=0;k<16;k=k+1)begin
   rc=mem_blk_pages_weights.pages[0].read_one_elem(actual,base+i+k);
   if(rc || actual!==original[127-k*8 -: 8])$fatal(1,"complete model readback mismatch at %0d",base+i+k);
  end
 end
 rc=$fgetc(fd);if(rc!=-1)$fatal(1,"reference has extra bytes");$fclose(fd);
 $display("FULL_INPUT_BINARY_PASS base=%0d bytes=%0d",base,count);
endtask
initial begin
 mem_blk_pages_weights=new("weights");
 mem_blk_pages_weights.tvinload_hex128_single("/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1/.cache/p64_full_bank_cosim_20261026_r1/sim/tv/cdatafile/c.lm_head_v4_partial_proto.autotvin_weights.dat",545685504,0);
 if(mem_blk_pages_weights.pages.size()!=1)$fatal(1,"weight page count");
 `include "weights_preflight.svh"
 check_binary("/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1/module_14_lm_head_v4/reports/layout_topk_20261024_r1/assets/tiled_W_B1024.bin",0,273416192);
 check_binary("/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1/artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin",273416192,272269312);
 $display("FULL_INPUT_MEMORY_PASS bytes=545685504 words=34105344 sentinel=1522 all_bytes=1 dut=0");$finish;
end
endmodule
