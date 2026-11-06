`timescale 1ns/1ps
module allocation_tb;
import uvm_pkg::*;import axi_pkg::*;
class original_latency extends axi_latency;
 function new(string name="original_latency");super.new(name);endfunction
 virtual function int get_rdata_lat();
  int delay;
  void'(std::randomize(delay) with {delay dist {0:=8, 0:=1, 256:=1, [0:256]:/2};});
  return delay;
 endfunction
endclass
class compiled_delay;
 rand int delay;
 constraint c {delay dist {0:=8, 0:=1, 256:=1, [0:256]:/2};}
endclass
original_latency original;compiled_delay reused;
integer mode,n,fd,i,j,done_children,delay;
longint unsigned checksum;
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
 original=new("original");reused=new();checksum=0;sample(0);
 for(i=0;i<n;i++)begin
  case(mode)
   0:delay=0;
   1:if(!std::randomize(delay) with {delay dist {0:=8, 0:=1, 256:=1, [0:256]:/2};})$fatal(1,"std random fail");
   2:delay=original.get_rdata_lat();
   3:begin if(!reused.randomize())$fatal(1,"class random fail");delay=reused.delay;end
  endcase
  if(delay<0 || delay>256)$fatal(1,"random bound");checksum+=delay;
  #1;if((i+1)%(n/4)==0)sample(i+1);
 end
 #10;

 sample(n+1);$fclose(fd);
 $display("ALLOCATION_MICRO_PASS mode=%0d n=%0d done_children=%0d checksum=%0d",mode,n,done_children,checksum);$finish;
end
endmodule
