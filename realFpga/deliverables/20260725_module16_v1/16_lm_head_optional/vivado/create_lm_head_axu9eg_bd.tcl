# Stage C: create and validate the AXU9EGB Module 16 LM Head block design.
#
# The AXI topology follows the colleague's RMSNorm bring-up document, expanded
# from three to four memory masters for hidden, weight, history and logits.
# The PS MIO selections come from the AXU9EGB user manual:
#   - PS Ethernet: GEM3 RGMII on MIO 64..75, MDIO on MIO 76..77
#   - PS UART pins: MIO 42..43.  Vivado 2021.1 exposes this pair under UART0
#     (UART1 only offers the complementary MIO pairs in zynq_ultra_ps_e v3.3).
#
# The board-level PS settings below are aligned with the colleague's known-good
# AXU9EGB Vivado 2021.1 project at ref/rmsnorm_axu9eg.  In particular, its
# conservative DDR4-1600 configuration is retained instead of using the memory
# devices' nominal DDR4-2400 maximum.  Capacity follows the board manual:
# four 8-Gbit x16 devices, 64-bit total and 4 GB total.

set script_dir [file normalize [file dirname [info script]]]
set module_dir [file normalize [file join $script_dir ".."]]
set project_dir [file normalize [file join $script_dir "build" "lm_head_axu9eg"]]
set ip_repo [file normalize [file join $module_dir "ip_repo" "lm_head_argmax"]]

set project_name "lm_head_axu9eg"
set design_name "lm_head_system"
set part_name "xczu9eg-ffvb1156-2-i"

if {![file exists [file join $ip_repo "component.xml"]]} {
    error "LM Head IP repository is missing component.xml: $ip_repo"
}

create_project -force $project_name $project_dir -part $part_name
set_property target_language Verilog [current_project]
set_property simulator_language Mixed [current_project]
set_property ip_repo_paths [list $ip_repo] [current_project]
update_ip_catalog

set lmh_ipdefs [get_ipdefs -all -filter {
    VLNV =~ "xilinx.com:hls:lm_head_argmax:*"
}]
if {[llength $lmh_ipdefs] != 1} {
    error "Expected exactly one lm_head_argmax IP definition, got: $lmh_ipdefs"
}

create_bd_design $design_name

set ps [create_bd_cell -type ip \
    -vlnv xilinx.com:ip:zynq_ultra_ps_e:* zynq_ultra_ps_e_0]
