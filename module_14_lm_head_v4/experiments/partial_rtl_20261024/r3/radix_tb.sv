`timescale 1ns/1ps
module radix_tb;
reg clk=0,rst=1,start=0; always #2.5 clk=~clk;
wire done,idle,ready;wire [31:0] result;
wire  inner_AWVALID;
wire  inner_AWREADY;
wire [63:0] inner_AWADDR;
wire [0:0] inner_AWID;
wire [31:0] inner_AWLEN;
wire [2:0] inner_AWSIZE;
wire [1:0] inner_AWBURST;
wire [1:0] inner_AWLOCK;
wire [3:0] inner_AWCACHE;
wire [2:0] inner_AWPROT;
wire [3:0] inner_AWQOS;
wire [3:0] inner_AWREGION;
wire [0:0] inner_AWUSER;
wire  inner_WVALID;
wire  inner_WREADY;
wire [127:0] inner_WDATA;
wire [15:0] inner_WSTRB;
wire  inner_WLAST;
wire [0:0] inner_WID;
wire [0:0] inner_WUSER;
wire  inner_ARVALID;
wire  inner_ARREADY;
wire [63:0] inner_ARADDR;
wire [0:0] inner_ARID;
wire [31:0] inner_ARLEN;
wire [2:0] inner_ARSIZE;
wire [1:0] inner_ARBURST;
wire [1:0] inner_ARLOCK;
wire [3:0] inner_ARCACHE;
wire [2:0] inner_ARPROT;
wire [3:0] inner_ARQOS;
wire [3:0] inner_ARREGION;
wire [0:0] inner_ARUSER;
wire  inner_RVALID;
wire  inner_RREADY;
wire [127:0] inner_RDATA;
wire  inner_RLAST;
wire [0:0] inner_RID;
wire [11:0] inner_RFIFONUM;
wire [0:0] inner_RUSER;
wire [1:0] inner_RRESP;
wire  inner_BVALID;
wire  inner_BREADY;
wire [1:0] inner_BRESP;
wire [0:0] inner_BID;
wire [0:0] inner_BUSER;
wire  bus_AWVALID;
wire  bus_AWREADY;
wire [64 - 1:0] bus_AWADDR;
wire [1 - 1:0] bus_AWID;
wire [7:0] bus_AWLEN;
wire [2:0] bus_AWSIZE;
wire [1:0] bus_AWBURST;
wire [1:0] bus_AWLOCK;
wire [3:0] bus_AWCACHE;
wire [2:0] bus_AWPROT;
wire [3:0] bus_AWQOS;
wire [3:0] bus_AWREGION;
wire [1 - 1:0] bus_AWUSER;
wire  bus_WVALID;
wire  bus_WREADY;
wire [128 - 1:0] bus_WDATA;
wire [16 - 1:0] bus_WSTRB;
wire  bus_WLAST;
wire [1 - 1:0] bus_WID;
wire [1 - 1:0] bus_WUSER;
wire  bus_ARVALID;
wire  bus_ARREADY;
wire [64 - 1:0] bus_ARADDR;
wire [1 - 1:0] bus_ARID;
wire [7:0] bus_ARLEN;
wire [2:0] bus_ARSIZE;
wire [1:0] bus_ARBURST;
wire [1:0] bus_ARLOCK;
wire [3:0] bus_ARCACHE;
wire [2:0] bus_ARPROT;
wire [3:0] bus_ARQOS;
wire [3:0] bus_ARREGION;
wire [1 - 1:0] bus_ARUSER;
wire  bus_RVALID;
wire  bus_RREADY;
wire [128 - 1:0] bus_RDATA;
wire  bus_RLAST;
wire [1 - 1:0] bus_RID;
wire [1 - 1:0] bus_RUSER;
wire [1:0] bus_RRESP;
wire  bus_BVALID;
wire  bus_BREADY;
wire [1:0] bus_BRESP;
wire [1 - 1:0] bus_BID;
wire [1 - 1:0] bus_BUSER;
assign inner_RLAST=0; assign inner_RID=0; assign inner_RUSER=0; assign inner_RRESP=0; assign inner_BID=0; assign inner_BUSER=0; assign inner_BRESP=0;
assign bus_RUSER=0; assign bus_BUSER=0;
lm_head_v4_partial_proto_p_anonymous_namespace_radix_candidates dut(.ap_clk(clk),
.ap_rst(rst),
.ap_start(start),
.ap_done(done),
.ap_idle(idle),
.ap_ready(ready),
.m_axi_meta_AWVALID(inner_AWVALID),
.m_axi_meta_AWREADY(inner_AWREADY),
.m_axi_meta_AWADDR(inner_AWADDR),
.m_axi_meta_AWID(inner_AWID),
.m_axi_meta_AWLEN(inner_AWLEN),
.m_axi_meta_AWSIZE(inner_AWSIZE),
.m_axi_meta_AWBURST(inner_AWBURST),
.m_axi_meta_AWLOCK(inner_AWLOCK),
.m_axi_meta_AWCACHE(inner_AWCACHE),
.m_axi_meta_AWPROT(inner_AWPROT),
.m_axi_meta_AWQOS(inner_AWQOS),
.m_axi_meta_AWREGION(inner_AWREGION),
.m_axi_meta_AWUSER(inner_AWUSER),
.m_axi_meta_WVALID(inner_WVALID),
.m_axi_meta_WREADY(inner_WREADY),
.m_axi_meta_WDATA(inner_WDATA),
.m_axi_meta_WSTRB(inner_WSTRB),
.m_axi_meta_WLAST(inner_WLAST),
.m_axi_meta_WID(inner_WID),
.m_axi_meta_WUSER(inner_WUSER),
.m_axi_meta_ARVALID(inner_ARVALID),
.m_axi_meta_ARREADY(inner_ARREADY),
.m_axi_meta_ARADDR(inner_ARADDR),
.m_axi_meta_ARID(inner_ARID),
.m_axi_meta_ARLEN(inner_ARLEN),
.m_axi_meta_ARSIZE(inner_ARSIZE),
.m_axi_meta_ARBURST(inner_ARBURST),
.m_axi_meta_ARLOCK(inner_ARLOCK),
.m_axi_meta_ARCACHE(inner_ARCACHE),
.m_axi_meta_ARPROT(inner_ARPROT),
.m_axi_meta_ARQOS(inner_ARQOS),
.m_axi_meta_ARREGION(inner_ARREGION),
.m_axi_meta_ARUSER(inner_ARUSER),
.m_axi_meta_RVALID(inner_RVALID),
.m_axi_meta_RREADY(inner_RREADY),
.m_axi_meta_RDATA(inner_RDATA),
.m_axi_meta_RLAST(inner_RLAST),
.m_axi_meta_RID(inner_RID),
.m_axi_meta_RFIFONUM(inner_RFIFONUM),
.m_axi_meta_RUSER(inner_RUSER),
.m_axi_meta_RRESP(inner_RRESP),
.m_axi_meta_BVALID(inner_BVALID),
.m_axi_meta_BREADY(inner_BREADY),
.m_axi_meta_BRESP(inner_BRESP),
.m_axi_meta_BID(inner_BID),
.m_axi_meta_BUSER(inner_BUSER),
.workspace(64'h400000ff0),
.ap_return(result));
lm_head_v4_partial_proto_meta_m_axi #(
    .CONSERVATIVE( 1 ),
    .USER_MAXREQS( 5 ),
    .MAX_READ_BURST_LENGTH( 128 ),
    .MAX_WRITE_BURST_LENGTH( 128 ),
    .C_M_AXI_ID_WIDTH( 1 ),
    .C_M_AXI_ADDR_WIDTH( 64 ),
    .C_M_AXI_DATA_WIDTH( 128 ),
    .C_M_AXI_AWUSER_WIDTH( 1 ),
    .C_M_AXI_ARUSER_WIDTH( 1 ),
    .C_M_AXI_WUSER_WIDTH( 1 ),
    .C_M_AXI_RUSER_WIDTH( 1 ),
    .C_M_AXI_BUSER_WIDTH( 1 ),
    .C_USER_VALUE( 0 ),
    .C_PROT_VALUE( 0 ),
    .C_CACHE_VALUE( 3 ),
    .USER_RFIFONUM_WIDTH( 12 ),
    .USER_DW( 128 ),
    .USER_AW( 64 ),
    .NUM_READ_OUTSTANDING( 16 ),
    .NUM_WRITE_OUTSTANDING( 16 ))
adapter(
    .AWVALID(bus_AWVALID),
    .AWREADY(bus_AWREADY),
    .AWADDR(bus_AWADDR),
    .AWID(bus_AWID),
    .AWLEN(bus_AWLEN),
    .AWSIZE(bus_AWSIZE),
    .AWBURST(bus_AWBURST),
    .AWLOCK(bus_AWLOCK),
    .AWCACHE(bus_AWCACHE),
    .AWPROT(bus_AWPROT),
    .AWQOS(bus_AWQOS),
    .AWREGION(bus_AWREGION),
    .AWUSER(bus_AWUSER),
    .WVALID(bus_WVALID),
    .WREADY(bus_WREADY),
    .WDATA(bus_WDATA),
    .WSTRB(bus_WSTRB),
    .WLAST(bus_WLAST),
    .WID(bus_WID),
    .WUSER(bus_WUSER),
    .ARVALID(bus_ARVALID),
    .ARREADY(bus_ARREADY),
    .ARADDR(bus_ARADDR),
    .ARID(bus_ARID),
    .ARLEN(bus_ARLEN),
    .ARSIZE(bus_ARSIZE),
    .ARBURST(bus_ARBURST),
    .ARLOCK(bus_ARLOCK),
    .ARCACHE(bus_ARCACHE),
    .ARPROT(bus_ARPROT),
    .ARQOS(bus_ARQOS),
    .ARREGION(bus_ARREGION),
    .ARUSER(bus_ARUSER),
    .RVALID(bus_RVALID),
    .RREADY(bus_RREADY),
    .RDATA(bus_RDATA),
    .RLAST(bus_RLAST),
    .RID(bus_RID),
    .RUSER(bus_RUSER),
    .RRESP(bus_RRESP),
    .BVALID(bus_BVALID),
    .BREADY(bus_BREADY),
    .BRESP(bus_BRESP),
    .BID(bus_BID),
    .BUSER(bus_BUSER),
    .ACLK(clk),
    .ARESET(rst),
    .ACLK_EN(1'b1),
    .I_ARVALID(inner_ARVALID),
    .I_ARREADY(inner_ARREADY),
    .I_ARADDR(inner_ARADDR),
    .I_ARLEN(inner_ARLEN),
    .I_RVALID(inner_RVALID),
    .I_RREADY(inner_RREADY),
    .I_RDATA(inner_RDATA),
    .I_RFIFONUM(inner_RFIFONUM),
    .I_AWVALID(inner_AWVALID),
    .I_AWREADY(inner_AWREADY),
    .I_AWADDR(inner_AWADDR),
    .I_AWLEN(inner_AWLEN),
    .I_WVALID(inner_WVALID),
    .I_WREADY(inner_WREADY),
    .I_WDATA(inner_WDATA),
    .I_WSTRB(inner_WSTRB),
    .I_BVALID(inner_BVALID),
    .I_BREADY(inner_BREADY)
);
axi_stall_memory #(.BASE(64'h400000000),.N(79331)) mem(.clk(clk),.rst(rst),.AWVALID(bus_AWVALID),.AWREADY(bus_AWREADY),.AWADDR(bus_AWADDR),.AWID(bus_AWID),.AWLEN(bus_AWLEN),.AWSIZE(bus_AWSIZE),.AWBURST(bus_AWBURST),.WVALID(bus_WVALID),.WREADY(bus_WREADY),.WDATA(bus_WDATA),.WSTRB(bus_WSTRB),.WLAST(bus_WLAST),.BVALID(bus_BVALID),.BREADY(bus_BREADY),.BID(bus_BID),.BRESP(bus_BRESP),.ARVALID(bus_ARVALID),.ARREADY(bus_ARREADY),.ARADDR(bus_ARADDR),.ARID(bus_ARID),.ARLEN(bus_ARLEN),.ARSIZE(bus_ARSIZE),.ARBURST(bus_ARBURST),.RVALID(bus_RVALID),.RREADY(bus_RREADY),.RDATA(bus_RDATA),.RLAST(bus_RLAST),.RID(bus_RID),.RRESP(bus_RRESP));
reg [127:0] expected[0:79331-1];
integer ci,j,cycles;string fixtures;string outputs; string inpath,outpath;reg [31:0] ks[0:13-1];
initial begin
if(!$value$plusargs("fixtures=%s",fixtures))$fatal(1,"fixtures missing");
if(!$value$plusargs("outputs=%s",outputs))$fatal(1,"outputs missing");
ks[0]=4109;
ks[1]=4110;
ks[2]=4109;
ks[3]=4109;
ks[4]=4109;
ks[5]=4109;
ks[6]=4110;
ks[7]=4109;
ks[8]=4109;
ks[9]=4110;
ks[10]=4110;
ks[11]=4096;
ks[12]=4110;
repeat(8)@(negedge clk);rst=0;
for(ci=0;ci<13;ci=ci+1)begin
inpath=$sformatf("%s/%02d_in.hex",fixtures,ci);outpath=$sformatf("%s/%02d_out.hex",fixtures,ci);
$readmemh(inpath,mem.data);$readmemh(outpath,expected);
@(negedge clk);start=1;cycles=0;
while(done!==1'b1)begin @(negedge clk);cycles=cycles+1;if(cycles>2100000)$fatal(1,"selector timeout case%0d",ci);end
start=0;
if(result!==ks[ci])$fatal(1,"K case%0d got%0d expected%0d",ci,result,ks[ci]);
repeat(100)@(negedge clk);
for(j=0;j<79331;j=j+1)if(mem.data[j]!==expected[j])$fatal(1,"memory case%0d beat%0d got%032h expected%032h",ci,j,mem.data[j],expected[j]);
$writememh($sformatf("%s/actual_%02d.hex",outputs,ci),mem.data);
$display("RADIX_CASE_PASS index=%0d K=%0d cycles=%0d read=%0d write=%0d ARstall=%0d Rgap=%0d AWstall=%0d Wstall=%0d Bdelay=%0d boundary=%0d",ci,result,cycles,mem.rdbeats,mem.wrbeats,mem.arstall,mem.rgap,mem.awstall,mem.wstall,mem.bdelay,mem.boundary);
end
if(mem.arstall==0||mem.rgap==0||mem.awstall==0||mem.wstall==0||mem.bdelay==0||mem.boundary==0)$fatal(1,"coverage absent");
$display("RADIX_RTL_ALL_PASS cases=13 source=frozen_r3_with_original_AXI_adapter");$finish;
end
endmodule
