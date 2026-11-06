# Reuse completed synthesis, preserving the Csim/synthesis reports.
set module [file dirname [file normalize [info script]]]
set run selector_csynth_r2
if {[info exists ::env(LMH4_SELECTOR_COSIM_RUN)]} {set run $::env(LMH4_SELECTOR_COSIM_RUN)}
if {![regexp {^[a-zA-Z0-9_-]+$} $run]} {error "bad run"}
cd [file join $module build $run]
if {[file exists hls/solution1/sim/report/lm_head_v4_selector_cosim.rpt]} {error "Preserve existing cosim report"}
open_project hls
open_solution solution1
cosim_design -rtl verilog -tool xsim -trace_level none -argv "$module --rtl"
puts "M14_V4_SELECTOR_FULL_RTL_COSIM=PASS"
exit
