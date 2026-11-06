open_project {D:/program/LLM_FPGA/module_14_lm_head_v3_1/board/build/m14_board_v31_20261019/m14_board_v31_20261019.xpr}
open_bd_design [get_files m14_v31_system.bd]
foreach p {/zynq_ultra_ps_e_0/maxihpm0_fpd_aclk /axi_smc/aclk /lm_head_v2_0/ap_clk /axi_cc_ddr/s_aclk /axi_cc_ddr/m_aclk /rst_pl_200M/slowest_sync_clk /rst_ui_ddr/slowest_sync_clk /calib_gpio/s_axi_aclk /ddr4_0/c0_ddr4_ui_clk /ddr4_0/sys_rst /ddr4_0/c0_ddr4_aresetn /rst_ui_ddr/aux_reset_in /calib_gate/Op1 /calib_gate/Op2 /calib_gate/Res /ddr4_0/c0_init_calib_complete} {
    puts "PINCHECK $p = [llength [get_bd_pins -quiet $p]]"
}
close_project
exit
