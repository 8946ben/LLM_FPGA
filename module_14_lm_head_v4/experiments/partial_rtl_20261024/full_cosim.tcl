set root [file normalize [file join [file dirname [info script]] .. .. ..]]
set src [file join $root module_14_lm_head_v4 experiments partial_hw_20261024]
set entry [file dirname [info script]]
set build [file join $root .cache p64_rtl_full_r1 hls]
if {![file exists [file join $build solution1 syn verilog lm_head_v4_partial_proto.v]]} {error "Verified r3 synthesis clone missing"}
open_project $build
set_top lm_head_v4_partial_proto
remove_files -tb [file join $src proto_tb.cpp]
set flags "-I$src -I$src/r3/derived -std=c++11 -ffp-contract=off -fno-fast-math"
add_files -tb [file join $entry full_tb.cpp] -cflags $flags
open_solution solution1
# No FIFO resizing, no new synthesis, no arithmetic/parameter change.
cosim_design -rtl verilog -tool xsim -enable_binary_tv -random_stall -enable_dataflow_profiling -trace_level none -O -argv [file join $entry full_fixtures]
puts "PARTIAL_FULL_COSIM_TOOL_PASS"
exit
