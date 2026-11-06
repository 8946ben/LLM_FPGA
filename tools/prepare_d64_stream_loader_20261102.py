"""Prepare finite differential tests of an explicitly restricted TV streamer."""
from pathlib import Path
import hashlib,json,tarfile
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4'
E=M/'experiments/d64_stream_loader_20261102';R=M/'reports/d64_stream_loader_20261102_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 E.mkdir(exist_ok=True);R.mkdir(exist_ok=True);assert not (R/'PLAN.json').exists()
 base=M/'experiments/d64_resource_recovery_20261102/mem_model.sv'
 text=base.read_text()
 method='''
    // Explicit opt-in: one file, one transaction 0, exact 128-bit hex words.
    // Does not replace the original general-purpose loader.
    function void tvinload_hex128_single(string path, int nbytes, int start_offset=0);
        integer fd, rc, i, k, errors;
        string tok, digits;
        bit [127:0] word128;
        mem_model#(ELE_WIDTH) blk;
        if(DATA_WIDTH!=128 || ELE_WIDTH!=8 || nbytes<0 || nbytes%16!=0)
            `uvm_fatal("stream_format","only aligned byte/128-bit input supported")
        fd=$fopen(path,"r");
        if(fd==0) `uvm_fatal("stream_format","input open failed")
        rc=$fscanf(fd,"%s",tok);if(rc!=1 || tok!="[[[runtime]]]") `uvm_fatal("stream_format","runtime header")
        rc=$fscanf(fd,"%s",tok);if(rc!=1 || tok!="[[transaction]]") `uvm_fatal("stream_format","transaction header")
        rc=$fscanf(fd,"%s",tok);if(rc!=1 || tok!="0") `uvm_fatal("stream_format","transaction must be zero")
        blk=mem_model#(ELE_WIDTH)::type_id::create("streamed page 0");
        blk.init(nbytes,start_offset);pages.push_back(blk);
        for(i=0;i<nbytes/16;i=i+1)begin
            rc=$fscanf(fd,"%s",tok);
            if(rc!=1 || tok.len()!=34 || tok.substr(0,1)!="0x") `uvm_fatal("stream_format","exact 128-bit hex word required")
            for(k=2;k<34;k=k+1)
                if(!((tok[k]>="0" && tok[k]<="9") || (tok[k]>="a" && tok[k]<="f") || (tok[k]>="A" && tok[k]<="F")))
                    `uvm_fatal("stream_format","non-hex digit")
            digits=tok.substr(2,33);rc=$sscanf(digits,"%h",word128);
            if(rc!=1) `uvm_fatal("stream_format","hex parse failed")
            for(k=0;k<16;k=k+1)begin
                errors=blk.write_one_elem((word128>>(k*8)) & 255,i*16+k+start_offset);
                if(errors) `uvm_fatal("stream_format","write outside configured input")
            end
        end
        rc=$fscanf(fd,"%s",tok);if(rc!=1 || tok!="[[/transaction]]") `uvm_fatal("stream_format","transaction length mismatch")
        rc=$fscanf(fd,"%s",tok);if(rc!=1 || tok!="[[[/runtime]]]") `uvm_fatal("stream_format","runtime trailer")
        rc=$fscanf(fd,"%s",tok);if(rc!=-1) `uvm_fatal("stream_format","trailing input")
        $fclose(fd);
        $display("STREAM_LOAD_PASS bytes=%0d offset=%0d words=%0d",nbytes,start_offset,nbytes/16);
    endfunction

'''
 needle='    virtual function tvoutdump_atinit(string fpath );'
 assert text.count(needle)==2  # Base pages and offset-page override.
 (E/'mem_model.sv').write_text(text.replace(needle,method+needle,1))
 # Both paths dump every loaded byte independently; Python checks the formula.
 tb='''`timescale 1ns/1ps
module loader_tb;
import uvm_pkg::*;import file_agent_pkg::*;
mem_model_pages#(128,8) model;
string files[$], path;
integer nbytes, mode, offset, rc, fd, i;
logic[7:0] value;
initial begin
 if(!$value$plusargs("MODE=%d",mode)) mode=0;
 if(!$value$plusargs("NBYTES=%d",nbytes)) nbytes=4194304;
 if(!$value$plusargs("OFFSET=%d",offset)) offset=0;
 if(!$value$plusargs("INPUT=%s",path)) path="input.dat";
 model=new("loader");
 if(mode==0)begin files.push_back(path);model.tvinload_pagechk_atinit(files,nbytes,0,offset);end
 else model.tvinload_hex128_single(path,nbytes,offset);
 if(model.pages.size()!=1)$fatal(1,"page count");
 fd=$fopen("loaded.bin","wb");if(!fd)$fatal(1,"dump open");
 for(i=0;i<nbytes;i=i+1)begin
  rc=model.pages[0].read_one_elem(value,i+offset);
  if(rc || value!==((i*17+3)&255))$fatal(1,"load byte mismatch");
  $fwrite(fd,"%c",value);
 end
 rc=model.pages[0].read_one_elem(value,offset-1);if(!rc || value!==8'hxx)$fatal(1,"low boundary");
 rc=model.pages[0].read_one_elem(value,offset+nbytes);if(!rc || value!==8'hxx)$fatal(1,"high boundary");
 $fclose(fd);$display("LOADER_DIFF_PASS bytes=%0d offset=%0d mode=%0d",nbytes,offset,mode);$finish;
end
endmodule
'''
 (E/'loader_tb.sv').write_text(tb)
 runner=ROOT/'tools/run_d64_stream_loader_20261102.py';(E/'run_qualification.py').write_bytes(runner.read_bytes())
 plan={'state':'FROZEN_FINITE_STREAM_LOADER_DIFFERENTIAL','scope':'Explicit single transaction 128-bit hex loader; original loader retained',
  'baseline_packed_model_sha256':sha(base),'source_sha256':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in E.iterdir() if p.is_file()},
  'tests':['original_4MiB','stream_4MiB','stream_offset97','reject_short','reject_long','reject_badhex','reject_missing_trailer'],
  'full_m14':'NOT_RUN','automatic_next_stage':False,'board':'NOT_RUN'}
 (R/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
 with tarfile.open(R/'entry.tar.gz','w:gz') as a:
  for p in list(E.iterdir())+[R/'PLAN.json']:a.add(p,arcname=str(p.relative_to(ROOT)))
 print(json.dumps({'archive':str(R/'entry.tar.gz'),'sha256':sha(R/'entry.tar.gz')}))
if __name__=='__main__':main()
