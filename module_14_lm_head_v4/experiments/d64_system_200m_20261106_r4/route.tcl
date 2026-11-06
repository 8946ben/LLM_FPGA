set_param general.maxThreads 2
# lm_head v4 experimental implementation: 5 ns (200 MHz) closure, PL DDR pin constraints,
# CDC/DRC checks and a packaged XSA/bitstream.
set here [file dirname [file normalize [info script]]]
set module [file normalize [file join $here .. ..]]
set project_dir [file join $module board build m14_d64_200m_r4]
set out [file join $module reports d64_system_200m_20261106_r4 hardware]
set xdc [file join $module experiments d64_system_200m_20261105_r1 lm_head_v4_ddr4_pins.xdc]
file mkdir $out
open_project [file join $project_dir m14_d64_200m.xpr]
set bd [get_files */m14_d64_system.bd]
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
reset_run impl_1
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
if {![string match "*Complete*" [get_property STATUS [get_runs synth_1]]]} {
    # ExplicitsequentialOOCgates:do notask synth_1 toautoqueueallIPs.
    foreach ip_run [lsort [get_runs *_synth_1]] {
        if {![string match "*Complete*" [get_property STATUS $ip_run]]} {
            reset_run $ip_run
            puts "D64_SERIAL_IP_BEGIN=$ip_run"
            launch_runs $ip_run -jobs 1
            wait_on_run $ip_run
            if {![string match "*Complete*" [get_property STATUS $ip_run]]} {error "IP synthesis failed: $ip_run"}
            puts "D64_SERIAL_IP_END=$ip_run"
        }
    }
    reset_run synth_1
    launch_runs synth_1 -jobs 1
    wait_on_run synth_1
}
if {![string match "*Complete*" [get_property STATUS [get_runs synth_1]]]} {error "Synthesis failed"}
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
set setup_paths [get_timing_paths -delay_type max -max_paths 1]
if {[llength $setup_paths] != 1} {error "No constrained setup path"}
set setup [get_property SLACK [lindex $setup_paths 0]]
set hold_paths [get_timing_paths -delay_type min -max_paths 1]
if {[llength $hold_paths] != 1} {error "No constrained hold path"}
set hold [get_property SLACK [lindex $hold_paths 0]]
if {$setup < 0 || $hold < 0} {error "Timing failed: setup=$setup hold=$hold"}
set sf [open [file join $out route_metrics.json] w]
puts $sf [format {{"setup_slack_ns":%.9f,"hold_slack_ns":%.9f,"part":"%s","target_mhz":200,"stage":"ROUTED_NOT_BITSTREAM_NOT_BOARD"}} $setup $hold [get_property PART [current_project]]]
close $sf
report_route_status -file [file join $out route_status.rpt]
report_clock_interaction -file [file join $out clock_interaction.rpt]
puts "M14_D64_ROUTE_RETURNED=PASS setup=$setup hold=$hold"
close_project
exit
