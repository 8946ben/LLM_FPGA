set root [file normalize [file join [file dirname [info script]] .. .. ..]]
set src [file join $root module_14_lm_head_v4 experiments partial_hw_20261024]
if {![info exists ::env(PARTIAL_PROTO_MODE)] || $::env(PARTIAL_PROTO_MODE) ni {csim csynth}} {error "Explicit csim/csynth mode required"}
set mode $::env(PARTIAL_PROTO_MODE)
set build [file join $root .cache p64 $mode]
if {[file exists $build]} {error "Existing run must be preserved"}
file mkdir $build
cd $build
open_project hls
set_top lm_head_v4_partial_proto
set flags "-I$src -I[file join $src derived] -std=c++11 -ffp-contract=off -fno-fast-math"
add_files [file join $src partial_proto.cpp] -cflags $flags
add_files [file join $src derived lm_head_v4_candidate.cpp] -cflags $flags
add_files -tb [file join $src proto_tb.cpp] -cflags $flags
open_solution solution1
set_part {xczu9eg-ffvb1156-2-i}
create_clock -period 5.000 -name default
set_clock_uncertainty 1.350
config_interface -m_axi_addr64
if {$mode eq "csim"} {
    csim_design -O -argv [file join $src fixtures]
} else {
    csynth_design
}
puts "PARTIAL_PROTO_${mode}=PASS"
exit
