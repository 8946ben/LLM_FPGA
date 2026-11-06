`timescale 1ns/1ps
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
