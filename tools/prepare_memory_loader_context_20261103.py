"""Finite no-DUT loader controls: module/UVM x new/factory, eight MiB."""
from pathlib import Path
import hashlib,json,tarfile
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';NAME='memory_loader_context_20261103_r1'
E=M/'experiments'/NAME;R=M/'reports'/NAME
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 E.mkdir(exist_ok=True);R.mkdir(exist_ok=True);assert not (R/'PLAN.json').exists()
 tb=r'''`timescale 1ns/1ps
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
'''
 (E/'allocation_tb.sv').write_text(tb)
 s=(ROOT/'tools/run_memory_allocation_micro_20261103.py').read_text().replace('memory_allocation_micro_20261103_r2',NAME)
 s=s.replace("assert not (M/'reports/full_bank_cosim_20261102_r2/ACTIVE.lock').exists()", "assert not (M/'reports/full_bank_cosim_20261102_r2/ACTIVE.lock').exists()\n assert not list((M/'reports').glob('memory_*/ACTIVE.lock'))")
 begin=s.index(" V.mkdir();shutil.copytree(OLD/'axivip'");end=s.index(" state={'state':",begin)
 s=s[:begin]+''' V.mkdir();shutil.copytree(OLD/'file_agent',V/'file_agent');shutil.copy2(E/'allocation_tb.sv',V/'allocation_tb.sv')
 assert sha(V/'file_agent/mem_model.sv')=='d1f50d29b2ed6636fd30a3d4420ec54f45a766410970162aba2056519d84a711'
 (V/'micro.prj').write_text('sv xil_defaultlib "file_agent/file_agent_pkg.sv"\\nsv xil_defaultlib "allocation_tb.sv"\\n')
 pattern=bytes((i*17+3)&255 for i in range(256));block=''.join('0x'+pattern[i:i+16][::-1].hex()+'\\n' for i in range(0,256,16))
 with (V/'c.lm_head_v4_partial_proto.autotvin_weights.dat').open('w') as f:
  f.write('[[[runtime]]]\\n[[transaction]] 0\\n')
  for i in range(8388608//256):f.write(block)
  f.write('[[/transaction]]\\n[[[/runtime]]]\\n')
 for name,value in [('tiled_offset.dat',0),('canonical_offset.dat',4194304)]:
  (V/name).write_text('[[[runtime]]]\\n[[transaction]] 0\\n0x%016x\\n[[/transaction]]\\n[[[/runtime]]]\\n'%value)
'''+s[end:]
 s=s.replace('-i ./axivip','-i ./file_agent').replace('for mode in range(6)','for mode in range(4)').replace('-testplusarg N=100000','-testplusarg UVM_VERBOSITY=UVM_LOW')
 compile(s,'run_context.py','exec');(E/'run_micro.py').write_text(s)
 plan={'state':'FROZEN_LOADER_EXECUTION_CONTEXT_CONTROL','sources':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in E.iterdir() if p.is_file()},
 'cases':['module/new','module/factory','UVM run_phase/new','UVM run_phase/factory'],'bytes':8388608,'repeated_same_address_writes':1000000,
 'qualified_model_sha256':'d1f50d29b2ed6636fd30a3d4420ec54f45a766410970162aba2056519d84a711','full_m14':'NOT_RUN','dut':'NOT_INSTANTIATED','board':'NOT_RUN','automatic_next_stage':False}
 (R/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
 with tarfile.open(R/'entry.tar.gz','w:gz') as a:
  for p in list(E.iterdir())+[R/'PLAN.json']:a.add(p,arcname=str(p.relative_to(ROOT)))
 template=(ROOT/'tools/bootstrap_memory_control_regression_20261103.py').read_text()
 template=template.replace('memory_control_regression_20261103_r1',NAME)
 template=template.replace('816b17f29cea5a90f3562e3fdbeea06a8731b673860b66ec947faf2849cf4948',sha(R/'entry.tar.gz'))
 (ROOT/'tools/bootstrap_memory_loader_context_20261103.py').write_text(template)
 print(json.dumps({'archive':str(R/'entry.tar.gz'),'sha256':sha(R/'entry.tar.gz')}))
if __name__=='__main__':main()
