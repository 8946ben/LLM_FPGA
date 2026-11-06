`timescale 1ns/1ps
module allocation_tb;
import uvm_pkg::*;import axi_pkg::*;
integer mode,n,fd,i,j,done_children;
longint unsigned checksum;
int nested[][$];int flat[$];int dyn[];
bit clk=0;always #0.5 clk=~clk;
task automatic sample(input integer count);
 integer procfd,rc,rss;
 string line;
 procfd=$fopen("/proc/self/status","r");if(!procfd)$fatal(1,"proc open");rss=-1;
 while(!$feof(procfd))begin
  rc=$fgets(line,procfd);
  if($sscanf(line,"VmRSS: %d kB",rss)==1)break;
 end
 $fclose(procfd);if(rss<0)$fatal(1,"RSS missing");
 $fwrite(fd,"%0d,%0d,%0d,%0d\n",mode,count,rss,checksum);$fflush(fd);
 $display("ALLOC_SAMPLE mode=%0d count=%0d rss_kib=%0d checksum=%0d",mode,count,rss,checksum);
endtask
initial begin
 if(!$value$plusargs("MODE=%d",mode))mode=0;
 if(!$value$plusargs("N=%d",n))n=100000;
 fd=$fopen("allocation_samples.csv","w");if(!fd)$fatal(1,"sample output");
 nested=new[1];nested[0].push_back(1);flat.push_back(1);dyn=new[1];dyn[0]=1;
 checksum=0;sample(0);
 for(i=0;i<n;i++)begin
  case(mode)
   0:checksum=0;
   1:begin nested[0][0]++;checksum=nested[0][0]-1;end
   2:begin flat[0]++;checksum=flat[0]-1;end
   3:begin dyn[0]++;checksum=dyn[0]-1;end
   4:checksum+=nested[0].size();
   5:checksum+=nested[0][0];
  endcase
  #1;
  if((i+1)%(n/4)==0)sample(i+1);
 end
 if(mode!=0 && checksum!=n)$fatal(1,"counter mismatch");
 #10;

 sample(n+1);$fclose(fd);
 $display("ALLOCATION_MICRO_PASS mode=%0d n=%0d done_children=%0d checksum=%0d",mode,n,done_children,checksum);$finish;
end
endmodule