set_property -dict [list \
    CONFIG.PSU__PSS_REF_CLK__FREQMHZ {33.333} \
    CONFIG.PSU__CRL_APB__PL0_REF_CTRL__FREQMHZ {100} \
    CONFIG.PSU__CRL_APB__PL0_REF_CTRL__SRCSEL {DPLL} \
    CONFIG.PSU__CRL_APB__PL0_REF_CTRL__DIVISOR0 {4} \
    CONFIG.PSU__CRL_APB__PL0_REF_CTRL__DIVISOR1 {1} \
    CONFIG.PSU__PL_CLK0_BUF {TRUE} \
    CONFIG.PSU__USE__FABRIC__RST {1} \
    CONFIG.PSU__NUM_FABRIC_RESETS {1} \
    CONFIG.PSU__USE__RST0 {0} \
    CONFIG.PSU__USE__M_AXI_GP0 {1} \
    CONFIG.PSU__USE__M_AXI_GP2 {0} \
    CONFIG.PSU__USE__S_AXI_GP2 {1} \
    CONFIG.PSU__USE__DDR_INTF_REQUESTED {0} \
    CONFIG.PSU__DDRC__ENABLE {1} \
    CONFIG.PSU__CRF_APB__DDR_CTRL__SRCSEL {DPLL} \
    CONFIG.PSU__DDRC__VREF {1} \
    CONFIG.PSU__DDRC__ECC {Disabled} \
    CONFIG.PSU__DDRC__BUS_WIDTH {64 Bit} \
    CONFIG.PSU__DDRC__DRAM_WIDTH {16 Bits} \
    CONFIG.PSU__DDRC__MEMORY_TYPE {DDR 4} \
    CONFIG.PSU__DDRC__COMPONENTS {Components} \
    CONFIG.PSU__DDRC__SPEED_BIN {DDR4_1600J} \
    CONFIG.PSU__CRF_APB__DDR_CTRL__FREQMHZ {800} \
    CONFIG.PSU__DDRC__DEVICE_CAPACITY {8192 MBits} \
    CONFIG.PSU__DDRC__RANK_ADDR_COUNT {0} \
    CONFIG.PSU__DDRC__BG_ADDR_COUNT {1} \
    CONFIG.PSU__DDRC__BANK_ADDR_COUNT {2} \
    CONFIG.PSU__DDRC__ROW_ADDR_COUNT {16} \
    CONFIG.PSU__DDRC__COL_ADDR_COUNT {10} \
    CONFIG.PSU__DDRC__CL {10} \
    CONFIG.PSU__DDRC__CWL {9} \
    CONFIG.PSU__DDRC__T_RCD {10} \
    CONFIG.PSU__DDRC__T_RP {10} \
    CONFIG.PSU__DDRC__T_RC {47.5} \
    CONFIG.PSU__DDRC__T_RAS_MIN {35} \
    CONFIG.PSU__DDRC__T_FAW {35} \
    CONFIG.PSU__DDRC__DDR4_T_REF_MODE {0} \
    CONFIG.PSU__DDRC__DDR4_T_REF_RANGE {Normal (0-85)} \
    CONFIG.PSU__DDRC__PHY_DBI_MODE {0} \
    CONFIG.PSU__DDRC__PARITY_ENABLE {0} \
    CONFIG.PSU__DDRC__CLOCK_STOP_EN {0} \
    CONFIG.PSU__DDRC__DDR4_CAL_MODE_ENABLE {0} \
    CONFIG.PSU__DDRC__DDR4_CRC_CONTROL {0} \
    CONFIG.PSU__DDRC__TRAIN_DATA_EYE {1} \
    CONFIG.PSU__DDRC__TRAIN_READ_GATE {1} \
    CONFIG.PSU__DDRC__TRAIN_WRITE_LEVEL {1} \
    CONFIG.PSU__DDRC__DDR4_ADDR_MAPPING {1} \
    CONFIG.PSU__DDRC__BRC_MAPPING {ROW_BANK_COL} \
    CONFIG.PSU__DDRC__DM_DBI {DM_NO_DBI} \
    CONFIG.PSU__DDRC__PER_BANK_REFRESH {0} \
    CONFIG.PSU__DDRC__FGRM {1X} \
    CONFIG.PSU__DDRC__LP_ASR {manual normal} \
    CONFIG.PSU__DDRC__DIMM_ADDR_MIRROR {0} \
    CONFIG.PSU__DDRC__STATIC_RD_MODE {0} \
    CONFIG.PSU__DDRC__SELF_REF_ABORT {0} \
    CONFIG.PSU__ENET3__PERIPHERAL__ENABLE {1} \
    CONFIG.PSU__ENET3__PERIPHERAL__IO {MIO 64 .. 75} \
    CONFIG.PSU__ENET3__GRP_MDIO__ENABLE {1} \
    CONFIG.PSU__ENET3__GRP_MDIO__IO {MIO 76 .. 77} \
    CONFIG.PSU__UART0__PERIPHERAL__ENABLE {1} \
    CONFIG.PSU__UART0__PERIPHERAL__IO {MIO 42 .. 43} \
    CONFIG.PSU__CRL_APB__UART1_REF_CTRL__DIVISOR0 {15} \
    CONFIG.PSU__CRL_APB__UART1_REF_CTRL__DIVISOR1 {1} \
    CONFIG.PSU__TTC0__PERIPHERAL__ENABLE {1} \
] $ps

