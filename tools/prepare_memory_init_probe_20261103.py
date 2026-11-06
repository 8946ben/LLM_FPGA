from pathlib import Path
import hashlib,json,tarfile
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';E=M/'experiments/memory_init_probe_20261103';R=M/'reports/memory_init_probe_20261103_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 E.mkdir(exist_ok=True);R.mkdir(exist_ok=True);assert not (R/'PLAN.json').exists()
 tb='''`timescale 1ns/1ps
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
 $fwrite(fd,"%0d,%0d,%0d,%0d,%0d\\n",mode,phase,count,rss,checksum);$fflush(fd);
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
'''
 (E/'allocation_tb.sv').write_text(tb)
 s=(ROOT/'tools/run_memory_allocation_micro_20261103.py').read_text().replace('experiments/memory_allocation_micro_20261103_r2','experiments/memory_init_probe_20261103').replace('reports/memory_allocation_micro_20261103_r2','reports/memory_init_probe_20261103_r1').replace('.cache/memory_allocation_micro_20261103_r2','.cache/memory_init_probe_20261103_r1')
 a=s.index(" (V/'micro.prj').write_text(");b=s.index(" state={'state'",a)
 s=s[:a]+''' shutil.copytree(OLD/'file_agent',V/'file_agent')
 assert sha(V/'file_agent/mem_model.sv')=='d1f50d29b2ed6636fd30a3d4420ec54f45a766410970162aba2056519d84a711'
 (V/'micro.prj').write_text('sv xil_defaultlib "file_agent/file_agent_pkg.sv"\\nsv xil_defaultlib "allocation_tb.sv"\\n')
 pattern=bytes((i*17+3)&255 for i in range(256))
 words=['0x'+pattern[i:i+16][::-1].hex()+'\\n' for i in range(0,256,16)]
 block=''.join(words)
 with (V/'c.lm_head_v4_partial_proto.autotvin_weights.dat').open('w') as f:
  f.write('[[[runtime]]]\\n[[transaction]] 0\\n')
  for i in range(67108864//256):f.write(block)
  f.write('[[/transaction]]\\n[[[/runtime]]]\\n')
 for name,value in [('tiled_offset.dat',0),('canonical_offset.dat',33554432)]:
  (V/name).write_text('[[[runtime]]]\\n[[transaction]] 0\\n0x%016x\\n[[/transaction]]\\n[[[/runtime]]]\\n'%value)
'''+s[b:]
 a=s.index("  run('elaborate',");b=s.index("  state.update(state='TOOL_PASS",a)
 s=s[:a]+'''  for linking in ['default','all']:
   opt=' -Oenable_linking_all_libraries' if linking=='all' else ''
   snap='init_'+linking
   run('elaborate_'+linking,'/tools/Xilinx/Vivado/2022.2/bin/xelab xil_defaultlib.allocation_tb -prj micro.prj -L uvm -L xil_defaultlib -i ./file_agent -relax -debug all'+opt+' -s '+snap)
   for mode in [0,1]:run('mode_'+linking+'_'+str(mode),'/tools/Xilinx/Vivado/2022.2/bin/xsim '+snap+' -runall -testplusarg MODE='+str(mode))
'''+s[b:]
 compile(s,'run_init.py','exec');(E/'run_micro.py').write_text(s)
 plan={'state':'FROZEN_EXACT_STORAGE_ENTRY_INIT_CONTROL','sources':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in E.iterdir() if p.is_file()},'bytes':67108864,
 'cases':['base direct helper','actual original virtual subclass entry'],'linking':['default','enable_linking_all_libraries'],
 'scope':'Exact qualified model, no DUT, all64MiB bytes verified','full_m14':'NOT_RUN','board':'NOT_RUN','automatic_next_stage':False}
 (R/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
 with tarfile.open(R/'entry.tar.gz','w:gz') as a:
  for p in list(E.iterdir())+[R/'PLAN.json']:a.add(p,arcname=str(p.relative_to(ROOT)))
 print(json.dumps({'archive':str(R/'entry.tar.gz'),'sha256':sha(R/'entry.tar.gz')}))
if __name__=='__main__':main()
