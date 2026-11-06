set module_dir [file normalize [file join [file dirname [info script]] ".."]]
set build_dir [file join $module_dir "build"]
file mkdir $build_dir
cd $build_dir

open_project -reset lm_head_v2_csynth
set_top lm_head_v2
add_files [file join $module_dir "src" "lm_head_v2.cpp"] \
    -cflags "-I[file join $module_dir include]"
open_solution -reset solution1
set_part {xczu9eg-ffvb1156-2-i}
create_clock -period 10 -name default
config_interface -m_axi_addr64
csynth_design
puts "LM_HEAD_V2_CSYNTH_PASS"
exit
