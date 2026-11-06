`timescale 1ns/1ps
module allocation_tb;
import uvm_pkg::*;import axi_pkg::*;
class plain_packet;
 logic[7:0] data[$];
endclass
plain_packet plain;
axi_transfer packet, source;
integer mode,n,fd,i,j,done_children;
longint unsigned checksum;
bit clk=0;
always #0.5 clk=~clk;
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
 source=new("clone_source");for(j=0;j<16;j=j+1)source.data.push_back(j);
 checksum=0;done_children=0;sample(0);
 for(i=0;i<n;i=i+1)begin
  case(mode)
   0:begin end
   1:begin
    plain=new();for(j=0;j<16;j=j+1)plain.data.push_back((i+j)&255);
    checksum+=plain.data[0];plain=null;
   end
   2,3:begin
    if(mode==2)packet=new("packet");else packet=axi_transfer::type_id::create("packet");
    for(j=0;j<16;j=j+1)packet.data.push_back((i+j)&255);
    checksum+=packet.data[0];packet=null;
   end
   4:begin
    if(!$cast(packet,source.clone()))$fatal(1,"clone type");
    if(packet.data.size()!=16 || packet.data[15]!==15)$fatal(1,"clone data");
    checksum+=packet.data[15];packet=null;
   end
   5:begin fork begin #0.01;done_children++;end join_none end
   default:$fatal(1,"bad mode");
  endcase
  #1;
  if((i+1)%(n/4)==0)sample(i+1);
 end
 #10;
 if(mode==5 && done_children!=n)$fatal(1,"fork children unfinished");
 sample(n+1);$fclose(fd);
 $display("ALLOCATION_MICRO_PASS mode=%0d n=%0d done_children=%0d checksum=%0d",mode,n,done_children,checksum);$finish;
end
endmodule
