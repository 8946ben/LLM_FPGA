"""Original 2093 events plus paired packed/byte/page semantics."""
from pathlib import Path
import json,hashlib,tarfile,shutil
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';NAME='memory_burst_semantics_20261103_r4'
E=M/'experiments'/NAME;R=M/'reports'/NAME;C=M/'experiments/memory_burst_model_20261103_r3';S=M/'reports/memory_growth_diagnosis_20261103_r1/sources'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 E.mkdir(exist_ok=True);R.mkdir(exist_ok=True);assert not (R/'PLAN.json').exists()
 shutil.copy2(C/'mem_model.sv',E/'mem_model.sv');shutil.copy2(M/'experiments/memory_full_loader_small_20261103_r1/memory_probe_pkg.sv',E/'memory_probe_pkg.sv')
 original=(S/'file_agent/mem_model.sv').read_text();original=original.replace('`ifndef MEM_MODEL__SV','').replace('`define MEM_MODEL__SV','');assert original.rstrip().endswith('`endif');original=original.rstrip()[:-len('`endif')]
 reference='package reference_memory_pkg;\nimport uvm_pkg::*;\nimport file_agent_pkg::file_read_agent;\nimport file_agent_pkg::file_write_agent;\n`include "uvm_macros.svh"\n'+original+'\nendpackage\n'
 (E/'reference_memory_pkg.sv').write_text(reference)
 legacy=(M/'experiments/sim_memory_bank_20261026/bank_memory_tb.sv').read_text().replace('module bank_memory_tb;','module legacy_tb;').replace('$finish;','$display("ALLOCATION_MICRO_PASS legacy2093");$finish;')
 (E/'legacy_tb.sv').write_text(legacy)
 paired=r'''`timescale 1ns/1ps
`include "uvm_macros.svh"
module pair_tb;
import uvm_pkg::*;
file_agent_pkg::mem_model#(8) m;
reference_memory_pkg::mem_model#(8) r;
file_agent_pkg::mem_model_pages_with_diffofst#(128,8) np;
reference_memory_pkg::mem_model_pages_with_diffofst#(128,8) rp;
file_agent_pkg::mem_model#(32) m32;
reference_memory_pkg::mem_model#(32) r32;
file_agent_pkg::mem_model#(128) m128;
reference_memory_pkg::mem_model#(128) r128;
integer fd,wfd,sa,sb,compare_expression_differences=0;
integer lengths[$]='{0,1,15,16,17,31,32,63};
longint positions[$]='{0,1,15,16,31,1048560,1048570,1048575,1048576,536870896,536870912,545685472,545685495,545685504,-7,4294967296};
class warning_audit extends uvm_report_catcher;
 int old_count[string],new_count[string];
 function new(string name="warning_audit");super.new(name);endfunction
 virtual function action_e catch();
  string id,msg;id=get_id();msg=get_message();
  if(get_severity()==UVM_WARNING && id.len()>=3)begin
   if(id.substr(0,2)=="ref")begin old_count[msg]++;$fwrite(wfd,"ref\t%s\n",msg);return CAUGHT;end
   if(id.substr(0,2)=="new")begin new_count[msg]++;$fwrite(wfd,"new\t%s\n",msg);return CAUGHT;end
  end
  return THROW;
 endfunction
endclass
warning_audit catcher;
function automatic logic[7:0] datum(input integer i,input integer seed);
 if(i%19==3)return 8'hxz;if(i%19==7)return 8'hzz;if(i%19==11)return 8'hxx;return ((i+seed)*17+3)&255;
endfunction
task automatic reset8(input int depth,input int offset);
 m.init(depth,offset);r.init(depth,offset);$fwrite(fd,"I,8,%0d,%0d\n",depth,offset);
endtask
task automatic put_range(input longint addr,input integer n,input integer seed);
 logic[7:0] q[$];integer a,b;
 for(int j=0;j<n;j++)q.push_back(datum(j,seed));
 a=m.write_elems(q,addr);b=r.write_elems(q,addr);if(a!=b || m.is_rd!==r.is_rd)$fatal(1,"paired bulk write");
 for(int j=0;j<n;j++)$fwrite(fd,"W,8,%016h,%b\n",addr+j,q[j]);
 $fwrite(fd,"WE,8,%016h,%0d,%0d\n",addr,n,a);
endtask
task automatic get_range(input longint addr,input integer n);
 logic[7:0] a[$],b[$];integer ra,rb;
 ra=m.read_elems(a,addr,n);rb=r.read_elems(b,addr,n);
 if(ra!=rb || a.size()!=b.size() || a.size()!=n || m.is_rd!==r.is_rd)$fatal(1,"paired read status/flag");
 for(int j=0;j<n;j++)begin
  if(a[j]!==b[j])$fatal(1,"paired read bits");$fwrite(fd,"R,8,%016h,%b\n",addr+j,a[j]);
 end
 $fwrite(fd,"RE,8,%016h,%0d,%0d,%0d\n",addr,n,ra,m.is_rd);
endtask
task automatic packed_write(input longint addr,input integer seed);
 logic[127:0] word128;logic[7:0] q[$];integer a,b;bit valid;
 valid=(m.depth>=16 && addr-m.offset>=0 && addr-m.offset<=m.depth-16 && ((addr-m.offset)&15)==0);
 for(int j=0;j<16;j++)begin word128[j*8+:8]=datum(j,seed);q.push_back(datum(j,seed));end
 a=m.write_packed16(word128,addr);
 if(valid)begin
  b=r.write_elems(q,addr);if(a!=0 || b!=0)$fatal(1,"packed write valid");
  for(int j=0;j<16;j++)$fwrite(fd,"W,8,%016h,%b\n",addr+j,q[j]);$fwrite(fd,"WE,8,%016h,16,0\n",addr);
 end else begin if(a!=1)$fatal(1,"packed reject");$fwrite(fd,"PERR,8,%016h,%0d\n",addr,a);end
endtask
task automatic packed_read(input longint addr);
 logic[127:0] word128;logic[7:0] q[$],actual_byte,reference_byte;integer a,b;bit valid,old_flag,direct_result,copied_result;
 old_flag=m.is_rd;valid=(m.depth>=16 && addr-m.offset>=0 && addr-m.offset<=m.depth-16 && ((addr-m.offset)&15)==0);
 a=m.read_packed16(word128,addr);
 if(addr==113)$display("PACKED_DEBUG_BEFORE_REF addr=%0d status=%0d word=%h",addr,a,word128);
 if(valid)begin
  b=r.read_elems(q,addr,16);if(a!=0 || b!=0 || m.is_rd!==r.is_rd)$fatal(1,"packed read valid");
  for(int j=0;j<16;j++)begin
   actual_byte=word128[j*8+:8];reference_byte=q[j];
   direct_result=(word128[j*8+:8]!==q[j]);copied_result=(actual_byte!==reference_byte);
   if(direct_result!=copied_result)begin
    compare_expression_differences++;if(compare_expression_differences<=3)$display("CASE_COMPARE_DIAGNOSTIC addr=%0d j=%0d direct=%0d copied=%0d actual=%b reference=%b",addr,j,direct_result,copied_result,actual_byte,reference_byte);
   end
   if(copied_result)begin $display("PACKED_MISMATCH addr=%0d j=%0d word=%h got=%b reference=%b qsize=%0d",addr,j,word128,actual_byte,reference_byte,q.size());$fatal(1,"packed read bits");end
   $fwrite(fd,"R,8,%016h,%b\n",addr+j,actual_byte);
  end
  $fwrite(fd,"RE,8,%016h,16,0,%0d\n",addr,m.is_rd);
 end else begin
  if(a!=1 || word128!==128'hxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx || m.is_rd!==old_flag)$fatal(1,"packed read rejected bits/flag");
  $fwrite(fd,"PRERR,8,%016h,%0d\n",addr,a);
 end
endtask
task automatic pipe_cases();
 logic[7:0] q[$],a[$],b[$];longint addresses[$];integer n;
 np=new("newpage");rp=new("refpage");np.whole_page_size=384;rp.whole_page_size=384;
 np.init_pages(1,128,0);rp.init_pages(1,128,0);np.min_offset=4096;rp.min_offset=4096;
 np.pages[0].set_name("newp");rp.pages[0].set_name("refp");$fwrite(fd,"I,8,128,0\n");
 for(int c=0;c<5;c++)begin
  q.delete();addresses.delete();n=(c==3)?3:32;
  for(int j=0;j<n;j++)begin
   q.push_back(datum(j,c));
   case(c)
    0:addresses.push_back(4096+j);
    1:addresses.push_back(4096+j*2);
    2:addresses.push_back(4096+31-j);
    3:addresses.push_back(4096+((j==1)?200:j));
    4:addresses.push_back(4096+120+j);
   endcase
  end
  np.write_elems_pipepage(q,addresses);rp.write_elems_pipepage(q,addresses);
  for(int j=0;j<n;j++)$fwrite(fd,"W,8,%016h,%b\n",addresses[j]-4096,q[j]);
  np.read_elems_pipepage(a,4096,128);rp.read_elems_pipepage(b,4096,128);
  if(a.size()!=128 || b.size()!=128 || np.pages[0].is_rd!==rp.pages[0].is_rd)$fatal(1,"page read status");
  for(int j=0;j<128;j++)begin if(a[j]!==b[j])$fatal(1,"page read bits");$fwrite(fd,"R,8,%016h,%b\n",64'(j),a[j]);end
  $fwrite(fd,"RE,8,0000000000000000,128,0,1\n");
 end
 a.delete();b.delete();a.push_back(8'h66);b.push_back(8'h66);
 np.read_elems_pipepage(a,5000,1);rp.read_elems_pipepage(b,5000,1);
 if(a.size()!=1 || b.size()!=1 || a[0]!==8'h66 || b[0]!==8'h66)$fatal(1,"no page changed caller queue");
 $display("BURST_NO_PAGE_CONTROL_PASS");
endtask
task automatic generic_cases();
 logic[31:0] q32[$],out32[$],actual32,reference32;logic[127:0] q128[$],out128[$],actual128,reference128;logic[511:0] word32;logic[2047:0] word128;longint addr;
 m32=new("new32");r32=new("ref32");m32.init(134217760);r32.init(134217760);$fwrite(fd,"I,32,134217760,0\n");
 m128=new("new128");r128=new("ref128");m128.init(33554464);r128.init(33554464);$fwrite(fd,"I,128,33554464,0\n");
 for(int c=0;c<2;c++)begin
  q32.delete();q128.delete();
  for(int j=0;j<16;j++)begin q32.push_back((32'h12xxzz34)^j^c);q128.push_back((128'h12345678abcdef01aa55xxzz11223344)^j^c);end
  for(int j=0;j<16;j++)begin word32[j*32+:32]=q32[j];word128[j*128+:128]=q128[j];end
  addr=(c==0)?0:134217728;sa=m32.write_packed16(word32,addr);sb=r32.write_elems(q32,addr);if(sa||sb)$fatal(1,"generic32 write");
  for(int j=0;j<16;j++)$fwrite(fd,"W,32,%016h,%b\n",addr+j,q32[j]);$fwrite(fd,"WE,32,%016h,16,0\n",addr);
  sa=m32.read_packed16(word32,addr);sb=r32.read_elems(out32,addr,16);if(sa||sb)$fatal(1,"generic32 read");
  for(int j=0;j<16;j++)begin actual32=word32[j*32+:32];reference32=out32[j];if(actual32!==reference32)$fatal(1,"generic32 bits");$fwrite(fd,"R,32,%016h,%b\n",addr+j,actual32);end
  $fwrite(fd,"RE,32,%016h,16,0,1\n",addr);
  addr=(c==0)?0:33554432;sa=m128.write_packed16(word128,addr);sb=r128.write_elems(q128,addr);if(sa||sb)$fatal(1,"generic128 write");
  for(int j=0;j<16;j++)$fwrite(fd,"W,128,%016h,%b\n",addr+j,q128[j]);$fwrite(fd,"WE,128,%016h,16,0\n",addr);
  sa=m128.read_packed16(word128,addr);sb=r128.read_elems(out128,addr,16);if(sa||sb)$fatal(1,"generic128 read");
  for(int j=0;j<16;j++)begin actual128=word128[j*128+:128];reference128=out128[j];if(actual128!==reference128)$fatal(1,"generic128 bits");$fwrite(fd,"R,128,%016h,%b\n",addr+j,actual128);end
  $fwrite(fd,"RE,128,%016h,16,0,1\n",addr);
 end
endtask
initial begin
 fd=$fopen("burst_events.csv","w");wfd=$fopen("warning_events.tsv","w");if(!fd || !wfd)$fatal(1,"event open");
 catcher=new();uvm_report_cb::add(null,catcher);m=new("new8");r=new("ref8");reset8(545685504,97);
 get_range(97,16);packed_read(113);packed_write(97,0);packed_read(97);
 for(int p=0;p<positions.size();p++)for(int l=0;l<lengths.size();l++)begin put_range(positions[p]+97,lengths[l],p+l);get_range(positions[p]+97,lengths[l]);end
 for(int i=0;i<512;i++)begin
  packed_write(97+64'(i)*4096,i);packed_write(97+64'(i)*4096+64'h20000000,i+1000);
  packed_read(97+64'(i)*4096);packed_read(97+64'(i)*4096+64'h20000000);
 end
 packed_write(98,1);packed_read(98);packed_write(545685504+97-8,1);packed_read(545685504+97-8);
 reset8(17,97);put_range(97,17,5);get_range(96,19);packed_write(97,9);packed_read(97);packed_read(113);
 reset8(0,0);get_range(0,1);packed_write(0,0);packed_read(0);
 reset8(31,0);put_range(0,31,3);m.init(31);r.init(31);$fwrite(fd,"I,8,31,0\n");get_range(0,31);
 pipe_cases();generic_cases();
 if(catcher.old_count.num()!=catcher.new_count.num())$fatal(1,"warning distinct mismatch");
 foreach(catcher.old_count[msg])if(catcher.old_count[msg]!=catcher.new_count[msg])$fatal(1,"warning frequency mismatch");
 $fclose(fd);$fclose(wfd);$display("CASE_COMPARE_DIAGNOSTIC_TOTAL count=%0d",compare_expression_differences);$display("ALLOCATION_MICRO_PASS burst_semantics alias_pairs=512 widths=8,32,128 four_state=1 pages=1");$finish;
end
endmodule
'''
 (E/'pair_tb.sv').write_text(paired)
 s=(ROOT/'tools/run_memory_allocation_micro_20261103.py').read_text().replace('memory_allocation_micro_20261103_r2',NAME)
 s=s.replace("assert not (M/'reports/full_bank_cosim_20261102_r2/ACTIVE.lock').exists()", "assert not (M/'reports/full_bank_cosim_20261102_r2/ACTIVE.lock').exists()\n assert not list((M/'reports').glob('memory_*/ACTIVE.lock'))")
 begin=s.index(" V.mkdir();shutil.copytree(OLD/'axivip'");end=s.index(" state={'state':",begin)
 s=s[:begin]+''' V.mkdir();shutil.copytree(OLD/'file_agent',V/'file_agent')
 shutil.copy2(E/'mem_model.sv',V/'file_agent/mem_model.sv')
 for n in ['legacy_tb.sv','pair_tb.sv','memory_probe_pkg.sv','reference_memory_pkg.sv']:shutil.copy2(E/n,V/n)
 (V/'micro.prj').write_text('sv xil_defaultlib "memory_probe_pkg.sv"\\nsv xil_defaultlib "file_agent/file_agent_pkg.sv"\\nsv xil_defaultlib "reference_memory_pkg.sv"\\nsv xil_defaultlib "legacy_tb.sv"\\nsv xil_defaultlib "pair_tb.sv"\\n')
'''+s[end:]
 s=s.replace("shutil.copy2(V/'allocation_samples.csv',d/'allocation_samples.csv')", "\n   for n in (['memory_events.csv'] if phase=='mode_legacy' else ['burst_events.csv','warning_events.tsv']):shutil.copy2(V/n,d/n)")
 begin=s.index("  run('elaborate',");end=s.index("  state.update(state='TOOL_PASS",begin)
 s=s[:begin]+'''  for name in ['pair']:
   run('elaborate_'+name,'/tools/Xilinx/Vivado/2022.2/bin/xelab xil_defaultlib.'+name+'_tb -prj micro.prj -L uvm -L xil_defaultlib -i ./file_agent -relax -debug all -s '+name+'_unit')
   run('mode_'+name,'/tools/Xilinx/Vivado/2022.2/bin/xsim '+name+'_unit -runall')
'''+s[end:]
 compile(s,'unit_runner.py','exec');(E/'run_micro.py').write_text(s)
 plan={'state':'FROZEN_BURST_MODEL_SEMANTICS_COMPARISON','sources':{str(x.relative_to(ROOT)).replace('\\','/'):sha(x) for x in E.iterdir() if x.is_file()},'model_sha256':sha(E/'mem_model.sv'),'reference_model_sha256':sha(S/'file_agent/mem_model.sv'),'tests':['original2093','paired_bulk_offset_bounds_XZ_alias_generic_pipe_warning'],'board':'NOT_RUN','full_m14':'NOT_RUN','automatic_next_stage':False}
 (R/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
 with tarfile.open(R/'entry.tar.gz','w:gz') as t:
  for x in list(E.iterdir())+[R/'PLAN.json']:t.add(x,arcname=str(x.relative_to(ROOT)))
 template=(ROOT/'tools/bootstrap_memory_control_regression_20261103.py').read_text().replace('memory_control_regression_20261103_r1',NAME).replace('816b17f29cea5a90f3562e3fdbeea06a8731b673860b66ec947faf2849cf4948',sha(R/'entry.tar.gz'))
 (ROOT/'tools/bootstrap_memory_burst_semantics_20261103.py').write_text(template)
 print(json.dumps({'archive':str(R/'entry.tar.gz'),'sha256':sha(R/'entry.tar.gz')}))
if __name__=='__main__':main()
