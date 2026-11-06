set module_dir [file normalize [file join [file dirname [info script]] ".."]]
set build_dir [file join $module_dir "build"]
file mkdir $build_dir
cd $build_dir

open_project -reset lm_head_v2_csim
set_top lm_head_v2
set test_flags "-std=c++0x -DLMH_V2_TEST_SMALL -I[file join $module_dir include]"
add_files [file join $module_dir "src" "lm_head_v2.cpp"] -cflags $test_flags
add_files -tb [file join $module_dir "tb" "lm_head_v2_tb.cpp"] -cflags $test_flags
open_solution -reset solution1
set_part {xczu9eg-ffvb1156-2-i}
create_clock -period 10 -name default
config_interface -m_axi_addr64
csim_design -clean
puts "LM_HEAD_V2_CSIM_PASS"
exit
