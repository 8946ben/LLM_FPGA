# Isolated diagnostic candidate. Never opens the production HLS project/IP repo.
set candidate_dir [file normalize [file dirname [info script]]]
set module_dir [file normalize [file join $candidate_dir .. .. ..]]
set run_root [file join $module_dir build frequency_200_20261016 reduce_layers]
set mode csynth
if {[info exists ::env(M14_200_MODE)]} {set mode $::env(M14_200_MODE)}
if {$mode ni {csynth csim cosim cosim_full_hidden rtl896}} {error "Unknown M14_200_MODE: $mode"}
set project_dir [file join $run_root $mode]
if {[file exists $project_dir]} {error "Preserve existing candidate project: $project_dir"}
file mkdir $run_root
cd $run_root
open_project $mode
set_top lm_head_v2
if {$mode eq "csynth"} {
    add_files [file join $candidate_dir src lm_head_v2.cpp] \
        -cflags "-I[file join $candidate_dir include]"
} else {
    set flags "-std=c++14 -DLMH_V2_TEST_FULL_HIDDEN -I[file join $candidate_dir tests]"
    if {$mode eq "rtl896"} {
        add_files [file join $candidate_dir tests rtl lm_head_v2.cpp] -cflags $flags
    } else {
        add_files [file join $candidate_dir tests kernel_full_hidden.cpp] -cflags $flags
    }
    add_files -tb [file join $candidate_dir tests kernel_equivalence.cpp] -cflags $flags
}
open_solution solution1
set_part {xczu9eg-ffvb1156-2-i}
create_clock -period 5.000 -name default
set_clock_uncertainty 1.350
config_interface -m_axi_addr64
if {$mode eq "csim"} {
    csim_design
} else {
    csynth_design
    if {$mode ne "csynth"} {cosim_design -rtl verilog -trace_level port}
}
puts "M14_200_REDUCE_LAYERS_${mode}_COMPLETE_NOT_BOARD_ACCEPTANCE"
exit
