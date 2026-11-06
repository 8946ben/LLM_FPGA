# Linked production-sized C functions; not an integrated HLS/RTL/system proof.
set module [file dirname [file normalize [info script]]]
set run selector_chain_csim_r1
if {[info exists ::env(LMH4_CHAIN_RUN)]} {set run $::env(LMH4_CHAIN_RUN)}
if {![regexp {^[a-zA-Z0-9_-]+$} $run]} {error "bad run"}
file mkdir [file join $module build $run]
cd [file join $module build $run]
if {[file exists hls]} {error "Preserve existing run"}
open_project hls
set_top lm_head_v4_lowrank
set flags "-I[file join $module include] -I[file join $module src] -std=c++11 -ffp-contract=off -fno-fast-math"
add_files [file join $module src selector_chain_csim_unit.cpp] -cflags $flags
add_files -tb [file join $module tests selector_chain_csim.cpp] -cflags $flags
open_solution solution1
set_part {xczu9eg-ffvb1156-2-i}
create_clock -period 5 -name default
csim_design -O -argv "$module [file join $module .. artifacts module14_v2_assets shared_vocab_weight.bf16.bin]"
puts "M14_V4_SELECTOR_CHAIN_CSIM_TCL=PASS"
exit
