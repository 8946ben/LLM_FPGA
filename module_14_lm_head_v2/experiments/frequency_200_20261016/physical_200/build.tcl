# Full single-module BD route, no bitstream generation and no board connection.
set here [file normalize [file dirname [info script]]]
set module_dir [file normalize [file join $here .. .. ..]]
set project [file join $module_dir board build m14_v2_200_layers m14_v2_200_layers.xpr]
set out [file join $module_dir reports frequency_200_20261016 reduce_layers physical_200]
file mkdir $out
if {[file exists [file join $out post_route.dcp]]} {error "Preserve prior routed result"}
open_project $project
set synth [get_runs synth_1]
set impl [get_runs impl_1]
if {[get_property PROGRESS $impl] ne "0%"} {error "Preserve existing implementation"}
set_property STEPS.PHYS_OPT_DESIGN.IS_ENABLED true $impl
set_property STEPS.POST_ROUTE_PHYS_OPT_DESIGN.IS_ENABLED true $impl
if {![string match "*Complete*" [get_property STATUS $synth]]} {
    if {[get_property PROGRESS $synth] ne "0%"} {error "Preserve incomplete synthesis; investigate first"}
    launch_runs synth_1 -jobs 4
    wait_on_run synth_1
}
if {![string match "*Complete*" [get_property STATUS $synth]]} {error "Synthesis failed"}
if {![file exists [file join $out post_synth_timing.rpt]]} {
    open_run synth_1
    report_utilization -file [file join $out post_synth_utilization.rpt]
    report_timing_summary -delay_type min_max -file [file join $out post_synth_timing.rpt]
    close_design
}
launch_runs impl_1 -to_step {phys_opt_design (Post-Route)} -jobs 4
wait_on_run impl_1
if {![string match "*Complete*" [get_property STATUS $impl]]} {error "Implementation failed"}
open_run impl_1
write_checkpoint [file join $out post_route.dcp]
report_utilization -file [file join $out post_route_utilization.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose \
    -max_paths 10 -file [file join $out post_route_timing.rpt]
report_drc -file [file join $out post_route_drc.rpt]
report_clocks -file [file join $out clocks.rpt]
check_timing -verbose -file [file join $out check_timing.rpt]
set setup [get_property SLACK [lindex [get_timing_paths -delay_type max -max_paths 1] 0]]
set hold [get_property SLACK [lindex [get_timing_paths -delay_type min -max_paths 1] 0]]
set f [open [file join $out routed_slacks.txt] w]
puts $f "SETUP_SLACK_NS=$setup"
puts $f "HOLD_SLACK_NS=$hold"
puts $f "BOARD_PROGRAMMED=0"
puts $f "BITSTREAM_GENERATED=0"
close $f
puts "M14_200_POST_ROUTE_SETUP_NS=$setup"
puts "M14_200_POST_ROUTE_HOLD_NS=$hold"
if {$setup < 0 || $hold < 0} {error "200 MHz routed setup/hold not met; reports preserved"}
puts "M14_200_ROUTE_COMPLETED_REVIEW_ALL_REPORTS_NOT_BOARD_ACCEPTANCE"
close_project
exit
