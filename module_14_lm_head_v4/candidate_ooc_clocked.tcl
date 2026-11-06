# Reuse synthesis, replace unqualified OOC r1 clock-source assumption.
set module [file dirname [file normalize [info script]]]
set input [file join $module build candidate_ooc_r1 synthesized.dcp]
set output [file join $module build candidate_ooc_clocked_r2]
if {[file exists $output]} {error "Preserve existing clocked OOC run"}
file mkdir $output
set_param general.maxThreads 4
open_checkpoint $input
if {[llength [get_cells -hierarchical -filter {IS_BLACKBOX == 1}]]} {error "Black box remains"}
if {[llength [get_sites BUFGCE_X0Y0]]!=1} {error "Expected clock reference site absent"}
set_property HD.CLK_SRC BUFGCE_X0Y0 [get_ports ap_clk]
set stream [open [file join $output CLOCK_SOURCE_ASSUMPTION.txt] w]
puts $stream "Standalone OOC reference source: HD.CLK_SRC=BUFGCE_X0Y0 on ap_clk. This is an explicit assumption, not a board clock placement claim."
puts $stream "Clock 5ns, setup uncertainty0.2ns/hold0.05ns from the saved synthesis constraints. External input/output delays are intentionally unqualified."
close $stream
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
puts "M14_V4_CANDIDATE_CLOCKED_OOC_ROUTE=COMPLETE"
close_design
exit
