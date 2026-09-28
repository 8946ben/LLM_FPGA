# Stage C: synthesize, implement and export the validated AXU9EGB LM Head
# hardware design.  This script never connects to or programs the board.

set script_dir [file normalize [file dirname [info script]]]
set project_dir [file normalize [file join $script_dir "build" "lm_head_axu9eg"]]
set project_file [file join $project_dir "lm_head_axu9eg.xpr"]
set result_dir [file normalize [file join $script_dir "build" "results"]]

file mkdir $result_dir

if {![file exists $project_file]} {
    error "Vivado project is missing; run create_lm_head_axu9eg_bd.tcl first: $project_file"
}

open_project $project_file

set bd_file [get_files "*/lm_head_system.bd"]
set ooc_runs [get_runs -quiet *_synth_1]
if {[llength $ooc_runs] > 0} {
    # 2026-07-25 zb: recover cleanly if a previous Windows child-process
    # launch was interrupted and left OOC runs marked as Running.
    foreach ooc_run $ooc_runs {
        set ooc_status [get_property STATUS $ooc_run]
        if {[string match "*Running*" $ooc_status] ||
            [string match "*Queued*" $ooc_status]} {
            reset_run $ooc_run
        }
    }
    delete_runs $ooc_runs
}
reset_target all $bd_file
generate_target all $bd_file
export_ip_user_files -of_objects $bd_file -sync -force -quiet
create_ip_run $bd_file
reset_run synth_1
reset_run impl_1

launch_runs synth_1 -jobs 4
wait_on_run synth_1
set synth_status [get_property STATUS [get_runs synth_1]]
puts "LMH_STAGE_C_SYNTH_STATUS=$synth_status"
if {![string match "*Complete*" $synth_status]} {
    error "Synthesis did not complete successfully: $synth_status"
}

open_run synth_1
report_utilization -file [file join $result_dir "post_synth_utilization.rpt"]
report_timing_summary -file [file join $result_dir "post_synth_timing_summary.rpt"]

launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1
set impl_status [get_property STATUS [get_runs impl_1]]
puts "LMH_STAGE_C_IMPL_STATUS=$impl_status"
if {![string match "*Complete*" $impl_status]} {
    error "Implementation/bitstream did not complete successfully: $impl_status"
}

open_run impl_1
report_utilization -file [file join $result_dir "post_route_utilization.rpt"]
report_timing_summary -file [file join $result_dir "post_route_timing_summary.rpt"]
report_drc -file [file join $result_dir "post_route_drc.rpt"]

set bit_file [file join $project_dir \
    "lm_head_axu9eg.runs" "impl_1" "lm_head_system_wrapper.bit"]
if {![file exists $bit_file]} {
    error "Implementation completed but bitstream is missing: $bit_file"
}

set xsa_file [file join $result_dir "lm_head_axu9eg.xsa"]
write_hw_platform -fixed -include_bit -force -file $xsa_file
if {![file exists $xsa_file]} {
    error "write_hw_platform completed but XSA is missing: $xsa_file"
}

set timing_paths [get_timing_paths -max_paths 1 -nworst 1]
if {[llength $timing_paths] > 0} {
    set worst_slack [get_property SLACK [lindex $timing_paths 0]]
} else {
    set worst_slack "N/A"
}

puts "LMH_STAGE_C_BUILD=PASS"
puts "LMH_STAGE_C_WORST_SLACK_NS=$worst_slack"
puts "LMH_STAGE_C_BIT=$bit_file"
puts "LMH_STAGE_C_XSA=$xsa_file"

close_project
exit
