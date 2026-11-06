open_vcd preview5.vcd
set top /apatb_lm_head_v4_partial_proto_top
log_vcd [get_objects $top/ap_clk]
foreach port {weights_ARVALID weights_ARREADY weights_ARADDR weights_ARLEN weights_RVALID weights_RREADY weights_RDATA weights_RLAST meta_AWVALID meta_AWREADY meta_AWADDR meta_AWLEN meta_WVALID meta_WREADY meta_WDATA meta_WSTRB meta_WLAST} {
 log_vcd [get_objects $top/$port]
}
add_condition -radix unsigned -name stop_after_five_blocks -notrace {/apatb_lm_head_v4_partial_proto_top/weights_ARVALID == 1} {
 set addr [get_value -radix unsigned /apatb_lm_head_v4_partial_proto_top/weights_ARADDR]
 if {$addr >= 9175040} {puts "BANK_PREVIEW5_STOP [current_time]"; stop}
}
run 15 ms
close_vcd
puts "BANK_PREVIEW5_RETURN [current_time]"
quit
