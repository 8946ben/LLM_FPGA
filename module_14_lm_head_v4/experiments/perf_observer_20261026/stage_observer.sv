`timescale 1ns/1ps
// Passive simulation observer. No DUT input is driven; no FPGA throughput claim.
module lmh_stage_observer(
 input clk,rst_n,top_start,top_done,top_idle,
 input [4:0] st_start,st_done,st_idle,
 input w_arvalid,w_arready,w_rvalid,w_rready,
 input m_arvalid,m_arready,m_rvalid,m_rready,
 input m_awvalid,m_awready,m_wvalid,m_wready,
 input [31:0] status
);
integer fd,j,k,frame=0;
string path;
longint unsigned tick=0,begin_tick[0:5];
longint unsigned wrd[0:5],mrd[0:5],mwr[0:5],warstall[0:5],wrback[0:5],marstall[0:5],mawstall[0:5],mwstall[0:5];
bit [5:0] active=0,busy_seen=0;
bit [4:0] prev_st=0;
bit prev_top=0;
initial begin
 if(!$value$plusargs("PROFILE_PATH=%s",path))path="stage_profile.csv";
 fd=$fopen(path,"w");if(fd==0)$fatal(1,"profile output open");
 $fwrite(fd,"frame,stage,cycles,weight_reads,meta_reads,meta_writes,weight_ar_stall,weight_r_backpressure,meta_ar_stall,meta_aw_stall,meta_w_stall,status\n");
 $fflush(fd);
end
task clear_slot(input integer n);
begin
 begin_tick[n]=tick;wrd[n]=0;mrd[n]=0;mwr[n]=0;warstall[n]=0;wrback[n]=0;marstall[n]=0;mawstall[n]=0;mwstall[n]=0;
end endtask
task emit(input integer n,input integer label);
begin
 $fwrite(fd,"%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d\n",frame,label,tick-begin_tick[n],wrd[n],mrd[n],mwr[n],warstall[n],wrback[n],marstall[n],mawstall[n],mwstall[n],status);
 $fflush(fd);
 $display("LMH_STAGE_PROFILE frame=%0d stage=%0d cycles=%0d weight_reads=%0d meta_reads=%0d meta_writes=%0d",frame,label,tick-begin_tick[n],wrd[n],mrd[n],mwr[n]);
end endtask
always @(posedge clk) begin
 if(!rst_n) begin
  tick=0;active=0;busy_seen=0;prev_st=0;prev_top=0;frame=0;
 end else begin
  tick=tick+1;
  if(top_start && !prev_top) begin
   frame=frame+1;active[5]=1;busy_seen[5]=0;clear_slot(5);
  end
  for(j=0;j<5;j=j+1)if(st_start[j] && !prev_st[j])begin
   active[j]=1;busy_seen[j]=0;clear_slot(j);
  end
  for(j=0;j<6;j=j+1)if(active[j])begin
   if(w_rvalid && w_rready)wrd[j]=wrd[j]+1;
   if(m_rvalid && m_rready)mrd[j]=mrd[j]+1;
   if(m_wvalid && m_wready)mwr[j]=mwr[j]+1;
   if(w_arvalid && !w_arready)warstall[j]=warstall[j]+1;
   if(w_rvalid && !w_rready)wrback[j]=wrback[j]+1;
   if(m_arvalid && !m_arready)marstall[j]=marstall[j]+1;
   if(m_awvalid && !m_awready)mawstall[j]=mawstall[j]+1;
   if(m_wvalid && !m_wready)mwstall[j]=mwstall[j]+1;
  end
  // Generated child done is also high while idle: require actual busy first.
  for(j=0;j<5;j=j+1)if(active[j])begin
   if(!st_idle[j])busy_seen[j]=1;
   if(busy_seen[j] && st_done[j])begin emit(j,j);active[j]=0;end
  end
  if(active[5])begin
   if(!top_idle)busy_seen[5]=1;
   if(busy_seen[5] && top_done)begin emit(5,-1);active[5]=0;end
  end
  prev_top=top_start;prev_st=st_start;
 end
end
final begin $fclose(fd);end
endmodule
