set module_dir [file normalize [file dirname [info script]]]
# Vitis HLS 2021.1 on Windows does not always propagate its private DLL
# directory to synthesis and IP-packaging child processes.
set hls_dll_dir {D:/install/Xilinx/Vitis_HLS/2021.1/lib/win64.o}
set ::env(PATH) "$hls_dll_dir;$::env(PATH)"

set build_dir [file join $module_dir "build"]
file mkdir $build_dir
cd $build_dir
open_project -reset lm_head_export
set_top lm_head_argmax
add_files [file join $module_dir "src" "lm_head_kernel.cpp"] -cflags "-I[file join $module_dir include]"
open_solution -reset solution1
set_part {xczu9eg-ffvb1156-2-i}
create_clock -period 5 -name default
csynth_design
export_design -format ip_catalog -rtl verilog
exit
