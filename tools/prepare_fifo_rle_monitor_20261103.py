"""Lossless run-length FIFO traces replace per-cycle retained queues."""
from pathlib import Path
import json,hashlib,tarfile,shutil
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';NAME='fifo_rle_monitor_20261103_r1';E=M/'experiments'/NAME;R=M/'reports'/NAME
H=M/'reports/memory_full_startup_20261103_r1/baseline_headers'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 E.mkdir(exist_ok=True);R.mkdir(exist_ok=True);assert not (R/'PLAN.json').exists()
 original=(H/'df_fifo_monitor.svh').read_text();text=original;changes=[]
 def edit(a,b):
  nonlocal text
  assert text.count(a)==1,a[:100];text=text.replace(a,b);changes.append([a,b])
 edit('        dump_file_agent chan_file;','''        dump_file_agent chan_file;
        integer depth_fd,block_fd;
        longint unsigned depth_run,block_run,depth_samples,block_samples,pushes,pops,clamped_reads;
        logic[31:0] depth_last;
        logic[1:0] block_last;
        bit rle_closed;''')
 edit('        this.max_used_depth = 32\'h0;','''        this.max_used_depth = 32'h0;
        depth_run=0;block_run=0;depth_samples=0;block_samples=0;pushes=0;pops=0;clamped_reads=0;rle_closed=0;
        depth_fd=$fopen({file_inst.file_name,".depth.rle"},"w");
        block_fd=$fopen({file_inst.file_name,".block.rle"},"w");
        if(!depth_fd || !block_fd)$fatal(1,"FIFO_RLE_OPEN_FAILED");''')
 old='''        this.file_dumper.open_file();
        this.file_dumper.dump_2_col(rt_depth_arr,rt_block_arr);
        this.file_dumper.finish_dump();'''
 new='''        if(!rle_closed)begin
            if(depth_run)$fwrite(depth_fd,"%0d,%0d\\n",depth_run,depth_last);
            if(block_run)$fwrite(block_fd,"%0d,%0d\\n",block_run,block_last);
            $fclose(depth_fd);$fclose(block_fd);rle_closed=1;
            $display("DF_FIFO_RLE_SUMMARY file=%s depth_samples=%0d block_samples=%0d end_depth=%0d max_depth=%0d pushes=%0d pops=%0d clamped_reads=%0d",this.file_dumper.file_name,depth_samples,block_samples,this.rt_depth,this.max_used_depth,pushes,pops,clamped_reads);
        end'''
 edit(old,new)
 edit('            this.rt_depth_arr.push_back(this.rt_depth);','''            if(depth_run!=0 && depth_last!==this.rt_depth)begin $fwrite(depth_fd,"%0d,%0d\\n",depth_run,depth_last);depth_run=0;end
            if(depth_run==0)depth_last=this.rt_depth;
            depth_run++;depth_samples++;
            if(in_intf.wr_en===1'b1)pushes++;
            if(in_intf.rd_en===1'b1)pops++;
            if(in_intf.rd_en===1'b1 && in_intf.wr_en!==1'b1 && this.rt_depth==0)clamped_reads++;''')
 # Preserve every branch and metric; change only the destination of its sample.
 for value,indent in [('1','                '),('10','                '),('0','                ')]:
  old=indent+"this.rt_block_arr.push_back(2'b"+value+');'
  code=indent+"begin\n"+indent+"    if(block_run!=0 && block_last!==2'b"+value+")begin $fwrite(block_fd,\"%0d,%0d\\n\",block_run,block_last);block_run=0;end\n"+indent+"    if(block_run==0)block_last=2'b"+value+";\n"+indent+"    block_run++;block_samples++;\n"+indent+'end'
  edit(old,code)
 (E/'df_fifo_monitor.svh').write_text(text)
 (E/'MONITOR_CHANGES.json').write_text(json.dumps({'original_sha256':sha(H/'df_fifo_monitor.svh'),'candidate_sha256':sha(E/'df_fifo_monitor.svh'),'edits':changes,'schema':'separate depth/block CSV run_length,value;original channel status unchanged;lossless expansion to original two columns'},indent=2)+'\n')
 for n in ['dump_file_agent.svh','csv_file_dump.svh','sample_agent.svh','df_fifo_interface.svh']:shutil.copy2(H/n,E/n)
 (E/'df_fifo_monitor_original.svh').write_text(original)
 (E/'df_fifo_monitor_rle.svh').write_text(text.replace('DF_FIFO_MONITOR__SV','DF_FIFO_MONITOR_RLE__SV').replace('class df_fifo_monitor extends','class df_fifo_monitor_rle extends'))
 tb=r'''`timescale 1ns/1ps
`include "dump_file_agent.svh"
`include "csv_file_dump.svh"
`include "sample_agent.svh"
`include "df_fifo_interface.svh"
`include "df_fifo_monitor_original.svh"
`include "df_fifo_monitor_rle.svh"
module monitor_tb;
bit clk=0,rst=1;always #2.5 clk=~clk;
df_fifo_intf iface(clk,rst);
csv_file_dump old_data,old_status,new_data,new_status;
df_fifo_monitor old_monitor;df_fifo_monitor_rle new_monitor;
integer mode,n,fd,gold_depth=0;bit old_done=0,new_done=0;
task automatic sample(input integer cycles);
 integer pf,rc,rss;string line;pf=$fopen("/proc/self/status","r");rss=-1;
 while(!$feof(pf))begin rc=$fgets(line,pf);if($sscanf(line,"VmRSS: %d kB",rss)==1)break;end
 $fclose(pf);if(rss<0)$fatal(1,"RSS missing");
 $fwrite(fd,"%0d,%0d,%0d,%0d,%0d\n",mode,cycles,rss,new_monitor.depth_samples,new_monitor.block_samples);$fflush(fd);
endtask
initial begin
 if(!$value$plusargs("MODE=%d",mode))mode=0;n=(mode==0)?20000:2000000;
 iface.finish=0;iface.wr_en=0;iface.rd_en=0;iface.fifo_rd_block=0;iface.fifo_wr_block=0;
 new_data=new("new_depth.csv");new_status=new("new_status.csv");new_monitor=new(new_data,iface,new_status);
 if(mode==0)begin old_data=new("old_depth.csv");old_status=new("old_status.csv");old_monitor=new(old_data,iface,old_status);end
 else old_done=1;
 fd=$fopen("allocation_samples.csv","w");sample(0);repeat(3)@(posedge clk);
 for(int i=0;i<n;i++)begin
  @(negedge clk);rst=0;
  iface.wr_en=(mode==0)?((i%7<5)&&gold_depth<128):0;
  iface.rd_en=(mode==0)?((i%7>=3)&&gold_depth>0):0;
  iface.fifo_wr_block=(mode==0)?((i%13<3)?1'b1:((i%101==0)?1'bx:1'b0)):0;
  iface.fifo_rd_block=(mode==0)?((i%11==0)?1'b1:1'b0):1;
  iface.finish=(i==n-1);
  if(i==0)begin
   fork
    begin if(mode==0)old_monitor.data_monitor();old_done=1;end
    begin new_monitor.data_monitor();new_done=1;end
   join_none
  end
  @(posedge clk);#0.1;gold_depth+=int'(iface.wr_en)-int'(iface.rd_en);
  if(new_monitor.rt_depth!=gold_depth)$fatal(1,"monitor depth divergence");
  if((i+1)%(n/4)==0)sample(i+1);
 end
 wait(old_done && new_done);
 if(mode==0)old_monitor.output_to_file();new_monitor.output_to_file();
 if(new_monitor.rt_depth_arr.size()!=0 || new_monitor.rt_block_arr.size()!=0)$fatal(1,"retained per-cycle samples");
 if(new_monitor.depth_samples!=n || new_monitor.block_samples!=n || new_monitor.pushes-new_monitor.pops!=new_monitor.rt_depth)$fatal(1,"summary/sample mismatch");
 sample(n+1);$fclose(fd);$display("ALLOCATION_MICRO_PASS fifo_rle mode=%0d samples=%0d retained=0",mode,n);$finish;
end
endmodule
'''
 (E/'monitor_tb.sv').write_text(tb)
 s=(ROOT/'tools/run_memory_allocation_micro_20261103.py').read_text().replace('memory_allocation_micro_20261103_r2',NAME)
 s=s.replace("assert not (M/'reports/full_bank_cosim_20261102_r2/ACTIVE.lock').exists()", "assert not (M/'reports/full_bank_cosim_20261102_r2/ACTIVE.lock').exists()\n assert not list((M/'reports').glob('memory_*/ACTIVE.lock'))\n assert not list((M/'reports').glob('fifo_rle_*/ACTIVE.lock'))")
 a=s.index(" V.mkdir();shutil.copytree(OLD/'axivip'");b=s.index(" state={'state':",a)
 s=s[:a]+''' V.mkdir()
 for p in E.iterdir():
  if p.suffix in ['.sv','.svh']:shutil.copy2(p,V/p.name)
 (V/'micro.prj').write_text('sv xil_defaultlib "monitor_tb.sv"\\n')
'''+s[b:]
 s=s.replace("shutil.copy2(V/'allocation_samples.csv',d/'allocation_samples.csv')", "\n   for n in ['allocation_samples.csv','new_status.csv','new_depth.csv.depth.rle','new_depth.csv.block.rle']+(['old_depth.csv','old_status.csv'] if phase=='mode_0' else []):shutil.copy2(V/n,d/n)")
 s=s.replace('xil_defaultlib.allocation_tb','xil_defaultlib.monitor_tb').replace('-i ./axivip','-i .').replace('for mode in range(6)','for mode in range(2)')
 compile(s,'run_rle.py','exec');(E/'run_micro.py').write_text(s)
 plan={'state':'FROZEN_LOSSLESS_FIFO_RLE_MONITOR','sources':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in E.iterdir() if p.is_file()},'cases':['20000 cycles exact original/new trace and summary','2000000 stable cycles RLE only memory'],
 'original_monitor_sha256':sha(H/'df_fifo_monitor.svh'),'candidate_monitor_sha256':sha(E/'df_fifo_monitor.svh'),'full_m14':'NOT_RUN','board':'NOT_RUN','automatic_next_stage':False}
 (R/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
 with tarfile.open(R/'entry.tar.gz','w:gz') as t:
  for p in list(E.iterdir())+[R/'PLAN.json']:t.add(p,arcname=str(p.relative_to(ROOT)))
 bootstrap=(ROOT/'tools/bootstrap_memory_control_regression_20261103.py').read_text().replace('memory_control_regression_20261103_r1',NAME).replace('816b17f29cea5a90f3562e3fdbeea06a8731b673860b66ec947faf2849cf4948',sha(R/'entry.tar.gz'))
 bootstrap=bootstrap.replace("assert not list((ROOT/'module_14_lm_head_v4/reports').glob('memory_*/ACTIVE.lock'))", "assert not list((ROOT/'module_14_lm_head_v4/reports').glob('memory_*/ACTIVE.lock'))\nassert not list((ROOT/'module_14_lm_head_v4/reports').glob('fifo_rle_*/ACTIVE.lock'))")
 (ROOT/'tools/bootstrap_fifo_rle_monitor_20261103.py').write_text(bootstrap)
 print(json.dumps({'archive':str(R/'entry.tar.gz'),'sha256':sha(R/'entry.tar.gz')}))
if __name__=='__main__':main()
