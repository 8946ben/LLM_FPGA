# lm_head v4 experimental implementation: 5 ns (200 MHz) closure, PL DDR pin constraints,
# CDC/DRC checks and a packaged XSA/bitstream.
set here [file dirname [file normalize [info script]]]
set_param general.maxThreads 2
set module [file normalize [file join $here .. ..]]
set project_dir [file normalize {D:/program/LLM_FPGA/.cache/e10_bd}]
set out [file join $module reports board_v4_20261021 hardware_r2]
set xdc [file join $module constraints lm_head_v4_ddr4_pins.xdc]
file mkdir $out
open_project [file join $project_dir m14_v4.xpr]
set bd [get_files */m14_v4_system.bd]
open_bd_design $bd
set critical_before [get_msg_config -count -severity {CRITICAL WARNING}]
validate_bd_design
if {[get_msg_config -count -severity {CRITICAL WARNING}] > $critical_before} {
    error "BD validation has critical warnings"
}
file copy -force $bd [file join $out implemented_bd.json]
puts "M14_V4_IMPLEMENTED_BD_VALIDATED=PASS"
set impl [get_runs impl_1]
set impl_status [get_property STATUS $impl]
if {[string match "*Complete*" $impl_status]} {error "Implementation already complete; preserve it"}
if {![string match "*Complete*" [get_property STATUS [get_runs synth_1]]]} {error "Saved synthesis not complete"}
reset_run -from_step place_design impl_1
if {![file exists [file join $project_dir m14_v4.runs impl_1 m14_v4_system_wrapper_opt.dcp]]} {error "Resume lost saved opt checkpoint"}
puts "EXP10_REUSE_OPT_DCP=PASS"
if {![file exists $xdc]} {error "Missing PL DDR pin constraints: $xdc"}
set present [get_files -quiet $xdc]
if {[llength $present] == 0} {
    add_files -fileset constrs_1 -norecurse $xdc
}
set_property used_in_synthesis false [get_files $xdc]
set_property STEPS.PHYS_OPT_DESIGN.IS_ENABLED true $impl
set_property STEPS.POST_ROUTE_PHYS_OPT_DESIGN.IS_ENABLED false $impl
set_property STEPS.PLACE_DESIGN.TCL.PRE [file join $here apply_io_constraints.tcl] $impl
# Pin constraints are implementation-only, so a completed synthesis is reused.
if {![string match "*Complete*" [get_property STATUS [get_runs synth_1]]]} {error "Saved synthesis no longer complete; do not resynthesize automatically"}
launch_runs impl_1 -to_step route_design -jobs 1
wait_on_run impl_1
if {![string match "*Complete*" [get_property STATUS $impl]]} {error "Implementation failed"}
open_run impl_1
write_checkpoint [file join $out post_route.dcp]
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -file [file join $out timing.rpt]
report_utilization -file [file join $out utilization.rpt]
report_io -file [file join $out io.rpt]
set reset [get_ports c0_ddr4_reset_n_0]
set io_file [open [file join $out io_contract.txt] w]
puts $io_file "reset_pin=[get_property PACKAGE_PIN $reset]"
puts $io_file "reset_iostandard=[get_property IOSTANDARD $reset]"
puts $io_file "reset_drive=[get_property DRIVE $reset]"
close $io_file
report_drc -file [file join $out drc.rpt]
report_clocks -file [file join $out clocks.rpt]
report_cdc -details -file [file join $out cdc.rpt]
check_timing -verbose -file [file join $out check_timing.rpt]
report_bus_skew -file [file join $out bus_skew.rpt]
set setup [get_property SLACK [lindex [get_timing_paths -delay_type max -max_paths 1] 0]]
set hold [get_property SLACK [lindex [get_timing_paths -delay_type min -max_paths 1] 0]]
if {$setup < 0 || $hold < 0} {error "Timing failed: setup=$setup hold=$hold"}
close_design
launch_runs impl_1 -to_step write_bitstream -jobs 1
wait_on_run impl_1
if {![string match "*Complete*" [get_property STATUS $impl]]} {error "Bitstream failed"}
open_run impl_1
write_hw_platform -fixed -include_bit -file [file join $out m14_v4_single.xsa]
set bit [file join $project_dir m14_v4.runs impl_1 m14_v4_system_wrapper.bit]
file copy $bit [file join $out m14_v4_system_wrapper.bit]
puts "M14_V4_HARDWARE=PASS setup=$setup hold=$hold"
close_project
exit
