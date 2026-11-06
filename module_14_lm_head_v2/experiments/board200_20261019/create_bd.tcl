# Independent board candidate: 200 MHz, revision 2, build_config 0x20c08011.
# Create the AXU9EGB M14 LM Head V2 single-module block design.
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

set project_dir {D:/program/LLM_FPGA/module_14_lm_head_v2/board/build/m14_board200_20261019}
set ip_repo {D:/program/LLM_FPGA/module_14_lm_head_v2/build/board200_20261019/hls/solution1/impl/ip}
if {[file exists $project_dir]} {error "Preserve existing 200 MHz project"}

set project_name "m14_board200_20261019"
set design_name "m14_200_system"
set part_name "xczu9eg-ffvb1156-2-i"

if {![file exists [file join $ip_repo "component.xml"]]} {
    error "M14 V2 IP repository is missing component.xml: $ip_repo"
}

create_project $project_name $project_dir -part $part_name
set_property target_language Verilog [current_project]
set_property simulator_language Mixed [current_project]
set_property ip_repo_paths [list $ip_repo] [current_project]
update_ip_catalog

set lmh_ipdefs [get_ipdefs -all -filter {
    VLNV =~ "user.org:llm_fpga:lm_head_v2:*"
}]
if {[llength $lmh_ipdefs] != 1} {
    error "Expected exactly one lm_head_v2 IP definition, got: $lmh_ipdefs"
}

create_bd_design $design_name

set ps [create_bd_cell -type ip \
    -vlnv xilinx.com:ip:zynq_ultra_ps_e:* zynq_ultra_ps_e_0]
set_property -dict [list \
    CONFIG.PSU__PSS_REF_CLK__FREQMHZ {33.333} \
    CONFIG.PSU__CRL_APB__PL0_REF_CTRL__FREQMHZ {200} \
    CONFIG.PSU__CRL_APB__PL0_REF_CTRL__SRCSEL {DPLL} \
    CONFIG.PSU__CRL_APB__PL0_REF_CTRL__DIVISOR0 {2} \
    CONFIG.PSU__CRL_APB__PL0_REF_CTRL__DIVISOR1 {1} \
    CONFIG.PSU__PL_CLK0_BUF {TRUE} \
    CONFIG.PSU__USE__FABRIC__RST {1} \
    CONFIG.PSU__NUM_FABRIC_RESETS {1} \
    CONFIG.PSU__USE__RST0 {0} \
    CONFIG.PSU__USE__M_AXI_GP0 {1} \
    CONFIG.PSU__USE__M_AXI_GP2 {0} \
    CONFIG.PSU__USE__S_AXI_GP2 {0} \
    CONFIG.PSU__USE__S_AXI_GP4 {1} \
    CONFIG.PSU__SAXIGP4__DATA_WIDTH {128} \
    CONFIG.PSU__HIGH_ADDRESS__ENABLE {1} \
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
    -vlnv user.org:llm_fpga:lm_head_v2:2.1 lm_head_v2_0]

set ctrl_smc [create_bd_cell -type ip \
    -vlnv xilinx.com:ip:smartconnect:* axi_smc_ctrl]
set_property -dict [list CONFIG.NUM_SI {1} CONFIG.NUM_MI {1}] $ctrl_smc

set mem_smc [create_bd_cell -type ip \
    -vlnv xilinx.com:ip:smartconnect:* axi_smc_mem]
set_property -dict [list CONFIG.NUM_SI {4} CONFIG.NUM_MI {1}] $mem_smc

set rst [create_bd_cell -type ip \
    -vlnv xilinx.com:ip:proc_sys_reset:* rst_ps8_0_200M]

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

