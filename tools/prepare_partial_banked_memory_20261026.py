"""Prepare isolated simulator-only memory banking and deterministic unit tests."""
from pathlib import Path
import hashlib,json,difflib,tarfile
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4'
E=M/'experiments/sim_memory_bank_20261026';R=M/'reports/sim_memory_bank_20261026_r1'
OLD=M/'reports/partial_rtl_20261026_diagnosis_r1/model_source/file_agent/mem_model.sv'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert not (R/'PLAN.json').exists()
 E.mkdir(exist_ok=True);R.mkdir(exist_ok=True)
 original=OLD.read_text();assert sha(OLD)=='d23ae329a236384b03397c3a3f01a94ae75d178d34a5c57f101fb8bee32efd26'
 start=original.index('class mem_model#');tail=original.index('class mem_model_pages#')
 oldclass=original[start:tail]
 newclass=oldclass.replace('    logic[WIDTH-1:0] mem[];\n    bit IsWr[];', '    lmh_sim_bank#(WIDTH) banks[];')
 newclass=newclass.replace('        mem = new[depth];\n        IsWr = new[depth];\n        IsWr[depth] = \'{default:0};',
  '        // Each independently allocated array stays below the XSIM bit-index limit.\n        banks = new[depth / 1048576 + ((depth % 1048576) != 0)];')
 newclass=newclass.replace('        longint addr;\n        addr = addrin', '        longint addr;\n        int bank_id, slot;\n        addr = addrin')
 newclass=newclass.replace('        if(IsWr[addr]==0) begin', '        bank_id = addr >> 20;\n        slot = addr & 1048575;\n        if(banks[bank_id] == null) begin\n            data = \'hx;\n        end else begin\n            data = banks[bank_id].mem[slot];\n        end\n        if(banks[bank_id] == null || banks[bank_id].IsWr[slot]==0) begin')
 newclass=newclass.replace('        data=mem[addr];\n', '')
 newclass=newclass.replace('    function bit write_one_elem(logic[WIDTH-1:0] data, longint addr);\n', '    function bit write_one_elem(logic[WIDTH-1:0] data, longint addr);\n        int bank_id, slot, count;\n')
 newclass=newclass.replace('        mem[addr]=data;\n        IsWr[addr]=1;', '        bank_id = addr >> 20;\n        slot = addr & 1048575;\n        if(banks[bank_id] == null) begin\n            count = depth - bank_id * 1048576;\n            if(count > 1048576) count = 1048576;\n            banks[bank_id] = new(count);\n        end\n        banks[bank_id].mem[slot]=data;\n        banks[bank_id].IsWr[slot]=1;')
 bank='''// Simulation-only bank; not synthesized and not a deployed memory ABI.
class lmh_sim_bank#(int WIDTH = 8);
    logic[WIDTH-1:0] mem[];
    bit IsWr[];
    function new(int count);
        mem = new[count];
        IsWr = new[count];
    endfunction
endclass

'''
 patched=original[:start]+bank+newclass+original[tail:]
 assert patched[patched.index('class mem_model_pages#'):]==original[tail:]
 assert 'data=mem[addr]' not in patched
 (E/'mem_model.sv').write_text(patched)
 (E/'model.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),patched.splitlines(True),fromfile='original/mem_model.sv',tofile='isolated/mem_model.sv')))
 tb='''`timescale 1ns/1ps
module bank_memory_tb;
import uvm_pkg::*;
import file_agent_pkg::*;
mem_model#(8) m;
mem_model#(32) m32;
mem_model#(128) m128;
logic[7:0] q[$], outq[$];
logic[7:0] value;
logic[31:0] v32;
logic[127:0] v128;
integer fd, status, i;
longint a;
task put(input longint address, input logic[7:0] data);
 status=m.write_one_elem(data,address);
 $fwrite(fd,"W,%016h,%02h,%0d\\n",address,data,status);
endtask
task get(input longint address);
 status=m.read_one_elem(value,address);
 $fwrite(fd,"R,%016h,%02h,%0d\\n",address,value,status);
endtask
initial begin
 fd=$fopen("memory_events.csv","w");if(fd==0)$fatal(1,"event file");
 m=new("bank_unit");m.init(545685504,0);$fwrite(fd,"INIT,545685504,0\\n");
 get(-1);get(545685504);get(64'h100001200);
 if(m.is_rd!==0)$fatal(1,"out-of-range set is_rd");
 get(64'h1234);if(m.is_rd!==1)$fatal(1,"valid unread did not set is_rd");
 for(i=0;i<512;i=i+1)begin
  a=i*4099;
  put(a,(i*17+3)&255);put(a+64'h20000000,(i*17+131)&255);
 end
 for(i=0;i<512;i=i+1)begin a=i*4099;get(a);get(a+64'h20000000);end
 put(1048575,8'ha1);put(1048576,8'hb2);get(1048575);get(1048576);
 put(545685503,8'hc3);get(545685503);put(545685504,8'hd4);get(545685504);
 put(-1,8'h55);put(64'h100000000,8'h66);get(0);
 q.delete();for(i=0;i<8;i=i+1)q.push_back(8'ha0+i);
 status=m.write_elems(q,1048572);if(status!=0)$fatal(1,"bulk crossbank status");
 $fwrite(fd,"BW,1048572,8,0\\n");for(i=0;i<8;i=i+1)get(1048572+i);
 m.read_elems(outq,1048572,8);if(outq.size()!=8)$fatal(1,"bulk read size");
 for(i=0;i<8;i=i+1)if(outq[i]!==q[i])$fatal(1,"bulk read order");
 status=m.write_elems(q,545685500);if(status!=4)$fatal(1,"bulk partial status");
 $fwrite(fd,"BW,545685500,8,4\\n");for(i=0;i<8;i=i+1)get(545685500+i);
 m.init(17,97);$fwrite(fd,"INIT,17,97\\n");
 get(96);get(97);put(97,8'h12);put(113,8'h34);get(97);get(113);get(114);
 m.init(0,0);$fwrite(fd,"INIT,0,0\\n");put(0,8'h22);get(0);
 m32=new("bank32");m32.init(134222368,0);
 status=m32.write_one_elem(32'h12345678,64'h1200);
 status=m32.write_one_elem(32'habcdef01,64'h8001200);
 status=m32.read_one_elem(v32,64'h1200);if(status||v32!==32'h12345678)$fatal(1,"width32 low alias");
 status=m32.read_one_elem(v32,64'h8001200);if(status||v32!==32'habcdef01)$fatal(1,"width32 high alias");
 m128=new("bank128");m128.init(33559072,0);
 status=m128.write_one_elem(128'h12345678abcdef01aa55xxzz11223344,64'h1200);
 status=m128.write_one_elem(128'hffeeddccbbaa99887766554433221100,64'h2001200);
 status=m128.read_one_elem(v128,64'h1200);if(status||v128!==128'h12345678abcdef01aa55xxzz11223344)$fatal(1,"width128 low/4state");
 status=m128.read_one_elem(v128,64'h2001200);if(status||v128!==128'hffeeddccbbaa99887766554433221100)$fatal(1,"width128 high alias");
 $fclose(fd);$display("BANK_MEMORY_UNIT_PASS pairs=512 widths=8,32,128 bulk=2 bounds=negative,end,over4GiB offset=97 four_state=preserved");$finish;
end
endmodule
'''
 (E/'bank_memory_tb.sv').write_text(tb)
 plan=dict(state='FROZEN_SIMULATOR_MEMORY_FIX_ENTRY',scope='Only isolated file_agent/mem_model.sv storage; no RTL/HLS/quality changes',
  original_model_sha256=sha(OLD),bank_elements=1048576,allocation='lazy separate class-owned arrays',
  semantics=['int depth/offset and original range checks retained','unwritten in-range reads remain X with warning and success status','negative/end/high longint addresses rejected before indexing','four-state stored data retained','read_elems/write_elems unchanged'],
  test='512 alias pairs; crossbank bulk and partial OOB; offset/zero depth; 32/128bit storage; X/Z',
  source_sha256={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in E.iterdir() if p.is_file()},
  prerequisites_for_preview='Actual unit PASS plus independent event replay; full input SHA/readback preflight required',
  automatic_next_stage=False,board='NOT_RUN')
 (R/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
 archive=R/'entry.tar.gz'
 with tarfile.open(archive,'w:gz') as t:
  for p in list(E.iterdir())+[R/'PLAN.json']:t.add(p,arcname=str(p.relative_to(ROOT)))
 print(json.dumps(dict(state=plan['state'],archive=str(archive),sha256=sha(archive))))
if __name__=='__main__':main()
