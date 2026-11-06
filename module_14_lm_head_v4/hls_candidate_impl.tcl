# Standalone experimental candidate IP implementation; no FPGA access or BD.
set module [file dirname [file normalize [info script]]]
set build [file join $module build candidate_csynth_r2]
cd $build
open_project hls
open_solution solution1
export_design -format ip_catalog -rtl verilog -flow impl
puts "M14_V4_CANDIDATE_STANDALONE_IMPL=PASS"
exit
