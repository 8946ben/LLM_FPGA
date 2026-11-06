set module_dir [file normalize [file join [file dirname [info script]] ".."]]
set build_dir [file join $module_dir "build"]
file mkdir $build_dir
cd $build_dir

open_project -reset lm_head_v2_cosim
set_top lm_head_v2
set hls_version [version -short]
set hls_major [lindex [split $hls_version "."] 0]
if {$hls_major >= 2020} {
    # The 2021.1 MinGW co-sim wrapper includes C++14 library constructs in
    # generated design-side sources.  Older Vivado HLS clang rejects the same
    # design cflag, so keep its tested C++0x split below.
    set design_flags "-std=c++14 -DLMH_V2_TEST_SMALL -I[file join $module_dir include]"
    set test_flags "-std=c++14 -DLMH_V2_TEST_SMALL -I[file join $module_dir include]"
} else {
    set design_flags "-DLMH_V2_TEST_SMALL -I[file join $module_dir include]"
    set test_flags "-std=c++0x -DLMH_V2_TEST_SMALL -I[file join $module_dir include]"
}
puts "LM_HEAD_V2_COSIM_HLS_VERSION=$hls_version"
add_files [file join $module_dir "src" "lm_head_v2.cpp"] -cflags $design_flags
add_files -tb [file join $module_dir "tb" "lm_head_v2_tb.cpp"] -cflags $test_flags
open_solution -reset solution1
set_part {xczu9eg-ffvb1156-2-i}
create_clock -period 10 -name default
config_interface -m_axi_addr64
csynth_design
cosim_design -rtl verilog -trace_level port
puts "LM_HEAD_V2_COSIM_PASS"
exit
