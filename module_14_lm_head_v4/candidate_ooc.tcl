# Standalone IP, not the PL-DDR board design or selector integration.
set module [file dirname [file normalize [info script]]]
set rtl [file join $module build candidate_csynth_r2 hls solution1 impl verilog]
set subcore [file join $module build candidate_csynth_r2 hls solution1 impl ip subcore]
set output [file join $module build candidate_ooc_r1]
if {[file exists $output]} {error "Preserve existing OOC run"}
file mkdir $output
create_project candidate_ooc $output -part xczu9eg-ffvb1156-2-i
set_param general.maxThreads 4
add_files [glob $rtl/*.v]
set generators [glob -nocomplain $subcore/*.tcl]
if {[llength $generators]!=4} {error "Expected four generated floating-point subcores"}
foreach generator $generators {source $generator}
set xdc [file join $output candidate_clock.xdc]
set stream [open $xdc w]
puts $stream {create_clock -name ap_clk -period 5.000 [get_ports ap_clk]}
puts $stream {set_clock_uncertainty -setup 0.200 [get_clocks ap_clk]}
puts $stream {set_clock_uncertainty -hold 0.050 [get_clocks ap_clk]}
close $stream
add_files -fileset constrs_1 $xdc
update_compile_order -fileset sources_1
synth_design -top lm_head_v4_candidate -part xczu9eg-ffvb1156-2-i -mode out_of_context
write_checkpoint [file join $output synthesized.dcp]
opt_design
place_design
phys_opt_design
route_design
report_timing_summary -delay_type min_max -max_paths 10 -check_timing_verbose -file [file join $output timing_summary.rpt]
report_timing -delay_type max -max_paths 10 -file [file join $output timing_max.rpt]
report_utilization -file [file join $output utilization.rpt]
report_drc -file [file join $output drc.rpt]
check_timing -verbose -file [file join $output check_timing.rpt]
write_checkpoint [file join $output routed.dcp]
puts "M14_V4_CANDIDATE_OOC_ROUTE=COMPLETE"
close_project
exit
