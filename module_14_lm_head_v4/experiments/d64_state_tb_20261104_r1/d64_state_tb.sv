`timescale 1ns/1ps
// PREPARED_NOT_SIMULATED. Full unchanged compute RTL, persistent DUT and memories.
// No DUT result is supplied by a reference file. Expectations are checked after return.
module d64_state_tb;
logic  ap_clk;
logic  ap_rst_n;
logic  m_axi_meta_AWVALID;
logic  m_axi_meta_AWREADY;
logic [64 - 1:0] m_axi_meta_AWADDR;
logic [1 - 1:0] m_axi_meta_AWID;
logic [7:0] m_axi_meta_AWLEN;
logic [2:0] m_axi_meta_AWSIZE;
logic [1:0] m_axi_meta_AWBURST;
logic [1:0] m_axi_meta_AWLOCK;
logic [3:0] m_axi_meta_AWCACHE;
logic [2:0] m_axi_meta_AWPROT;
logic [3:0] m_axi_meta_AWQOS;
logic [3:0] m_axi_meta_AWREGION;
logic [1 - 1:0] m_axi_meta_AWUSER;
logic  m_axi_meta_WVALID;
logic  m_axi_meta_WREADY;
logic [128 - 1:0] m_axi_meta_WDATA;
logic [16 - 1:0] m_axi_meta_WSTRB;
logic  m_axi_meta_WLAST;
logic [1 - 1:0] m_axi_meta_WID;
logic [1 - 1:0] m_axi_meta_WUSER;
logic  m_axi_meta_ARVALID;
logic  m_axi_meta_ARREADY;
logic [64 - 1:0] m_axi_meta_ARADDR;
logic [1 - 1:0] m_axi_meta_ARID;
logic [7:0] m_axi_meta_ARLEN;
logic [2:0] m_axi_meta_ARSIZE;
logic [1:0] m_axi_meta_ARBURST;
logic [1:0] m_axi_meta_ARLOCK;
logic [3:0] m_axi_meta_ARCACHE;
logic [2:0] m_axi_meta_ARPROT;
logic [3:0] m_axi_meta_ARQOS;
logic [3:0] m_axi_meta_ARREGION;
logic [1 - 1:0] m_axi_meta_ARUSER;
logic  m_axi_meta_RVALID;
logic  m_axi_meta_RREADY;
logic [128 - 1:0] m_axi_meta_RDATA;
logic  m_axi_meta_RLAST;
logic [1 - 1:0] m_axi_meta_RID;
logic [1 - 1:0] m_axi_meta_RUSER;
logic [1:0] m_axi_meta_RRESP;
logic  m_axi_meta_BVALID;
logic  m_axi_meta_BREADY;
logic [1:0] m_axi_meta_BRESP;
logic [1 - 1:0] m_axi_meta_BID;
logic [1 - 1:0] m_axi_meta_BUSER;
logic  m_axi_weights_AWVALID;
logic  m_axi_weights_AWREADY;
logic [64 - 1:0] m_axi_weights_AWADDR;
logic [1 - 1:0] m_axi_weights_AWID;
logic [7:0] m_axi_weights_AWLEN;
logic [2:0] m_axi_weights_AWSIZE;
logic [1:0] m_axi_weights_AWBURST;
logic [1:0] m_axi_weights_AWLOCK;
logic [3:0] m_axi_weights_AWCACHE;
logic [2:0] m_axi_weights_AWPROT;
logic [3:0] m_axi_weights_AWQOS;
logic [3:0] m_axi_weights_AWREGION;
logic [1 - 1:0] m_axi_weights_AWUSER;
logic  m_axi_weights_WVALID;
logic  m_axi_weights_WREADY;
logic [128 - 1:0] m_axi_weights_WDATA;
logic [16 - 1:0] m_axi_weights_WSTRB;
logic  m_axi_weights_WLAST;
logic [1 - 1:0] m_axi_weights_WID;
logic [1 - 1:0] m_axi_weights_WUSER;
logic  m_axi_weights_ARVALID;
logic  m_axi_weights_ARREADY;
logic [64 - 1:0] m_axi_weights_ARADDR;
logic [1 - 1:0] m_axi_weights_ARID;
logic [7:0] m_axi_weights_ARLEN;
logic [2:0] m_axi_weights_ARSIZE;
logic [1:0] m_axi_weights_ARBURST;
logic [1:0] m_axi_weights_ARLOCK;
logic [3:0] m_axi_weights_ARCACHE;
logic [2:0] m_axi_weights_ARPROT;
logic [3:0] m_axi_weights_ARQOS;
logic [3:0] m_axi_weights_ARREGION;
logic [1 - 1:0] m_axi_weights_ARUSER;
logic  m_axi_weights_RVALID;
logic  m_axi_weights_RREADY;
logic [128 - 1:0] m_axi_weights_RDATA;
logic  m_axi_weights_RLAST;
logic [1 - 1:0] m_axi_weights_RID;
logic [1 - 1:0] m_axi_weights_RUSER;
logic [1:0] m_axi_weights_RRESP;
logic  m_axi_weights_BVALID;
logic  m_axi_weights_BREADY;
logic [1:0] m_axi_weights_BRESP;
logic [1 - 1:0] m_axi_weights_BID;
logic [1 - 1:0] m_axi_weights_BUSER;
logic  s_axi_control_AWVALID;
logic  s_axi_control_AWREADY;
logic [8 - 1:0] s_axi_control_AWADDR;
logic  s_axi_control_WVALID;
logic  s_axi_control_WREADY;
logic [32 - 1:0] s_axi_control_WDATA;
logic [4 - 1:0] s_axi_control_WSTRB;
logic  s_axi_control_ARVALID;
logic  s_axi_control_ARREADY;
logic [8 - 1:0] s_axi_control_ARADDR;
logic  s_axi_control_RVALID;
logic  s_axi_control_RREADY;
logic [32 - 1:0] s_axi_control_RDATA;
logic [1:0] s_axi_control_RRESP;
logic  s_axi_control_BVALID;
logic  s_axi_control_BREADY;
logic [1:0] s_axi_control_BRESP;
logic  interrupt;
lm_head_v4_partial_proto dut(
 .ap_clk(ap_clk),
 .ap_rst_n(ap_rst_n),
 .m_axi_meta_AWVALID(m_axi_meta_AWVALID),
 .m_axi_meta_AWREADY(m_axi_meta_AWREADY),
 .m_axi_meta_AWADDR(m_axi_meta_AWADDR),
 .m_axi_meta_AWID(m_axi_meta_AWID),
 .m_axi_meta_AWLEN(m_axi_meta_AWLEN),
 .m_axi_meta_AWSIZE(m_axi_meta_AWSIZE),
 .m_axi_meta_AWBURST(m_axi_meta_AWBURST),
 .m_axi_meta_AWLOCK(m_axi_meta_AWLOCK),
 .m_axi_meta_AWCACHE(m_axi_meta_AWCACHE),
 .m_axi_meta_AWPROT(m_axi_meta_AWPROT),
 .m_axi_meta_AWQOS(m_axi_meta_AWQOS),
 .m_axi_meta_AWREGION(m_axi_meta_AWREGION),
 .m_axi_meta_AWUSER(m_axi_meta_AWUSER),
 .m_axi_meta_WVALID(m_axi_meta_WVALID),
 .m_axi_meta_WREADY(m_axi_meta_WREADY),
 .m_axi_meta_WDATA(m_axi_meta_WDATA),
 .m_axi_meta_WSTRB(m_axi_meta_WSTRB),
 .m_axi_meta_WLAST(m_axi_meta_WLAST),
 .m_axi_meta_WID(m_axi_meta_WID),
 .m_axi_meta_WUSER(m_axi_meta_WUSER),
 .m_axi_meta_ARVALID(m_axi_meta_ARVALID),
 .m_axi_meta_ARREADY(m_axi_meta_ARREADY),
 .m_axi_meta_ARADDR(m_axi_meta_ARADDR),
 .m_axi_meta_ARID(m_axi_meta_ARID),
 .m_axi_meta_ARLEN(m_axi_meta_ARLEN),
 .m_axi_meta_ARSIZE(m_axi_meta_ARSIZE),
 .m_axi_meta_ARBURST(m_axi_meta_ARBURST),
 .m_axi_meta_ARLOCK(m_axi_meta_ARLOCK),
 .m_axi_meta_ARCACHE(m_axi_meta_ARCACHE),
 .m_axi_meta_ARPROT(m_axi_meta_ARPROT),
 .m_axi_meta_ARQOS(m_axi_meta_ARQOS),
 .m_axi_meta_ARREGION(m_axi_meta_ARREGION),
 .m_axi_meta_ARUSER(m_axi_meta_ARUSER),
 .m_axi_meta_RVALID(m_axi_meta_RVALID),
 .m_axi_meta_RREADY(m_axi_meta_RREADY),
 .m_axi_meta_RDATA(m_axi_meta_RDATA),
 .m_axi_meta_RLAST(m_axi_meta_RLAST),
 .m_axi_meta_RID(m_axi_meta_RID),
 .m_axi_meta_RUSER(m_axi_meta_RUSER),
 .m_axi_meta_RRESP(m_axi_meta_RRESP),
 .m_axi_meta_BVALID(m_axi_meta_BVALID),
 .m_axi_meta_BREADY(m_axi_meta_BREADY),
 .m_axi_meta_BRESP(m_axi_meta_BRESP),
 .m_axi_meta_BID(m_axi_meta_BID),
 .m_axi_meta_BUSER(m_axi_meta_BUSER),
 .m_axi_weights_AWVALID(m_axi_weights_AWVALID),
 .m_axi_weights_AWREADY(m_axi_weights_AWREADY),
 .m_axi_weights_AWADDR(m_axi_weights_AWADDR),
 .m_axi_weights_AWID(m_axi_weights_AWID),
 .m_axi_weights_AWLEN(m_axi_weights_AWLEN),
 .m_axi_weights_AWSIZE(m_axi_weights_AWSIZE),
 .m_axi_weights_AWBURST(m_axi_weights_AWBURST),
 .m_axi_weights_AWLOCK(m_axi_weights_AWLOCK),
 .m_axi_weights_AWCACHE(m_axi_weights_AWCACHE),
 .m_axi_weights_AWPROT(m_axi_weights_AWPROT),
 .m_axi_weights_AWQOS(m_axi_weights_AWQOS),
 .m_axi_weights_AWREGION(m_axi_weights_AWREGION),
 .m_axi_weights_AWUSER(m_axi_weights_AWUSER),
 .m_axi_weights_WVALID(m_axi_weights_WVALID),
 .m_axi_weights_WREADY(m_axi_weights_WREADY),
 .m_axi_weights_WDATA(m_axi_weights_WDATA),
 .m_axi_weights_WSTRB(m_axi_weights_WSTRB),
 .m_axi_weights_WLAST(m_axi_weights_WLAST),
 .m_axi_weights_WID(m_axi_weights_WID),
 .m_axi_weights_WUSER(m_axi_weights_WUSER),
 .m_axi_weights_ARVALID(m_axi_weights_ARVALID),
 .m_axi_weights_ARREADY(m_axi_weights_ARREADY),
 .m_axi_weights_ARADDR(m_axi_weights_ARADDR),
 .m_axi_weights_ARID(m_axi_weights_ARID),
 .m_axi_weights_ARLEN(m_axi_weights_ARLEN),
 .m_axi_weights_ARSIZE(m_axi_weights_ARSIZE),
 .m_axi_weights_ARBURST(m_axi_weights_ARBURST),
 .m_axi_weights_ARLOCK(m_axi_weights_ARLOCK),
 .m_axi_weights_ARCACHE(m_axi_weights_ARCACHE),
 .m_axi_weights_ARPROT(m_axi_weights_ARPROT),
 .m_axi_weights_ARQOS(m_axi_weights_ARQOS),
 .m_axi_weights_ARREGION(m_axi_weights_ARREGION),
 .m_axi_weights_ARUSER(m_axi_weights_ARUSER),
 .m_axi_weights_RVALID(m_axi_weights_RVALID),
 .m_axi_weights_RREADY(m_axi_weights_RREADY),
 .m_axi_weights_RDATA(m_axi_weights_RDATA),
 .m_axi_weights_RLAST(m_axi_weights_RLAST),
 .m_axi_weights_RID(m_axi_weights_RID),
 .m_axi_weights_RUSER(m_axi_weights_RUSER),
 .m_axi_weights_RRESP(m_axi_weights_RRESP),
 .m_axi_weights_BVALID(m_axi_weights_BVALID),
 .m_axi_weights_BREADY(m_axi_weights_BREADY),
 .m_axi_weights_BRESP(m_axi_weights_BRESP),
 .m_axi_weights_BID(m_axi_weights_BID),
 .m_axi_weights_BUSER(m_axi_weights_BUSER),
 .s_axi_control_AWVALID(s_axi_control_AWVALID),
 .s_axi_control_AWREADY(s_axi_control_AWREADY),
 .s_axi_control_AWADDR(s_axi_control_AWADDR),
 .s_axi_control_WVALID(s_axi_control_WVALID),
 .s_axi_control_WREADY(s_axi_control_WREADY),
 .s_axi_control_WDATA(s_axi_control_WDATA),
 .s_axi_control_WSTRB(s_axi_control_WSTRB),
 .s_axi_control_ARVALID(s_axi_control_ARVALID),
 .s_axi_control_ARREADY(s_axi_control_ARREADY),
 .s_axi_control_ARADDR(s_axi_control_ARADDR),
 .s_axi_control_RVALID(s_axi_control_RVALID),
 .s_axi_control_RREADY(s_axi_control_RREADY),
 .s_axi_control_RDATA(s_axi_control_RDATA),
 .s_axi_control_RRESP(s_axi_control_RRESP),
 .s_axi_control_BVALID(s_axi_control_BVALID),
 .s_axi_control_BREADY(s_axi_control_BREADY),
 .s_axi_control_BRESP(s_axi_control_BRESP),
 .interrupt(interrupt)
);
d64_native_memory #(.N(80591),.STORAGE_N(80592),.READ_ONLY(0)) mem_meta(
 .clk(ap_clk),.rst(!ap_rst_n),
 .AWVALID(m_axi_meta_AWVALID),
 .AWREADY(m_axi_meta_AWREADY),
 .AWADDR(m_axi_meta_AWADDR),
 .AWID(m_axi_meta_AWID),
 .AWLEN(m_axi_meta_AWLEN),
 .AWSIZE(m_axi_meta_AWSIZE),
 .AWBURST(m_axi_meta_AWBURST),
 .WVALID(m_axi_meta_WVALID),
 .WREADY(m_axi_meta_WREADY),
 .WDATA(m_axi_meta_WDATA),
 .WSTRB(m_axi_meta_WSTRB),
 .WLAST(m_axi_meta_WLAST),
 .BVALID(m_axi_meta_BVALID),
 .BREADY(m_axi_meta_BREADY),
 .BID(m_axi_meta_BID),
 .BRESP(m_axi_meta_BRESP),
 .ARVALID(m_axi_meta_ARVALID),
 .ARREADY(m_axi_meta_ARREADY),
 .ARADDR(m_axi_meta_ARADDR),
 .ARID(m_axi_meta_ARID),
 .ARLEN(m_axi_meta_ARLEN),
 .ARSIZE(m_axi_meta_ARSIZE),
 .ARBURST(m_axi_meta_ARBURST),
 .RVALID(m_axi_meta_RVALID),
 .RREADY(m_axi_meta_RREADY),
 .RDATA(m_axi_meta_RDATA),
 .RLAST(m_axi_meta_RLAST),
 .RID(m_axi_meta_RID),
 .RRESP(m_axi_meta_RRESP)
);

d64_native_memory #(.N(34105344),.STORAGE_N(34105344),.READ_ONLY(1)) mem_weights(
 .clk(ap_clk),.rst(!ap_rst_n),
 .AWVALID(m_axi_weights_AWVALID),
 .AWREADY(m_axi_weights_AWREADY),
 .AWADDR(m_axi_weights_AWADDR),
 .AWID(m_axi_weights_AWID),
 .AWLEN(m_axi_weights_AWLEN),
 .AWSIZE(m_axi_weights_AWSIZE),
 .AWBURST(m_axi_weights_AWBURST),
 .WVALID(m_axi_weights_WVALID),
 .WREADY(m_axi_weights_WREADY),
 .WDATA(m_axi_weights_WDATA),
 .WSTRB(m_axi_weights_WSTRB),
 .WLAST(m_axi_weights_WLAST),
 .BVALID(m_axi_weights_BVALID),
 .BREADY(m_axi_weights_BREADY),
 .BID(m_axi_weights_BID),
 .BRESP(m_axi_weights_BRESP),
 .ARVALID(m_axi_weights_ARVALID),
 .ARREADY(m_axi_weights_ARREADY),
 .ARADDR(m_axi_weights_ARADDR),
 .ARID(m_axi_weights_ARID),
 .ARLEN(m_axi_weights_ARLEN),
 .ARSIZE(m_axi_weights_ARSIZE),
 .ARBURST(m_axi_weights_ARBURST),
 .RVALID(m_axi_weights_RVALID),
 .RREADY(m_axi_weights_RREADY),
 .RDATA(m_axi_weights_RDATA),
 .RLAST(m_axi_weights_RLAST),
 .RID(m_axi_weights_RID),
 .RRESP(m_axi_weights_RRESP)
);

string root,weight_tv,out_dir;
integer cycle=0,frame=-1,ctrl_fd,metrics_fd,ar_count=0,aw_count=0,raw_write_beats=0;
integer starts=0,dones=0,canonical_read_requests=0,current_debug=1;
bit active_case=0,seen_busy=0,seen_done=0,previous_start=0;
longint unsigned ip_start_cycle=0,ip_done_cycle=0;
file_agent_pkg::mem_model_pages#(128,8) weight_loader;
logic[127:0] word_value;
logic[7:0] byte_value;
integer rc,fd,byte_in;
localparam integer META_BYTES=24368,WS_BEATS=79068;
localparam logic[127:0] GUARD=128'hfedcba98765432100123456789abcdef;
initial ap_clk=0;always #2.5 ap_clk=~ap_clk;
always @(posedge ap_clk)if(ap_rst_n)begin
 cycle=cycle+1;
 if(dut.ap_start===1'b1&&!previous_start)begin
  if(!active_case)$fatal(1,"STATE_START_OUTSIDE_CASE");starts++;ip_start_cycle=cycle;
 end
 previous_start=(dut.ap_start===1'b1);
 if(active_case&&dut.ap_idle===1'b0)seen_busy=1;
 if(active_case&&seen_busy&&dut.ap_done===1'b1&&!seen_done)begin
  dones++;seen_done=1;ip_done_cycle=cycle;
 end
 if(m_axi_weights_ARVALID&&m_axi_weights_ARREADY)begin
  if(!active_case)$fatal(1,"STATE_WEIGHT_AR_OUTSIDE_CASE");
  ar_count++;
  if(m_axi_weights_ARADDR>=273416192)canonical_read_requests++;
 end
 if(m_axi_meta_AWVALID&&m_axi_meta_AWREADY)begin
  if(!active_case||m_axi_meta_AWADDR<META_BYTES)$fatal(1,"STATE_META_WRITE_OUTSIDE_WORKSPACE");
  aw_count++;
 end
 if(m_axi_meta_WVALID&&m_axi_meta_WREADY)begin
  if(mem_meta.wa<META_BYTES)$fatal(1,"STATE_METADATA_OVERWRITE");
  if(mem_meta.wa>=META_BYTES+76997*16 && mem_meta.wa<META_BYTES+79052*16 && m_axi_meta_WSTRB!=0)begin
   raw_write_beats++;
   if(current_debug==0)$fatal(1,"STATE_PRODUCTION_RAW_WRITE");
  end
 end
end
task automatic ctrl_read(input logic[7:0] address,output logic[31:0] value);
 integer waited;
 @(negedge ap_clk);s_axi_control_ARADDR=address;s_axi_control_ARVALID=1;
 waited=0;
 do begin @(posedge ap_clk);waited++;if(waited>10000)$fatal(1,"STATE_CONTROL_AR_TIMEOUT");end while(s_axi_control_ARREADY!==1'b1);
 @(negedge ap_clk);s_axi_control_ARVALID=0;s_axi_control_RREADY=1;
 waited=0;
 do begin @(posedge ap_clk);waited++;if(waited>10000)$fatal(1,"STATE_CONTROL_R_TIMEOUT");end while(s_axi_control_RVALID!==1'b1);
 value=s_axi_control_RDATA;
 if(s_axi_control_RRESP!==2'b00||$isunknown(value))$fatal(1,"STATE_CONTROL_READ_INVALID");
 $fwrite(ctrl_fd,"R,%0d,%0d,%02h,%08h\n",frame,cycle,address,value);
 @(negedge ap_clk);s_axi_control_RREADY=0;
endtask
task automatic ctrl_write(input logic[7:0] address,input logic[31:0] value);
 integer aw_wait,w_wait,b_wait;
 @(negedge ap_clk);s_axi_control_BREADY=1;
 fork
  begin
   s_axi_control_AWADDR=address;s_axi_control_AWVALID=1;aw_wait=0;
   do begin @(posedge ap_clk);aw_wait++;if(aw_wait>10000)$fatal(1,"STATE_CONTROL_AW_TIMEOUT");end while(s_axi_control_AWREADY!==1'b1);
   @(negedge ap_clk);s_axi_control_AWVALID=0;
  end
  begin
   s_axi_control_WDATA=value;s_axi_control_WSTRB=4'hf;s_axi_control_WVALID=1;w_wait=0;
   do begin @(posedge ap_clk);w_wait++;if(w_wait>10000)$fatal(1,"STATE_CONTROL_W_TIMEOUT");end while(s_axi_control_WREADY!==1'b1);
   @(negedge ap_clk);s_axi_control_WVALID=0;
  end
 join
 b_wait=0;
 do begin @(posedge ap_clk);b_wait++;if(b_wait>10000)$fatal(1,"STATE_CONTROL_B_TIMEOUT");end while(s_axi_control_BVALID!==1'b1);
 if(s_axi_control_BRESP!==2'b00)$fatal(1,"STATE_CONTROL_WRITE_INVALID");
 $fwrite(ctrl_fd,"W,%0d,%0d,%02h,%08h\n",frame,cycle,address,value);
 @(negedge ap_clk);s_axi_control_BREADY=0;
endtask
task automatic write_check(input logic[7:0] address,input logic[31:0] value);
 logic[31:0] got;
 ctrl_write(address,value);ctrl_read(address,got);
 if(got!==value)$fatal(1,"STATE_PARAMETER_READBACK address=%h",address);
endtask
task automatic load_meta(input string relative_path);
 integer h,c,e;logic[127:0] v;
 if(!mem_meta.idle||!mem_weights.idle)$fatal(1,"STATE_MUTATE_WHILE_BUS_ACTIVE");
 h=$fopen({root,"/",relative_path},"rb");if(!h)$fatal(1,"STATE_META_OPEN");
 for(integer beat=0;beat<1523;beat++)begin
  for(integer lane=0;lane<16;lane++)begin
   c=$fgetc(h);if(c<0)$fatal(1,"STATE_META_SHORT");v[lane*8+:8]=c;
  end
  e=mem_meta.storage.write_packed16(v,beat*16);if(e)$fatal(1,"STATE_META_LOAD_RANGE");
 end
 if($fgetc(h)!=-1)$fatal(1,"STATE_META_LONG");$fclose(h);
endtask
task automatic dump_memory(input string label,input string suffix);
 integer h,e;logic[127:0] v;
 if(!mem_meta.idle||!mem_weights.idle)$fatal(1,"STATE_DUMP_WHILE_BUS_ACTIVE");
 h=$fopen({out_dir,"/",label,".",suffix,".hex"},"w");if(!h)$fatal(1,"STATE_DUMP_OPEN");
 for(integer beat=0;beat<80592;beat++)begin
  e=mem_meta.storage.read_packed16(v,beat*16);if(e)$fatal(1,"STATE_DUMP_RANGE");
  $fwrite(h,"%032h\n",v);
 end
 $fclose(h);
 e=mem_meta.storage.read_packed16(v,80591*16);if(e||v!==GUARD)$fatal(1,"STATE_END_GUARD_CHANGED");
endtask
task automatic mutate_weight(input integer offset,input logic[15:0] expect_value,input logic[15:0] new_value);
 integer e;logic[7:0] lo,hi;
 if(!mem_meta.idle||!mem_weights.idle)$fatal(1,"STATE_WEIGHT_MUTATE_ACTIVE");
 e=mem_weights.storage.read_one_elem(lo,offset);e+=mem_weights.storage.read_one_elem(hi,offset+1);
 if(e||{hi,lo}!==expect_value)$fatal(1,"STATE_WEIGHT_MUTATION_ORIGINAL");
 e=mem_weights.storage.write_one_elem(new_value[7:0],offset);
 e+=mem_weights.storage.write_one_elem(new_value[15:8],offset+1);
 if(e)$fatal(1,"STATE_WEIGHT_MUTATION_RANGE");
endtask
task automatic run_case(input integer index,input string label,input string input_path,
 input integer debug_value,input integer capacity,input integer expected_status,
 input logic[31:0] expected_token,input logic[31:0] expected_score,input integer expected_k,input logic[31:0] expected_crc,
 input integer injection_offset,input logic[15:0] original_weight);
 logic[31:0] value,status,token,score,count,crc,preview_lo,preview_hi;
 integer first_starts,first_dones,first_mrd,first_mwr,first_wrd,first_canonical,first_raw,waited;
 longint unsigned call_begin,call_end;
 frame=index;current_debug=debug_value;seen_busy=0;seen_done=0;
 load_meta(input_path);dump_memory(label,"before");
 if(injection_offset>=0)mutate_weight(injection_offset,original_weight,16'h7fc0);
 ctrl_read(0,value);
 if((value&32'h85)!=4)$fatal(1,"STATE_NOT_IDLE_BEFORE_CASE");
 for(integer field=0;field<6;field++)begin
  ctrl_read(field==5?8'ha8:8'h54+16*field,value);
  ctrl_read(field==5?8'ha8:8'h54+16*field,value);
  if(value!==0)$fatal(1,"STATE_STALE_OUTPUT_VALID");
 end
 write_check(8'h10,0);write_check(8'h14,0);write_check(8'h1c,0);write_check(8'h20,0);
 write_check(8'h28,273416192);write_check(8'h2c,0);write_check(8'h34,META_BYTES);write_check(8'h38,0);
 write_check(8'h40,capacity);write_check(8'h48,debug_value);
 first_starts=starts;first_dones=dones;first_mrd=mem_meta.rdbeats;first_mwr=mem_meta.wrbeats;
 first_wrd=mem_weights.rdbeats;first_canonical=canonical_read_requests;first_raw=raw_write_beats;
 active_case=1;call_begin=cycle;ctrl_write(0,1);waited=0;
 do begin
  ctrl_read(0,value);waited++;
  if(waited>500000)$fatal(1,"STATE_CASE_DONE_TIMEOUT");
  if(!value[1])repeat(64)@(negedge ap_clk);
 end while(value[1]!==1'b1);
 call_end=cycle;
 if(starts!=first_starts+1||dones!=first_dones+1||!seen_busy||!seen_done)$fatal(1,"STATE_REAL_CALL_NOT_OBSERVED");
 for(integer field=0;field<6;field++)begin
  ctrl_read(field==5?8'ha8:8'h54+16*field,value);if(value!==1)$fatal(1,"STATE_MISSING_OUTPUT_VALID");
  ctrl_read(field==5?8'ha8:8'h54+16*field,value);if(value!==0)$fatal(1,"STATE_OUTPUT_VALID_NOT_CLEARED");
 end
 ctrl_read(8'h50,status);ctrl_read(8'h60,token);ctrl_read(8'h70,score);ctrl_read(8'h80,count);
 ctrl_read(8'h90,crc);ctrl_read(8'ha0,preview_lo);ctrl_read(8'ha4,preview_hi);
 if(status!==expected_status||token!==expected_token||score!==expected_score||count!==expected_k||crc!==expected_crc)
  $fatal(1,"STATE_OUTPUT_MISMATCH case=%s status=%h token=%h score=%h K=%h crc=%h",label,status,token,score,count,crc);
 if({preview_hi,preview_lo}!==(expected_status==0?64'd1220608:64'd0))$fatal(1,"STATE_PREVIEW_COUNT_MISMATCH");
 ctrl_read(0,value);if(value[1]!==0||value[0]!==0||value[7]!==0||value[2]!==1)$fatal(1,"STATE_DONE_NOT_CLEARED_OR_NOT_IDLE");
 waited=0;
 while(!mem_meta.idle||!mem_weights.idle)begin
  @(negedge ap_clk);waited++;if(waited>10000)$fatal(1,"STATE_BUS_DRAIN_TIMEOUT");
 end
 @(negedge ap_clk);active_case=0;
 if(expected_status==0&&mem_weights.rdbeats-first_wrd<=1220608)$fatal(1,"STATE_EXACT_WEIGHT_READ_MISSING");
 if(expected_status!=0&&canonical_read_requests!=first_canonical)$fatal(1,"STATE_ERROR_READ_CANONICAL");
 if(index>=5&&index<=9)begin
  if(mem_weights.rdbeats!=first_wrd||mem_meta.wrbeats!=first_mwr)$fatal(1,"STATE_EARLY_ERROR_SIDE_EFFECT");
  if(index<=6&&mem_meta.rdbeats!=first_mrd)$fatal(1,"STATE_BAD_PARAMETER_READ_META");
 end
 if(debug_value==0&&raw_write_beats!=first_raw)$fatal(1,"STATE_PRODUCTION_RAW_BEATS");
 if(injection_offset>=0)mutate_weight(injection_offset,16'h7fc0,original_weight);
 dump_memory(label,"after");
 $fwrite(metrics_fd,"%0d,%s,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d\n",index,label,debug_value,status,token,score,count,crc,ip_done_cycle-ip_start_cycle,call_end-call_begin,
 mem_meta.rdbeats-first_mrd,mem_meta.wrbeats-first_mwr,mem_weights.rdbeats-first_wrd,canonical_read_requests-first_canonical,raw_write_beats-first_raw,starts);
 $fflush(metrics_fd);$fflush(ctrl_fd);
 $display("STATE_CASE_RETURNED index=%0d label=%s status=%0d K=%0d ip_cycles=%0d",index,label,status,count,ip_done_cycle-ip_start_cycle);
endtask
initial begin
 ap_rst_n=0;
 s_axi_control_AWVALID=0;s_axi_control_AWADDR=0;s_axi_control_WVALID=0;s_axi_control_WDATA=0;s_axi_control_WSTRB=0;
 s_axi_control_ARVALID=0;s_axi_control_ARADDR=0;s_axi_control_RREADY=0;s_axi_control_BREADY=0;
 m_axi_meta_RUSER=0;m_axi_meta_BUSER=0;m_axi_weights_RUSER=0;m_axi_weights_BUSER=0;
 if(!$value$plusargs("ROOT=%s",root)||!$value$plusargs("WEIGHTS_TV=%s",weight_tv)||!$value$plusargs("OUT=%s",out_dir))$fatal(1,"STATE_PATH_ARGUMENTS_REQUIRED");
 ctrl_fd=$fopen({out_dir,"/control_trace.csv"},"w");metrics_fd=$fopen({out_dir,"/case_metrics.csv"},"w");
 if(!ctrl_fd||!metrics_fd)$fatal(1,"STATE_RESULTS_OPEN");
 $fwrite(metrics_fd,"case,label,debug,status,token,score,K,crc,ip_cycles,control_call_cycles,meta_reads,meta_writes,weight_reads,canonical_requests,raw_write_beats,total_starts\n");
 wait(mem_meta.initialized&&mem_weights.initialized);
 weight_loader=new("real_original_full_weight_tv");weight_loader.tvinload_hex128_single(weight_tv,545685504,0);
 if(weight_loader.pages.size()!=1)$fatal(1,"STATE_WEIGHT_PAGE_COUNT");mem_weights.storage=weight_loader.pages[0];
 `include "state_weight_sentinels.svh"
 for(integer beat=0;beat<80591;beat++)begin
  rc=mem_meta.storage.write_packed16(128'ha5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5,beat*16);
  if(rc)$fatal(1,"STATE_INITIAL_META_RANGE");
 end
 rc=mem_meta.storage.write_packed16(GUARD,80591*16);if(rc)$fatal(1,"STATE_INITIAL_GUARD_RANGE");
 repeat(8)@(negedge ap_clk);ap_rst_n=1;repeat(8)@(negedge ap_clk);
 `include "state_schedule.svh"
 if(starts!=12||dones!=12||!mem_meta.idle||!mem_weights.idle)$fatal(1,"STATE_FINAL_COUNTS");
 $fclose(ctrl_fd);$fclose(metrics_fd);$display("D64_STATE_SUITE_RETURNED calls=12 no_inter_call_reset=1");$finish;
end
initial begin #2000000000;$fatal(1,"STATE_SIMULATION_WATCHDOG");end
endmodule
