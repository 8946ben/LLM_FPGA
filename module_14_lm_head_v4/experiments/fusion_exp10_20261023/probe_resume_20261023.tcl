set_param general.maxThreads 2
open_project {D:/program/LLM_FPGA/.cache/e10_bd/m14_v4.xpr}
puts "EXP10_SYNTH_STATUS=[get_property STATUS [get_runs synth_1]]"
puts "EXP10_IMPL_STATUS=[get_property STATUS [get_runs impl_1]]"
reset_run -help
launch_runs -help
close_project
puts "EXP10_RESUME_PROBE=PASS"
exit
