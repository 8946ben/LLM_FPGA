`timescale 1ns/1ps
// Diagnostic passive stop only. No compute replacement or full-call PASS.
module d64_prefix_probe;
bit started=0,target_pending=0,finished=0,exported=0;
time start_time,end_time;
string out_dir;
integer fd,err;
logic[127:0] value;
initial if(!$value$plusargs("OUT=%s",out_dir))$fatal(1,"PREFIX_OUT_REQUIRED");
always @(posedge d64_state_tb.ap_clk)begin
 if(d64_state_tb.ap_rst_n)begin
  if(!started && d64_state_tb.dut.ap_start===1'b1)begin
   if(d64_state_tb.frame!=0)$fatal(1,"PREFIX_WRONG_FRAME");
   started=1;start_time=$time;
   fd=$fopen({out_dir,"/compute_start.marker"},"w");if(!fd)$fatal(1,"PREFIX_START_OPEN");
   $fwrite(fd,"%0t\n",start_time);$fclose(fd);
  end
  if(d64_state_tb.m_axi_meta_AWVALID&&d64_state_tb.m_axi_meta_AWREADY&&d64_state_tb.m_axi_meta_AWADDR==64'd44832)begin
   if(!started||target_pending||d64_state_tb.frame!=0)$fatal(1,"PREFIX_TARGET_STATE");
   target_pending<=1;
  end
  if(target_pending&&d64_state_tb.m_axi_meta_BVALID&&d64_state_tb.m_axi_meta_BREADY)begin
   end_time=$time;finished<=1;target_pending<=0;
  end
 end
end
always @(negedge d64_state_tb.ap_clk)if(finished&&!exported)begin
 exported=1;
 if(!d64_state_tb.mem_meta.idle||d64_state_tb.frame!=0||d64_state_tb.seen_done)$fatal(1,"PREFIX_EXPORT_STATE");
 fd=$fopen({out_dir,"/compute_end.marker"},"w");if(!fd)$fatal(1,"PREFIX_END_OPEN");
 $fwrite(fd,"%0t\n",end_time);$fclose(fd);
 fd=$fopen({out_dir,"/prefix_after.hex"},"w");if(!fd)$fatal(1,"PREFIX_DUMP_OPEN");
 for(integer word=0;word<80592;word++)begin
  err=d64_state_tb.mem_meta.storage.read_packed16(value,word*16);
  if(err)$fatal(1,"PREFIX_DUMP_RANGE");
  $fwrite(fd,"%032h\n",value);
 end
 $fclose(fd);
 if(value!==128'hfedcba98765432100123456789abcdef)$fatal(1,"PREFIX_GUARD");
 fd=$fopen({out_dir,"/prefix_metrics.csv"},"w");if(!fd)$fatal(1,"PREFIX_METRICS_OPEN");
 $fwrite(fd,"rows,cycles,meta_reads,meta_writes,weight_reads,starts,dones\n5120,%0d,%0d,%0d,%0d,%0d,%0d\n",(end_time-start_time)/5,d64_state_tb.mem_meta.rdbeats,d64_state_tb.mem_meta.wrbeats,d64_state_tb.mem_weights.rdbeats,d64_state_tb.starts,d64_state_tb.dones);$fclose(fd);
 $display("PREFIX_DIAGNOSTIC_RETURNED rows=5120 complete_call=0");$finish;
end
endmodule
bind d64_state_tb d64_prefix_probe prefix_probe();