set lmh [create_bd_cell -type ip \
    -vlnv xilinx.com:hls:lm_head_argmax:1.0 lm_head_argmax_0]

set ctrl_smc [create_bd_cell -type ip \
    -vlnv xilinx.com:ip:smartconnect:* axi_smc_ctrl]
set_property -dict [list CONFIG.NUM_SI {1} CONFIG.NUM_MI {1}] $ctrl_smc

set mem_smc [create_bd_cell -type ip \
    -vlnv xilinx.com:ip:smartconnect:* axi_smc_mem]
set_property -dict [list CONFIG.NUM_SI {4} CONFIG.NUM_MI {1}] $mem_smc

set rst [create_bd_cell -type ip \
    -vlnv xilinx.com:ip:proc_sys_reset:* rst_ps8_0_100M]

set const_zero [create_bd_cell -type ip \
    -vlnv xilinx.com:ip:xlconstant:* const_zero]
set_property -dict [list CONFIG.CONST_VAL {0}] $const_zero

set const_one [create_bd_cell -type ip \
    -vlnv xilinx.com:ip:xlconstant:* const_one]
set_property -dict [list CONFIG.CONST_VAL {1}] $const_one

# Zynq UltraScale+ PS DDR and MIO are dedicated package connections.  Unlike
# processing_system7, zynq_ultra_ps_e does not expose DDR/FIXED_IO BD ports.
# They are configured entirely through the PS cell and exported in the XSA.

# Control path: A53 -> HPM0_FPD -> SmartConnect -> HLS AXI-Lite registers.
connect_bd_intf_net \
    [get_bd_intf_pins $ps/M_AXI_HPM0_FPD] \
    [get_bd_intf_pins $ctrl_smc/S00_AXI]
connect_bd_intf_net \
    [get_bd_intf_pins $ctrl_smc/M00_AXI] \
    [get_bd_intf_pins $lmh/s_axi_control]

# Data path: four HLS AXI masters -> SmartConnect -> HP0_FPD -> PS DDR.
set memory_interfaces [list \
    m_axi_gmem_hidden \
    m_axi_gmem_weight \
    m_axi_gmem_history \
    m_axi_gmem_logits \
]
set si_index 0
foreach interface_name $memory_interfaces {
    set si_pin [format "S%02d_AXI" $si_index]
    connect_bd_intf_net \
        [get_bd_intf_pins $lmh/$interface_name] \
        [get_bd_intf_pins $mem_smc/$si_pin]
    incr si_index
}
connect_bd_intf_net \
    [get_bd_intf_pins $mem_smc/M00_AXI] \
    [get_bd_intf_pins $ps/S_AXI_HP0_FPD]

# A single 100 MHz PL clock domain is used for first-board bring-up.
set pl_clk0 [get_bd_pins $ps/pl_clk0]
set clock_pins [list \
    $ps/maxihpm0_fpd_aclk \
    $ps/saxihp0_fpd_aclk \
    $ctrl_smc/aclk \
    $mem_smc/aclk \
    $lmh/ap_clk \
    $rst/slowest_sync_clk \
]
foreach clock_pin $clock_pins {
    connect_bd_net $pl_clk0 [get_bd_pins $clock_pin]
}

# Reset path.  pl_resetn0 is active-low; Vivado infers the external reset
# polarity from the connected pin.  In this generated proc_sys_reset instance
# C_AUX_RESET_HIGH=0, so aux_reset_in is inactive at logic 1.  The MicroBlaze
# debug reset remains inactive at logic 0, and dcm_locked is tied high because
# pl_clk0 is produced by the PS.
connect_bd_net \
    [get_bd_pins $ps/pl_resetn0] \
    [get_bd_pins $rst/ext_reset_in]
connect_bd_net \
    [get_bd_pins $const_zero/dout] \
    [get_bd_pins $rst/mb_debug_sys_rst]
