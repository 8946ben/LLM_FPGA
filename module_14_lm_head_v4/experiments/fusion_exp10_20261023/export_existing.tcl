# Reuse precisely the synthesized and co-simulated solution; no resynthesis.
set module [file dirname [file normalize [info script]]]
cd {D:/program/LLM_FPGA/.cache/e10}
open_project hls
open_solution solution1
export_design -format ip_catalog -vendor exp10.local -library hls -version 4.10
puts "EXP10_EXPORT=PASS"
exit
