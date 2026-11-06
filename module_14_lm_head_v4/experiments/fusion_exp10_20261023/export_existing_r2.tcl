cd {D:/program/LLM_FPGA/.cache/e10}
open_project hls
open_solution solution1
config_export -disable_deadlock_detection true
export_design -format ip_catalog -vendor exp10.local -library hls -version 4.10
puts "EXP10_EXPORT=PASS"
exit
