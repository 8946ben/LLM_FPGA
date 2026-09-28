proc report_reset_properties {label project_file design_file ps_name} {
    open_project $project_file
    open_bd_design $design_file
    set ps [get_bd_cells $ps_name]
    puts "${label}_USE_FABRIC_RST=[get_property CONFIG.PSU__USE__FABRIC__RST $ps]"
    puts "${label}_NUM_FABRIC_RESETS=[get_property CONFIG.PSU__NUM_FABRIC_RESETS $ps]"
    puts "${label}_USE_RST0=[get_property CONFIG.PSU__USE__RST0 $ps]"
    puts "${label}_PL_RESETN0_PIN_COUNT=[llength [get_bd_pins -quiet $ps_name/pl_resetn0]]"
    close_project
}

report_reset_properties \
    "RMS" \
    "D:/program/LLM_FPGA/ref/rmsnorm_axu9eg/rmsnorm_axu9eg.xpr" \
    "D:/program/LLM_FPGA/ref/rmsnorm_axu9eg/rmsnorm_axu9eg.srcs/sources_1/bd/system_wrapper/system_wrapper.bd" \
    "zynq_ultra_ps_e_0"

report_reset_properties \
    "LMH" \
    "D:/program/LLM_FPGA/realFpga/vivado/build/lm_head_axu9eg/lm_head_axu9eg.xpr" \
    "D:/program/LLM_FPGA/realFpga/vivado/build/lm_head_axu9eg/lm_head_axu9eg.srcs/sources_1/bd/lm_head_system/lm_head_system.bd" \
    "zynq_ultra_ps_e_0"

exit
