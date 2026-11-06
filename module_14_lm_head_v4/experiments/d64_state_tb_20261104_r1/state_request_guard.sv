`timescale 1ns/1ps
// PREPARED_NOT_COMPILED. Passive full-suite request monitor, never drives DUT.
module d64_state_request_guard(
 input clk,rst_n,active_case,
 input integer frame,current_debug,
 input m_arvalid,m_arready,input[63:0] m_araddr,input[7:0] m_arlen,
 input m_awvalid,m_awready,input[63:0] m_awaddr,input[7:0] m_awlen,
 input w_arvalid,w_arready,input[63:0] w_araddr,input[7:0] w_arlen
);
integer fd,summary_fd,tick=0,j;
integer m_ar[0:11],m_rb[0:11],m_aw[0:11],m_wb[0:11],w_ar[0:11],w_rb[0:11],canonical[0:11];
string out_dir;
logic[64:0] ending;
initial begin
 if(!$value$plusargs("OUT=%s",out_dir))$fatal(1,"STATE_REQUEST_PATH_REQUIRED");
 fd=$fopen({out_dir,"/address_requests.csv"},"w");
 summary_fd=$fopen({out_dir,"/address_summary.csv"},"w");
 if(!fd||!summary_fd)$fatal(1,"STATE_REQUEST_OPEN");
end
task automatic range_check(input logic[63:0] address,input logic[7:0] len,input logic[64:0] low,input logic[64:0] high);
 logic[64:0] end_address;
 if($isunknown({address,len}))$fatal(1,"STATE_REQUEST_UNKNOWN");
 end_address={1'b0,address}+65'd16*({1'b0,len}+9'd1);
 if(address[3:0]!=0||len>=128||{1'b0,address}<low||end_address>high||end_address[64])
  $fatal(1,"STATE_REQUEST_RANGE address=%h len=%0d",address,len);
 if({1'b0,address[11:0]}+13'd16*({1'b0,len}+9'd1)>4096)$fatal(1,"STATE_REQUEST_4K");
endtask
always @(posedge clk)begin
 if(!rst_n)begin
  tick=0;
  for(j=0;j<12;j++)begin m_ar[j]=0;m_rb[j]=0;m_aw[j]=0;m_wb[j]=0;w_ar[j]=0;w_rb[j]=0;canonical[j]=0;end
 end else begin
  tick=tick+1;
  if((m_arvalid&&m_arready)||(m_awvalid&&m_awready)||(w_arvalid&&w_arready))begin
   if($isunknown({active_case,frame})||!active_case||frame<0||frame>11)$fatal(1,"STATE_REQUEST_OUTSIDE_FRAME");
  end
  if(m_arvalid&&m_arready)begin
   range_check(m_araddr,m_arlen,0,1289456);
   ending={1'b0,m_araddr}+65'd16*({1'b0,m_arlen}+9'd1);
   if(frame==5||frame==6)$fatal(1,"STATE_BAD_PARAMETER_META_REQUEST");
   if(frame>=7&&frame<=9&&ending>24368)$fatal(1,"STATE_ERROR_READ_OUTSIDE_METADATA");
   m_ar[frame]++;m_rb[frame]+=m_arlen+1;
   $fwrite(fd,"MR,%0d,%0d,%016h,%0d\n",frame,tick,m_araddr,m_arlen);
  end
  if(m_awvalid&&m_awready)begin
   range_check(m_awaddr,m_awlen,24368,1289456);
   if(frame>=5&&frame<=9)$fatal(1,"STATE_EARLY_ERROR_WRITE_REQUEST");
   m_aw[frame]++;m_wb[frame]+=m_awlen+1;
   $fwrite(fd,"MW,%0d,%0d,%016h,%0d\n",frame,tick,m_awaddr,m_awlen);
  end
  if(w_arvalid&&w_arready)begin
   range_check(w_araddr,w_arlen,0,545685504);
   ending={1'b0,w_araddr}+65'd16*({1'b0,w_arlen}+9'd1);
   if(frame>=5&&frame<=9)$fatal(1,"STATE_EARLY_ERROR_WEIGHT_REQUEST");
   if(w_araddr<273416192&&ending>273416192)$fatal(1,"STATE_WEIGHT_REQUEST_SPANS_TWO_ASSETS");
   if(frame==10&&ending>273416192)$fatal(1,"STATE_PREVIEW_ERROR_CANONICAL_REQUEST");
   w_ar[frame]++;w_rb[frame]+=w_arlen+1;
   if(w_araddr>=273416192)canonical[frame]++;
   $fwrite(fd,"WR,%0d,%0d,%016h,%0d\n",frame,tick,w_araddr,w_arlen);
  end
 end
end
final begin
 for(j=0;j<12;j++)$fwrite(summary_fd,"%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d\n",j,m_ar[j],m_rb[j],m_aw[j],m_wb[j],w_ar[j],w_rb[j],canonical[j]);
 $fclose(fd);$fclose(summary_fd);
end
endmodule
bind d64_state_tb d64_state_request_guard state_request_guard(
 .clk(ap_clk),.rst_n(ap_rst_n),.active_case(active_case),.frame(frame),.current_debug(current_debug),
 .m_arvalid(m_axi_meta_ARVALID),.m_arready(m_axi_meta_ARREADY),.m_araddr(m_axi_meta_ARADDR),.m_arlen(m_axi_meta_ARLEN),
 .m_awvalid(m_axi_meta_AWVALID),.m_awready(m_axi_meta_AWREADY),.m_awaddr(m_axi_meta_AWADDR),.m_awlen(m_axi_meta_AWLEN),
 .w_arvalid(m_axi_weights_ARVALID),.w_arready(m_axi_weights_ARREADY),.w_araddr(m_axi_weights_ARADDR),.w_arlen(m_axi_weights_ARLEN));
