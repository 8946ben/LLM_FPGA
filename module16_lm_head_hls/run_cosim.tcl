set module_dir [file normalize [file dirname [info script]]]
set hls_dll_dir {D:/install/Xilinx/Vitis_HLS/2021.1/lib/win64.o}
set hls_mingw_dir {D:/install/Xilinx/Vitis_HLS/2021.1/tps/win64/msys64/mingw64/bin}
set hls_fpo_dir {D:/install/Xilinx/Vitis_HLS/2021.1/win64/tools/fpo_v7_0}
set ::env(PATH) "$hls_mingw_dir;$hls_fpo_dir;$hls_dll_dir;$::env(PATH)"

set build_dir [file join $module_dir "build"]
file mkdir $build_dir
cd $build_dir
open_project -reset lm_head_cosim
set_top lm_head_argmax
set compact_flags "-DLMH_COSIM_SMALL -I[file join $module_dir include]"
add_files [file join $module_dir "src" "lm_head_kernel.cpp"] -cflags $compact_flags
add_files -tb [file join $module_dir "tb" "lm_head_tb.cpp"] -cflags $compact_flags
open_solution -reset solution1
set_part {xcu280-fsvh2892-2L-e}
create_clock -period 4 -name default
csynth_design
cosim_design -rtl verilog -trace_level port
exit
