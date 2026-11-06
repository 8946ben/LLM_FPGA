# Isolated, synthesis-only timing diagnostic. Does not connect to FPGA hardware.
# Launch with Vitis HLS 2021.1. Production 100 MHz sources/projects are not reset.
set experiment_dir [file normalize [file dirname [info script]]]
set module_dir [file normalize [file join $experiment_dir ".." ".."]]
set run_dir [file join $module_dir build frequency_200_20261016]
file mkdir $run_dir
cd $run_dir
set project_name lm_head_v2_200_diagnostic
# Preserve earlier diagnostics rather than resetting an existing result.
if {[file exists [file join $run_dir $project_name]]} {
    error "Diagnostic project already exists; archive it or select a fresh run directory."
}
open_project $project_name
set_top lm_head_v2
add_files [file join $module_dir src lm_head_v2.cpp] \
    -cflags "-I[file join $module_dir include]"
open_solution solution1
set_part {xczu9eg-ffvb1156-2-i}
create_clock -period 5.000 -name default
# Explicitly retain the 27% margin used by the 2021.1 HLS default (100 MHz:2.70ns).
# HLS scheduling uncertainty is distinct from post-route clock uncertainty.
set_clock_uncertainty 1.350
config_interface -m_axi_addr64
csynth_design
puts "M14_200_CSYNTH_COMPLETE_NOT_TIMING_ACCEPTANCE"
exit
