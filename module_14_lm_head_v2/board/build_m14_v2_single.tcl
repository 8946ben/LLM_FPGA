# Synthesize, implement and export the M14 V2 single-module
# hardware design.  This script never connects to or programs the board.

set script_dir [file normalize [file dirname [info script]]]
set project_dir [file normalize [file join $script_dir "build" "m14_v2_single"]]
set project_file [file join $project_dir "m14_v2_single.xpr"]
set result_dir [file normalize [file join $script_dir ".." "reports" \
    "board_build"]]

file mkdir $result_dir

if {![file exists $project_file]} {
    error "Vivado project is missing; run create_m14_v2_single_bd.tcl first: $project_file"
}

open_project $project_file

set reuse_completed_impl 0
if {[info exists ::env(LMH_REUSE_COMPLETED_IMPL)] &&
    $::env(LMH_REUSE_COMPLETED_IMPL) eq "1"} {
    set reuse_completed_impl 1
    puts "M14_V2_REUSE_COMPLETED_IMPL=1"
}

if {!$reuse_completed_impl} {
    set bd_file [get_files "*/m14_v2_system.bd"]
    set ooc_runs [get_runs -quiet *_synth_1]
    if {[llength $ooc_runs] > 0} {
        # Recover cleanly if a previous Windows child-process launch was
        # interrupted and left OOC runs marked as Running.
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
}
set synth_status [get_property STATUS [get_runs synth_1]]
puts "M14_V2_SYNTH_STATUS=$synth_status"
if {![string match "*Complete*" $synth_status]} {
    error "Synthesis did not complete successfully: $synth_status"
}

if {!$reuse_completed_impl} {
    open_run synth_1
    report_utilization -file [file join $result_dir "post_synth_utilization.rpt"]
    report_timing_summary -file [file join $result_dir "post_synth_timing_summary.rpt"]

    launch_runs impl_1 -to_step write_bitstream -jobs 4
    wait_on_run impl_1
}
set impl_status [get_property STATUS [get_runs impl_1]]
puts "M14_V2_IMPL_STATUS=$impl_status"
if {![string match "*Complete*" $impl_status]} {
    error "Implementation/bitstream did not complete successfully: $impl_status"
}

open_run impl_1
report_utilization -file [file join $result_dir "post_route_utilization.rpt"]
report_timing_summary -file [file join $result_dir "post_route_timing_summary.rpt"]
report_drc -file [file join $result_dir "post_route_drc.rpt"]

set bit_file [file join $project_dir \
    "m14_v2_single.runs" "impl_1" "m14_v2_system_wrapper.bit"]
if {![file exists $bit_file]} {
    error "Implementation completed but bitstream is missing: $bit_file"
}

if {[llength [info commands write_hw_platform]] > 0} {
    set platform_file [file join $result_dir "m14_v2_single.xsa"]
    write_hw_platform -fixed -include_bit -force -file $platform_file
    if {![file exists $platform_file]} {
        error "write_hw_platform completed but XSA is missing: $platform_file"
    }
    puts "M14_V2_XSA=$platform_file"
} else {
    set hwdef_file [file join $result_dir "m14_v2_single.hwdef"]
    set platform_file [file join $result_dir "m14_v2_single.sysdef"]
    write_hwdef -force $hwdef_file
    write_sysdef -force -hwdef $hwdef_file -bitfile $bit_file $platform_file
    if {![file exists $hwdef_file] || ![file exists $platform_file]} {
        error "Legacy hardware platform export did not produce hwdef/sysdef."
    }
    puts "M14_V2_HWDEF=$hwdef_file"
    puts "M14_V2_SYSDEF=$platform_file"
}

set timing_paths [get_timing_paths -max_paths 1 -nworst 1]
if {[llength $timing_paths] > 0} {
    set worst_slack [get_property SLACK [lindex $timing_paths 0]]
} else {
    set worst_slack "N/A"
}

puts "M14_V2_BUILD=PASS"
puts "M14_V2_WORST_SLACK_NS=$worst_slack"
puts "M14_V2_BIT=$bit_file"
puts "M14_V2_PLATFORM=$platform_file"

close_project
exit
