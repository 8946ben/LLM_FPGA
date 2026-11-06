# Isolated candidate exact-head experiment. No released IP or hardware access.
set module [file dirname [file normalize [info script]]]
set mode csim
if {[info exists ::env(LMH4_HLS_MODE)]} {set mode $::env(LMH4_HLS_MODE)}
if {$mode ni {csim csynth}} {error "mode must be csim or csynth"}
set run candidate_$mode
if {[info exists ::env(LMH4_HLS_RUN)]} {set run $::env(LMH4_HLS_RUN)}
if {![regexp {^[a-zA-Z0-9_-]+$} $run]} {error "invalid run name"}
set build [file join $module build $run]
file mkdir $build
cd $build
if {[file exists hls]} {error "Preserve existing HLS project; choose a new run directory"}
open_project hls
set_top lm_head_v4_candidate
set flags "-I[file join $module include] -I[file join $module src] -std=c++11 -ffp-contract=off -fno-fast-math"
add_files [file join $module src lm_head_v4_candidate.cpp] -cflags $flags
add_files -tb [file join $module tests candidate_csim.cpp] -cflags $flags
open_solution solution1
set_part {xczu9eg-ffvb1156-2-i}
create_clock -period 5.000 -name default
set_clock_uncertainty 1.350
config_interface -m_axi_addr64
if {$mode eq "csim"} {
    csim_design -O -argv [file join $module .. artifacts module14_v2_assets]
} else {
    csynth_design
}
puts "M14_V4_CANDIDATE_$mode=PASS"
exit
