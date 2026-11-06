# lm_head v3.1 implementation: 5 ns (200 MHz) closure, PL DDR pin constraints,
# CDC/DRC checks and a packaged XSA/bitstream.
set here [file dirname [file normalize [info script]]]
set module [file normalize [file join $here .. ..]]
set project_dir [file join $module board build m14_board_v31_20261019]
set out [file join $module reports board_v31_20261019 hardware]
set xdc [file join $module constraints lm_head_v31_ddr4_pins.xdc]
file mkdir $out
open_project [file join $project_dir m14_board_v31_20261019.xpr]
set impl [get_runs impl_1]
set impl_status [get_property STATUS $impl]
if {[string match "*Complete*" $impl_status]} {error "Implementation already complete; preserve it"}
reset_runs -from_step phys_opt_design impl_1
if {![file exists $xdc]} {error "Missing PL DDR pin constraints: $xdc"}
set present [get_files -quiet $xdc]
if {[llength $present] == 0} {
    add_files -fileset constrs_1 -norecurse $xdc
}
set_property used_in_synthesis false [get_files $xdc]
set_property STEPS.PHYS_OPT_DESIGN.IS_ENABLED true $impl
set_property STEPS.POST_ROUTE_PHYS_OPT_DESIGN.IS_ENABLED false $impl
# Resume after the saved placed checkpoint. Re-run interrupted phys_opt and route.
if {![string match "*Complete*" [get_property STATUS [get_runs synth_1]]]} {
    reset_run synth_1
    launch_runs synth_1 -jobs 4
    wait_on_run synth_1
}
if {![string match "*Complete*" [get_property STATUS [get_runs synth_1]]]} {error "Synthesis failed"}
launch_runs impl_1 -to_step route_design -jobs 4
wait_on_run impl_1
if {![string match "*Complete*" [get_property STATUS $impl]]} {error "Implementation failed"}
open_run impl_1
write_checkpoint -force [file join $out post_route.dcp]
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -file [file join $out timing.rpt]
report_utilization -file [file join $out utilization.rpt]
report_drc -file [file join $out drc.rpt]
report_clocks -file [file join $out clocks.rpt]
report_cdc -details -file [file join $out cdc.rpt]
check_timing -verbose -file [file join $out check_timing.rpt]
set setup [get_property SLACK [lindex [get_timing_paths -delay_type max -max_paths 1] 0]]
set hold [get_property SLACK [lindex [get_timing_paths -delay_type min -max_paths 1] 0]]
if {$setup < 0 || $hold < 0} {error "Timing failed: setup=$setup hold=$hold"}
close_design
launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1
if {![string match "*Complete*" [get_property STATUS $impl]]} {error "Bitstream failed"}
open_run impl_1
write_hw_platform -fixed -include_bit -file [file join $out m14_v31_single.xsa]
set bit [file join $project_dir m14_board_v31_20261019.runs impl_1 m14_v31_system_wrapper.bit]
file copy $bit [file join $out m14_v31_system_wrapper.bit]
puts "M14_V31_HARDWARE=PASS setup=$setup hold=$hold"
close_project
exit

