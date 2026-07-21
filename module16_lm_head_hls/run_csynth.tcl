set module_dir [file normalize [file dirname [info script]]]
# Vitis HLS 2021.1 on Windows does not always propagate its private DLL
# directory to the synthesis clang child process.
set hls_dll_dir {D:/install/Xilinx/Vitis_HLS/2021.1/lib/win64.o}
set ::env(PATH) "$hls_dll_dir;$::env(PATH)"

set build_dir [file join $module_dir "build"]
file mkdir $build_dir
cd $build_dir
open_project -reset lm_head_csynth
set_top lm_head_argmax
add_files [file join $module_dir "src" "lm_head_kernel.cpp"] -cflags "-I[file join $module_dir include]"
open_solution -reset solution1
set_part {xcu280-fsvh2892-2L-e}
create_clock -period 4 -name default
csynth_design
exit
