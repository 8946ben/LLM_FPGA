# Dedicated project; preserve accepted 100 MHz and diagnostic 200 MHz results.
set here [file dirname [file normalize [info script]]]
set module [file normalize [file join $here .. ..]]
set project_dir [file join $module board build m14_board200_20261019]
set out [file join $module reports board200_20261019 hardware]
file mkdir $out
open_project [file join $project_dir m14_board200_20261019.xpr]
set impl [get_runs impl_1]
if {[get_property PROGRESS $impl] ne "0%"} {error "Preserve existing implementation"}
set_property STEPS.PHYS_OPT_DESIGN.IS_ENABLED true $impl
set_property STEPS.POST_ROUTE_PHYS_OPT_DESIGN.IS_ENABLED true $impl
launch_runs synth_1 -jobs 4
wait_on_run synth_1
if {![string match "*Complete*" [get_property STATUS [get_runs synth_1]]]} {error "Synthesis failed"}
launch_runs impl_1 -to_step {phys_opt_design (Post-Route)} -jobs 4
wait_on_run impl_1
if {![string match "*Complete*" [get_property STATUS $impl]]} {error "Implementation failed"}
open_run impl_1
write_checkpoint [file join $out post_route.dcp]
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -file [file join $out timing.rpt]
report_utilization -file [file join $out utilization.rpt]
report_drc -file [file join $out drc.rpt]
report_clocks -file [file join $out clocks.rpt]
check_timing -verbose -file [file join $out check_timing.rpt]
set setup [get_property SLACK [lindex [get_timing_paths -delay_type max -max_paths 1] 0]]
set hold [get_property SLACK [lindex [get_timing_paths -delay_type min -max_paths 1] 0]]
if {$setup < 0 || $hold < 0} {error "Timing failed: setup=$setup hold=$hold"}
close_design
launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1
if {![string match "*Complete*" [get_property STATUS $impl]]} {error "Bitstream failed"}
open_run impl_1
write_hw_platform -fixed -include_bit -file [file join $out m14_v2_single.xsa]
set bit [file join $project_dir m14_board200_20261019.runs impl_1 m14_200_system_wrapper.bit]
file copy $bit [file join $out m14_v2_system_wrapper.bit]
puts "M14_BOARD200_HARDWARE=PASS setup=$setup hold=$hold"
close_project
exit
