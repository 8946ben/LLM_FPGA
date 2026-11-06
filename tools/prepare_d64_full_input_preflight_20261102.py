"""Full input scale, no DUT: exact source hashes plus every memory byte readback."""
from pathlib import Path
import hashlib,json,tarfile
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4'
E=M/'experiments/d64_full_input_preflight_20261102_r2';R=M/'reports/d64_full_input_preflight_20261102_r2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 E.mkdir(exist_ok=True);R.mkdir(exist_ok=True);assert not (R/'PLAN.json').exists()
 remote='/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1'
 tb='''`timescale 1ns/1ps
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
 mem_blk_pages_weights.tvinload_hex128_single("REMOTE/.cache/p64_full_bank_cosim_20261026_r1/sim/tv/cdatafile/c.lm_head_v4_partial_proto.autotvin_weights.dat",545685504,0);
 if(mem_blk_pages_weights.pages.size()!=1)$fatal(1,"weight page count");
 `include "weights_preflight.svh"
 check_binary("REMOTE/module_14_lm_head_v4/reports/layout_topk_20261024_r1/assets/tiled_W_B1024.bin",0,273416192);
 check_binary("REMOTE/artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin",273416192,272269312);
 $display("FULL_INPUT_MEMORY_PASS bytes=545685504 words=34105344 sentinel=1522 all_bytes=1 dut=0");$finish;
end
endmodule
'''.replace('REMOTE',remote)
 (E/'full_input_tb.sv').write_text(tb)
 (E/'mem_model.sv').write_bytes((M/'experiments/d64_stream_loader_20261102/mem_model.sv').read_bytes())
 (E/'weights_preflight.svh').write_bytes((M/'experiments/sim_memory_bank_20261026/weights_preflight.svh').read_bytes())
 (E/'run_preflight.py').write_bytes((ROOT/'tools/run_d64_full_input_preflight_20261102.py').read_bytes())
 oldplan=json.loads((M/'reports/full_bank_cosim_20261026_r1/PLAN.json').read_text())
 source_paths=['module_14_lm_head_v4/reports/layout_topk_20261024_r1/assets/tiled_W_B1024.bin','artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin']
 plan={'state':'FROZEN_NO_DUT_FULL_INPUT_MEMORY_PREFLIGHT','source_sha256':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in E.iterdir() if p.is_file()},
   'weight_sha256':{p:oldplan['source_sha256'][p] for p in source_paths},'full_tv_sha256':oldplan['full_tv_sha256'],
   'limits':{'phase_seconds':900,'max_group_rss_gib':32,'min_available_gib':32},'dut':'NOT_INSTANTIATED','full_m14':'NOT_RUN','board':'NOT_RUN','automatic_next_stage':False}
 (R/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
 with tarfile.open(R/'entry.tar.gz','w:gz') as a:
  for p in list(E.iterdir())+[R/'PLAN.json']:a.add(p,arcname=str(p.relative_to(ROOT)))
 print(json.dumps({'archive':str(R/'entry.tar.gz'),'sha256':sha(R/'entry.tar.gz')}))
if __name__=='__main__':main()
