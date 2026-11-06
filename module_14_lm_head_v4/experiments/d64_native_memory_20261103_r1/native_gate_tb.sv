`timescale 1ns/1ps
// PREPARED ONLY. Run after the current strong-delay full call independently passes.
// Actual native AXI responses, no M14 outputs or numerical references are injected.
module native_gate_tb;
localparam logic[63:0] BASE=64'h0000000100000000;
localparam integer N=33554436; // Last four words lie beyond the old 512MiB alias.
reg clk=0,rst=1;always #2.5 clk=~clk;
reg AWVALID=0;wire AWREADY;reg[63:0] AWADDR=BASE;reg AWID=0;
reg[7:0] AWLEN=0;reg[2:0] AWSIZE=4;reg[1:0] AWBURST=1;
reg WVALID=0;wire WREADY;reg[127:0] WDATA=0;reg[15:0] WSTRB=0;reg WLAST=0;
wire BVALID;reg BREADY=0;wire BID;wire[1:0] BRESP;
reg ARVALID=0;wire ARREADY;reg[63:0] ARADDR=BASE;reg ARID=0;
reg[7:0] ARLEN=0;reg[2:0] ARSIZE=4;reg[1:0] ARBURST=1;
wire RVALID;reg RREADY=0;wire[127:0] RDATA;wire RLAST,RID;wire[1:0] RRESP;
d64_native_memory #(.BASE(BASE),.N(N),.STORAGE_N(N+1)) dut(.*);
reg ro_write=0;
d64_native_memory #(.N(4),.READ_ONLY(1)) ro(
 .clk(clk),.rst(rst),.AWVALID(ro_write),.AWREADY(),.AWADDR(64'd0),.AWID(1'b0),
 .AWLEN(8'd0),.AWSIZE(3'd4),.AWBURST(2'd1),.WVALID(1'b0),.WREADY(),
 .WDATA(128'd0),.WSTRB(16'd0),.WLAST(1'b0),.BVALID(),.BREADY(1'b0),.BID(),.BRESP(),
 .ARVALID(1'b0),.ARREADY(),.ARADDR(64'd0),.ARID(1'b0),.ARLEN(8'd0),.ARSIZE(3'd4),
 .ARBURST(2'd1),.RVALID(),.RREADY(1'b0),.RDATA(),.RLAST(),.RID(),.RRESP());
integer fd,cycle=0,ar_count=0,r_count=0,aw_count=0,w_count=0,b_count=0;
integer stall_r=0,stall_b=0,stall_w=0,phasefd,err;
string scenario;
reg ready_pattern=0;
logic[127:0] check_word;
always @(negedge clk)if(ready_pattern&&!rst)begin
 RREADY=(cycle%19>=8);BREADY=(cycle%23>=11);
end
always @(posedge clk)begin
 cycle=cycle+1;
 if(!rst)begin
  if(ARVALID&&ARREADY)begin ar_count++;$fwrite(fd,"AR,%0d,%016h,%0d,%0d\n",cycle,ARADDR,ARLEN,ARID);end
  if(RVALID&&RREADY)begin r_count++;$fwrite(fd,"R,%0d,%032h,%0d,%0d,%0d\n",cycle,RDATA,RLAST,RID,RRESP);end
  if(AWVALID&&AWREADY)begin aw_count++;$fwrite(fd,"AW,%0d,%016h,%0d,%0d\n",cycle,AWADDR,AWLEN,AWID);end
  if(WVALID&&WREADY)begin w_count++;$fwrite(fd,"W,%0d,%032h,%04h,%0d\n",cycle,WDATA,WSTRB,WLAST);end
  if(BVALID&&BREADY)begin b_count++;$fwrite(fd,"B,%0d,%0d,%0d\n",cycle,BID,BRESP);end
  if(RVALID&&!RREADY)stall_r++;
  if(BVALID&&!BREADY)stall_b++;
  if(WVALID&&!WREADY)stall_w++;
 end
end
function automatic logic[127:0] pattern(input integer seed,input integer beat);
 logic[127:0] v;
 for(integer lane=0;lane<16;lane++)v[8*lane+:8]=(seed*37+beat*19+lane*11)&255;
 return v;
endfunction
task automatic read_request(input logic[63:0] addr,input integer len,input bit id);
 @(negedge clk);ARADDR=addr;ARLEN=len;ARID=id;ARVALID=1;
 do @(posedge clk);while(ARREADY!==1'b1);
 @(negedge clk);ARVALID=0;
endtask
task automatic read_burst(input logic[63:0] addr,input integer len,input bit id);
 integer target;
 target=r_count+len+1;read_request(addr,len,id);
 wait(r_count==target);@(negedge clk);
 if(dut.ractive||RVALID)$fatal(1,"GATE_NOT_IDLE_AFTER_READ");
endtask
task automatic write_address(input logic[63:0] addr,input integer len,input bit id,input integer gap);
 repeat(gap)@(negedge clk);
 @(negedge clk);AWADDR=addr;AWLEN=len;AWID=id;AWVALID=1;
 do @(posedge clk);while(AWREADY!==1'b1);
 @(negedge clk);AWVALID=0;
endtask
task automatic write_data(input integer len,input integer seed,input logic[15:0] mask,input integer gap);
 repeat(gap)@(negedge clk);
 for(integer beat=0;beat<=len;beat++)begin
  @(negedge clk);WDATA=pattern(seed,beat);WSTRB=mask;WLAST=(beat==len);WVALID=1;
  do @(posedge clk);while(WREADY!==1'b1);
  @(negedge clk);WVALID=0;
 end
endtask
task automatic write_burst(input logic[63:0] addr,input integer len,input bit id,input integer seed,
                          input logic[15:0] mask,input integer awgap,input integer wgap);
 integer target;
 target=b_count+1;
 fork write_address(addr,len,id,awgap);write_data(len,seed,mask,wgap);join
 wait(b_count==target);@(negedge clk);
 if(dut.wactive||dut.resp_pending||BVALID)$fatal(1,"GATE_NOT_IDLE_AFTER_WRITE");
endtask
task automatic memory_sample(input integer epoch);
 lmh_memory_probe_pkg::sample("native_epoch",epoch);
 $fwrite(fd,"EPOCH,%0d,%0d\n",cycle,epoch);$fflush(fd);
endtask
task automatic reset_bus;
 @(negedge clk);rst=1;ARVALID=0;AWVALID=0;WVALID=0;RREADY=0;BREADY=0;
 $fwrite(fd,"RESET,%0d\n",cycle);
 repeat(4)@(negedge clk);
 if(RVALID!==0||BVALID!==0)$fatal(1,"GATE_RESET_RESPONSE_NOT_CLEARED");
 rst=0;
endtask
initial begin
 fd=$fopen("native_wire.csv","w");if(!fd)$fatal(1,"GATE_OPEN_FAILED");
 if(!$value$plusargs("CASE=%s",scenario))scenario="positive";
 repeat(5)@(negedge clk);rst=0;repeat(2)@(negedge clk);
 if(scenario=="positive")begin
  ready_pattern=1;
  // Deliberately different content at offsets differing by exactly512MiB.
  write_burst(BASE,3,0,1,16'hffff,0,12);
  write_burst(BASE+64'h20000000,3,1,9,16'hffff,17,0);
  read_burst(BASE,3,0);read_burst(BASE+64'h20000000,3,1);
  // AXI must split at4KiB; test each side of the1MiB bank boundary separately.
  write_burst(BASE+1048560,0,1,2,16'hffff,0,0);
  write_burst(BASE+1048576,1,0,3,16'hffff,0,0);
  read_burst(BASE+1048560,0,1);read_burst(BASE+1048576,1,0);
  write_burst(BASE+16,0,1,4,16'h5aa5,0,0);read_burst(BASE,3,0);
  write_burst(BASE,0,0,8,16'h0000,0,0);read_burst(BASE,0,1);
  // Unwritten byte lanes remain actual four-state X after a partial write.
  write_burst(BASE+8192,0,1,6,16'h00ff,0,0);read_burst(BASE+8192,0,1);
  // Byte-valid masks must remain unchanged for an all-zero strobe.
  write_burst(BASE+8208,0,0,7,16'h0000,0,0);read_burst(BASE+8208,0,0);
  // Extra allocated guard is not in the exposed logical AXI range.
  err=dut.storage.write_packed16(128'hfedcba98765432100123456789abcdef,16*N);
  if(err)$fatal(1,"GATE_GUARD_INIT");
  read_burst(BASE+16*(N-1),0,1);
  // Simultaneous independent read/write channels, disjoint address regions.
  fork
   read_burst(BASE,3,0);
   write_burst(BASE+16384,7,1,11,16'hffff,3,0);
  join
  read_burst(BASE+16384,7,1);
  // Reset an outstanding held R; storage is preserved and old R is canceled.
  ready_pattern=0;RREADY=0;BREADY=0;read_request(BASE,3,1);
  wait(RVALID===1);repeat(21)@(negedge clk);reset_bus();
  ready_pattern=1;read_burst(BASE,3,1);
  // Reset a held B response after a completed write. Memory must persist.
  ready_pattern=0;BREADY=0;RREADY=1;
  fork write_address(BASE+24576,0,0,0);write_data(0,13,16'hffff,0);join
  wait(BVALID===1);repeat(21)@(negedge clk);reset_bus();
  ready_pattern=1;read_burst(BASE+24576,0,0);
  write_burst(BASE+32768,127,0,21,16'hffff,0,0);
  memory_sample(0);
  for(integer epoch=1;epoch<=4;epoch++)begin
   for(integer rep=0;rep<256;rep++)read_burst(BASE+32768,127,rep%2);
   memory_sample(epoch);
  end
  ready_pattern=0;RREADY=1;BREADY=1;repeat(10)@(negedge clk);
  if(!dut.idle||ro.RVALID||ro.BVALID)$fatal(1,"GATE_NOT_QUIESCENT");
  err=dut.storage.read_packed16(check_word,16*N);
  if(err||check_word!==128'hfedcba98765432100123456789abcdef)$fatal(1,"GATE_END_GUARD_CHANGED");
  if(stall_r<21||stall_b<21||stall_w<5)$fatal(1,"GATE_BACKPRESSURE_NOT_EXERCISED");
  $fwrite(fd,"DONE,%0d,%0d,%0d,%0d,%0d,%0d\n",cycle,ar_count,r_count,aw_count,w_count,b_count);
  $fclose(fd);$display("NATIVE_GATE_PASS case=positive AR=%0d R=%0d AW=%0d W=%0d B=%0d rstall=%0d bstall=%0d wstall=%0d",ar_count,r_count,aw_count,w_count,b_count,stall_r,stall_b,stall_w);
  $finish;
 end else if(scenario=="readonly")begin
  @(negedge clk);ro_write=1;
 end else if(scenario=="wlast")begin
  write_address(BASE,0,0,0);
  @(negedge clk);WVALID=1;WSTRB=16'hffff;WLAST=0;
 end else if(scenario=="xstrobe")begin
  write_address(BASE,0,0,0);
  @(negedge clk);WVALID=1;WSTRB=16'hxxff;WLAST=1;
 end else if(scenario=="ar_stability")begin
  RREADY=0;read_request(BASE,0,0);wait(RVALID===1);
  @(negedge clk);ARVALID=1;ARADDR=BASE;
  @(negedge clk);ARADDR=BASE+16;
 end else if(scenario=="aw_stability")begin
  write_address(BASE,0,0,0);
  @(negedge clk);AWVALID=1;AWADDR=BASE;
  @(negedge clk);AWADDR=BASE+16;
 end else if(scenario=="w_stability")begin
  @(negedge clk);WVALID=1;WDATA=1;WSTRB=16'hffff;WLAST=1;
  @(negedge clk);WDATA=2;
 end else begin
  @(negedge clk);ARVALID=1;ARADDR=BASE;ARLEN=0;ARSIZE=4;ARBURST=1;
  case(scenario)
   "below":ARADDR=BASE-16;
   "end":ARADDR=BASE+16*N;
   "over_end":begin ARADDR=BASE+16*(N-1);ARLEN=1;end
   "high":ARADDR=64'hfffffffffffffff0;
   "alignment":ARADDR=BASE+1;
   "size":ARSIZE=3;
   "burst":ARBURST=0;
   "length":ARLEN=128;
   "4k":begin ARADDR=BASE+4080;ARLEN=1;end
   "xaddr":ARADDR=64'hxxxxxxxxxxxxxxxx;
   "xlen":ARLEN=8'hxx;
   "xsize":ARSIZE=3'bxxx;
   "xburst":ARBURST=2'bxx;
   "xid":ARID=1'bx;
   default:$fatal(1,"GATE_UNKNOWN_CASE %s",scenario);
  endcase
 end
 repeat(100)@(negedge clk);$fatal(1,"GATE_EXPECTED_REJECTION_MISSING case=%s",scenario);
end
initial begin #5000000;$fatal(1,"GATE_WATCHDOG");end
endmodule
