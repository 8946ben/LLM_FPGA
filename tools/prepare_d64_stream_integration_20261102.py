"""Keep original offset subclass entry; opt into streaming inside its base call."""
from pathlib import Path
import hashlib,json,tarfile
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4'
E=M/'experiments/d64_stream_integration_20261102_r2';R=M/'reports/d64_stream_integration_20261102_r2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 E.mkdir(exist_ok=True);R.mkdir(exist_ok=True);assert not (R/'PLAN.json').exists()
 original=(M/'experiments/d64_stream_loader_20261102/mem_model.sv').read_text()
 suffix='c.lm_head_v4_partial_proto.autotvin_weights.dat';n=len(suffix)
 branch='''        // Keep virtual subclass entry and its offset initialization unchanged.
        if(DATA_WIDTH==128 && ELE_WIDTH==8 && !ispagechk && offset==0 && depth%16==0 && fpath.size()==1)
            if(fpath[0].len()>=SUFFIX_LENGTH && fpath[0].substr(fpath[0].len()-SUFFIX_LENGTH,fpath[0].len()-1)=="SUFFIX") begin
                tvinload_hex128_single(fpath[0],depth,0);
                return;
            end
'''.replace('SUFFIX_LENGTH',str(n)).replace('SUFFIX',suffix)
 needle='        fr.config_file(fpath, bitw);'
 assert original.count(needle)==1
 model=original.replace(needle,branch+needle)
 subclass='class mem_model_pages_with_diffofst#'
 assert model[model.index(subclass):]==original[original.index(subclass):]
 (E/'mem_model.sv').write_text(model)
 tb='''`timescale 1ns/1ps
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
'''
 (E/'mapping_tb.sv').write_text(tb)
 template=(ROOT/'tools/run_d64_resource_recovery_20261102.py').read_text()
 replacements=[
  ('experiments/d64_resource_recovery_20261102','experiments/d64_stream_integration_20261102_r2'),
  ('reports/d64_resource_recovery_20261102_r1','reports/d64_stream_integration_20261102_r2'),
  ('.cache/d64_resource_recovery_20261102_r1','.cache/d64_stream_integration_20261102_r2'),
  ("case=='byte_bench'","case=='original_mapping'"),
  ("top='bank_memory_tb' if case=='packed_unit' else 'memory_bench_tb'","top='mapping_tb'"),
  ("marker='BANK_MEMORY_UNIT_PASS ' if case=='packed_unit' else 'MEMORY_BENCH_PASS '","marker='MAPPING_INTEGRATION_PASS '"),
  ("if case=='packed_unit':assert any(x.startswith('PACKED_LANES_PASS ') for x in log.splitlines())", "assert (case=='stream_mapping') == any(x.startswith('STREAM_LOAD_PASS ') for x in log.splitlines())"),
  ("name='memory_events.csv' if case=='packed_unit' else 'bench_events.csv'", "name='mapping_bytes.bin'"),
 ]
 for a,b in replacements:assert a in template,a;template=template.replace(a,b)
 anchor="    VICE_NEVER"
 # Tiny exact fixtures, generated before the first xelab invocation.
 needle="            (v/'unit.prj').write_text"
 fixture='''            payload=bytes((i*17+3)&255 for i in range(256))*32
            tv='[[[runtime]]]\\n[[transaction]] 0\\n'+''.join('0x'+payload[i:i+16][::-1].hex()+'\\n' for i in range(0,8192,16))+'[[/transaction]]\\n[[[/runtime]]]\\n'
            for name in ['c.lm_head_v4_partial_proto.autotvin_weights.dat','ordinary.dat']:(v/name).write_text(tv)
            for name,value in [('tiled_offset.dat',0),('canonical_offset.dat',4096)]:
                (v/name).write_text('[[[runtime]]]\\n[[transaction]] 0\\n0x%016x\\n[[/transaction]]\\n[[[/runtime]]]\\n'%value)
'''
 assert needle in template;template=template.replace(needle,fixture+needle)
 compile(template,'run_qualification.py','exec');(E/'run_qualification.py').write_text(template)
 baseline=M/'experiments/d64_resource_recovery_20261102/mem_model.sv'
 plan={'state':'FROZEN_REAL_OFFSET_SUBCLASS_DIFFERENTIAL','baseline_model':str(baseline.relative_to(ROOT)).replace('\\','/'),'baseline_sha256':sha(baseline),
  'source_sha256':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in E.iterdir() if p.is_file()},
  'cases':['original_mapping','stream_mapping'],'subclass_suffix_unchanged':True,'reference_call':'Original virtual tvinload_pagechk_atinit retained',
  'automatic_next_stage':False,'board':'NOT_RUN'}
 (R/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
 with tarfile.open(R/'entry.tar.gz','w:gz') as a:
  for p in list(E.iterdir())+[R/'PLAN.json']:a.add(p,arcname=str(p.relative_to(ROOT)))
 print(json.dumps({'archive':str(R/'entry.tar.gz'),'sha256':sha(R/'entry.tar.gz')}))
if __name__=='__main__':main()
