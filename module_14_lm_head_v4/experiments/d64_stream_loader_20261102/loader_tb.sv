`timescale 1ns/1ps
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
