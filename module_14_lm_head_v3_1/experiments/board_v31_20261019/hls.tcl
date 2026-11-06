# v3.1 board candidate: arithmetic source identical to v3, new identity only.
set here [file dirname [file normalize [info script]]]
set module [file normalize [file join $here .. ..]]
set build [file join $module build board_v31_20261019]
file mkdir $build
cd $build
if {[file exists hls]} {error "Preserve existing HLS project"}
open_project hls
set_top lm_head_v2
add_files [file join $here src lm_head_v2.cpp] -cflags "-I[file join $here include]"
open_solution solution1
set_part {xczu9eg-ffvb1156-2-i}
create_clock -period 5.000 -name default
set_clock_uncertainty 1.350
config_interface -m_axi_addr64
csynth_design
puts "M14_V31_CSYNTH=PASS"
exit
