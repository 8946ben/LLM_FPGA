set module [file dirname [file normalize [info script]]]
set mode csim
if {[info exists ::env(LMH4_ROUTE_MODE)]} {set mode $::env(LMH4_ROUTE_MODE)}
if {$mode ni {csim csynth cosim}} {error "bad mode"}
set run router_$mode
if {[info exists ::env(LMH4_ROUTE_RUN)]} {set run $::env(LMH4_ROUTE_RUN)}
if {![regexp {^[a-zA-Z0-9_-]+$} $run]} {error "bad run name"}
set build [file join $module build $run]
file mkdir $build
cd $build
if {[file exists hls]} {error "Preserve existing run"}
open_project hls
set_top lm_head_v4_router
set flags "-I[file join $module include] -I[file join $module src] -std=c++11 -ffp-contract=off -fno-fast-math"
add_files [file join $module src lm_head_v4_router.cpp] -cflags $flags
add_files -tb [file join $module tests router_csim.cpp] -cflags $flags
open_solution solution1
set_part {xczu9eg-ffvb1156-2-i}
create_clock -period 5 -name default
set_clock_uncertainty 1.350
config_interface -m_axi_addr64
if {$mode eq "csim"} {csim_design -O -argv [file join $module reports router_fixture_20261021]} else {
    csynth_design
    if {$mode eq "cosim"} {cosim_design -rtl verilog -tool xsim -trace_level none -argv "[file join $module reports router_fixture_20261021] --rtl"}
}
puts "M14_V4_ROUTER_$mode=PASS"
exit