# Data path: four HLS AXI masters -> SmartConnect -> HP2_FPD -> PS DDR.
set memory_interfaces [list \
    m_axi_hidden \
    m_axi_weight \
    m_axi_history \
    m_axi_logits \
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
    [get_bd_intf_pins $ps/S_AXI_HP2_FPD]

# A single 200 MHz PL clock domain is used for first-board bring-up.
set pl_clk0 [get_bd_pins $ps/pl_clk0]
set clock_pins [list \
    $ps/maxihpm0_fpd_aclk \
    $ps/saxihp2_fpd_aclk \
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

# Use a stable control address for the HLS register bank.
assign_bd_address -offset 0xA0000000 -range 0x00010000 \
    -target_address_space [get_bd_addr_spaces $ps/Data] \
    [get_bd_addr_segs $lmh/s_axi_control/Reg]

# Map only the two physical 2 GiB DDR regions registered by the project
# profile.  Vivado 2017.4 otherwise exposes a wider DDR_HIGH aperture than the
# 4 GiB fitted memory, which would make out-of-capacity addresses look valid.
foreach interface_name $memory_interfaces {
    set master_space [get_bd_addr_spaces $lmh/Data_${interface_name}]
    assign_bd_address -offset 0x00000000 -range 0x80000000 \
        -target_address_space $master_space \
        [get_bd_addr_segs $ps/SAXIGP4/HP2_DDR_LOW]
    assign_bd_address -offset 0x800000000 -range 0x80000000 \
        -target_address_space $master_space \
        [get_bd_addr_segs $ps/SAXIGP4/HP2_DDR_HIGH]
}

# Fail closed if a future IP export or PS preset silently narrows the address
# path.  The HLS masters keep uint64_t software registers, while the PS HP2
# path must cover the project's 40-bit DDR profile including DDR_HIGH.
foreach interface_name $memory_interfaces {
    set master_pin [get_bd_intf_pins $lmh/$interface_name]
    set master_space [get_bd_addr_spaces $lmh/Data_${interface_name}]
    set master_addr_width [get_property CONFIG.ADDR_WIDTH $master_pin]
    if {$master_addr_width != 64} {
        error "$interface_name address width must be 64, got $master_addr_width"
    }

    set has_ddr_low 0
    set has_ddr_high 0
    foreach segment [get_bd_addr_segs -of_objects $master_space] {
        if {[string match "*DDR_LOW*" $segment]} {
            set has_ddr_low 1
            if {[expr {[get_property OFFSET $segment]}] != 0x00000000 ||
                [expr {[get_property RANGE $segment]}] != 0x80000000} {
                error "$interface_name DDR_LOW offset/range mismatch"
            }
        }
        if {[string match "*DDR_HIGH*" $segment]} {
            set has_ddr_high 1
            if {[expr {[get_property OFFSET $segment]}] != 0x800000000 ||
                [expr {[get_property RANGE $segment]}] != 0x80000000} {
                error "$interface_name DDR_HIGH offset/range mismatch"
            }
        }
    }
    if {!$has_ddr_low || !$has_ddr_high} {
        error "$interface_name must map both DDR_LOW and DDR_HIGH"
    }
    puts "M14_V2_MASTER_ADDR_WIDTH=$interface_name|$master_addr_width"
    puts "M14_V2_MASTER_DDR_REGIONS=$interface_name|DDR_LOW|DDR_HIGH"
}

set hp2_addr_width [get_property CONFIG.ADDR_WIDTH \
    [get_bd_intf_pins $ps/S_AXI_HP2_FPD]]
if {$hp2_addr_width < 40} {
    error "HP2 address width must cover the 40-bit project profile, got $hp2_addr_width"
}
puts "M14_V2_HP2_ADDR_WIDTH=$hp2_addr_width"
puts "M14_V2_PS_HIGH_ADDRESS_ENABLE=[get_property CONFIG.PSU__HIGH_ADDRESS__ENABLE $ps]"

validate_bd_design
save_bd_design

set bd_file [get_files [format "*/%s.bd" $design_name]]
generate_target all $bd_file
set wrapper_files [make_wrapper -files $bd_file -top]
add_files -norecurse $wrapper_files
set_property top ${design_name}_wrapper [current_fileset]
update_compile_order -fileset sources_1

puts "M14_V2_CREATE=PASS"
puts "M14_V2_PART=[get_property PART [current_project]]"
puts "M14_V2_HLS_VLNV=[get_property VLNV $lmh]"
puts "M14_V2_PL0_ACTUAL_MHZ=[get_property CONFIG.PSU__CRL_APB__PL0_REF_CTRL__ACT_FREQMHZ $ps]"
puts "M14_V2_GEM3_IO=[get_property CONFIG.PSU__ENET3__PERIPHERAL__IO $ps]"
puts "M14_V2_MDIO_IO=[get_property CONFIG.PSU__ENET3__GRP_MDIO__IO $ps]"
puts "M14_V2_UART0_IO=[get_property CONFIG.PSU__UART0__PERIPHERAL__IO $ps]"
puts "M14_V2_CONTROL_BASE=0xA0000000"
puts "M14_V2_DDR_REQUESTED=[get_property CONFIG.PSU__USE__DDR_INTF_REQUESTED $ps]"
puts "M14_V2_DDR_ENABLE=[get_property CONFIG.PSU__DDRC__ENABLE $ps]"
puts "M14_V2_DDR_BUS_WIDTH=[get_property CONFIG.PSU__DDRC__BUS_WIDTH $ps]"
puts "M14_V2_DDR_DRAM_WIDTH=[get_property CONFIG.PSU__DDRC__DRAM_WIDTH $ps]"
puts "M14_V2_DDR_DEVICE_CAPACITY=[get_property CONFIG.PSU__DDRC__DEVICE_CAPACITY $ps]"
puts "M14_V2_DDR_ROW_ADDR_COUNT=[get_property CONFIG.PSU__DDRC__ROW_ADDR_COUNT $ps]"
puts "M14_V2_DDR_FREQ_MHZ=[get_property CONFIG.PSU__CRF_APB__DDR_CTRL__FREQMHZ $ps]"
puts "M14_V2_DDR_SPEED_BIN=[get_property CONFIG.PSU__DDRC__SPEED_BIN $ps]"
puts "M14_V2_DDR_PRESET_STATUS=REFERENCE_ALIGNED_RMSNORM_AXU9EGB"

foreach address_space [lsort [get_bd_addr_spaces]] {
    puts "M14_V2_ADDR_SPACE=$address_space"
    foreach segment [lsort [get_bd_addr_segs -of_objects $address_space]] {
        puts "M14_V2_ADDR_SEGMENT=$address_space|$segment|[get_property OFFSET $segment]|[get_property RANGE $segment]"
    }
}

set hp2_width [get_property CONFIG.PSU__SAXIGP4__DATA_WIDTH $ps]
if {$hp2_width != 128} {
    error "HP2 width must be 128, got $hp2_width"
}
puts "M14_V2_HP2_WIDTH=$hp2_width"


set actual [get_property CONFIG.PSU__CRL_APB__PL0_REF_CTRL__ACT_FREQMHZ $ps]
if {$actual < 199.9 || $actual > 200.1} {error "PL0 actual frequency not approximately 200 MHz: $actual"}
puts "M14_BOARD200_BD_CREATED_ACTUAL_MHZ=$actual"

close_project
exit
