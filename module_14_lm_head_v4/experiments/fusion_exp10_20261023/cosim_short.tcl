# Exact synthesis copied with SHA proof to avoid Windows260 path limit.
cd {D:/program/LLM_FPGA/.cache/e10}
open_project hls
open_solution solution1
cosim_design -rtl verilog -tool xsim -trace_level none -argv {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023 --rtl}
puts "EXP10_SHORT_COSIM=PASS"
exit
