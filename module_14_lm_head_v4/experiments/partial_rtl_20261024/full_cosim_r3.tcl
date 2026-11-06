set root [file normalize [file join [file dirname [info script]] .. .. ..]]
set src [file join $root module_14_lm_head_v4 experiments partial_hw_20261024]
set entry [file dirname [info script]]
set build [file join $root .cache p64_rtl_full_r3 hls]
if {![file exists [file join $build solution1 syn verilog lm_head_v4_partial_proto.v]]} {error "Verified r3 synthesis clone missing"}
cd [file dirname $build]
open_project [file tail $build]
set_top lm_head_v4_partial_proto
set flags "-I$src -I$src/r3/derived -std=c++11 -ffp-contract=off -fno-fast-math"
open_solution solution1
# No FIFO resizing, no new synthesis, no arithmetic/parameter change.
cosim_design -rtl verilog -tool xsim -enable_binary_tv -random_stall -enable_dataflow_profiling -trace_level none -O -argv [file join $entry full_fixtures_r3]
puts "PARTIAL_FULL_COSIM_TOOL_PASS"
exit
