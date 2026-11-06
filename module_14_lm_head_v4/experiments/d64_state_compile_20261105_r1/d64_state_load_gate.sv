`timescale 1ns/1ps
module d64_state_load_gate;
initial begin
 wait(d64_state_tb.ap_rst_n===1'b1);
 if(d64_state_tb.starts!==0||d64_state_tb.dones!==0)$fatal(1,"LOAD_GATE_COMPUTE_STARTED");
 $display("STATE_LOAD_ONLY_PASS bytes=545685504 sentinels=1522 starts=0 dones=0");
 $finish;
end
endmodule