connect_bd_net \
    [get_bd_pins $const_one/dout] \
    [get_bd_pins $rst/aux_reset_in] \
    [get_bd_pins $rst/dcm_locked]
connect_bd_net \
    [get_bd_pins $rst/interconnect_aresetn] \
    [get_bd_pins $ctrl_smc/aresetn] \
    [get_bd_pins $mem_smc/aresetn]
connect_bd_net \
    [get_bd_pins $rst/peripheral_aresetn] \
    [get_bd_pins $lmh/ap_rst_n]

# Use a stable control address and automatically map every HLS master to the
# reachable PS DDR segments.
assign_bd_address -offset 0xA0000000 -range 0x00010000 \
    -target_address_space [get_bd_addr_spaces $ps/Data] \
    [get_bd_addr_segs $lmh/s_axi_control/Reg] -force
assign_bd_address

validate_bd_design
save_bd_design

set bd_file [get_files [format "*/%s.bd" $design_name]]
generate_target all $bd_file
set wrapper_files [make_wrapper -files $bd_file -top]
add_files -norecurse $wrapper_files
set_property top ${design_name}_wrapper [current_fileset]
update_compile_order -fileset sources_1

puts "LMH_STAGE_C_CREATE=PASS"
puts "LMH_STAGE_C_PART=[get_property PART [current_project]]"
puts "LMH_STAGE_C_HLS_VLNV=[get_property VLNV $lmh]"
puts "LMH_STAGE_C_PL0_ACTUAL_MHZ=[get_property CONFIG.PSU__CRL_APB__PL0_REF_CTRL__ACT_FREQMHZ $ps]"
puts "LMH_STAGE_C_GEM3_IO=[get_property CONFIG.PSU__ENET3__PERIPHERAL__IO $ps]"
puts "LMH_STAGE_C_MDIO_IO=[get_property CONFIG.PSU__ENET3__GRP_MDIO__IO $ps]"
puts "LMH_STAGE_C_UART0_IO=[get_property CONFIG.PSU__UART0__PERIPHERAL__IO $ps]"
puts "LMH_STAGE_C_CONTROL_BASE=0xA0000000"
puts "LMH_STAGE_C_DDR_REQUESTED=[get_property CONFIG.PSU__USE__DDR_INTF_REQUESTED $ps]"
puts "LMH_STAGE_C_DDR_ENABLE=[get_property CONFIG.PSU__DDRC__ENABLE $ps]"
puts "LMH_STAGE_C_DDR_BUS_WIDTH=[get_property CONFIG.PSU__DDRC__BUS_WIDTH $ps]"
puts "LMH_STAGE_C_DDR_DRAM_WIDTH=[get_property CONFIG.PSU__DDRC__DRAM_WIDTH $ps]"
puts "LMH_STAGE_C_DDR_DEVICE_CAPACITY=[get_property CONFIG.PSU__DDRC__DEVICE_CAPACITY $ps]"
puts "LMH_STAGE_C_DDR_ROW_ADDR_COUNT=[get_property CONFIG.PSU__DDRC__ROW_ADDR_COUNT $ps]"
puts "LMH_STAGE_C_DDR_FREQ_MHZ=[get_property CONFIG.PSU__CRF_APB__DDR_CTRL__FREQMHZ $ps]"
puts "LMH_STAGE_C_DDR_SPEED_BIN=[get_property CONFIG.PSU__DDRC__SPEED_BIN $ps]"
puts "LMH_STAGE_C_DDR_PRESET_STATUS=REFERENCE_ALIGNED_RMSNORM_AXU9EGB"

foreach address_space [lsort [get_bd_addr_spaces]] {
    puts "LMH_STAGE_C_ADDR_SPACE=$address_space"
    foreach segment [lsort [get_bd_addr_segs -of_objects $address_space]] {
        puts "LMH_STAGE_C_ADDR_SEGMENT=$address_space|$segment|[get_property OFFSET $segment]|[get_property RANGE $segment]"
    }
}

close_project
exit
