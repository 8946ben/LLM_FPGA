`timescale 1ns/1ps
module memory_bench_tb;
import uvm_pkg::*; import file_agent_pkg::*;
mem_model#(8) m;
logic[7:0] q[$], got;
integer i,j,k,status,fd;
longint unsigned checksum;
initial begin
 fd=$fopen("bench_events.csv","w");
 m=new("bench");m.init(4194304,0);
 $display("BENCH_PHASE init");
 for(i=0;i<4194304;i=i+1)begin
   status=m.write_one_elem((i*17+3)&255,i);
   if(status)$fatal(1,"bench write");
 end
 $display("BENCH_PHASE filled");
 for(k=0;k<3;k=k+1)begin
   checksum=0;
   for(i=0;i<262144;i=i+1)begin
     status=m.read_elems(q,i*16,16);
     if(status || q.size()!=16)$fatal(1,"bench read status");
     for(j=0;j<16;j=j+1)begin
       if(q[j]!==(((i*16+j)*17+3)&255))$fatal(1,"bench data");
       checksum=checksum+q[j];
     end
   end
   if(checksum!==64'd534773760)$fatal(1,"bench checksum");
   $fwrite(fd,"%0d,%0d\n",k,checksum);$fflush(fd);
   $display("BENCH_PHASE epoch=%0d checksum=%0d",k,checksum);
 end
 $fclose(fd);$display("MEMORY_BENCH_PASS bytes=4194304 epochs=3 reads=12582912");$finish;
end
endmodule
