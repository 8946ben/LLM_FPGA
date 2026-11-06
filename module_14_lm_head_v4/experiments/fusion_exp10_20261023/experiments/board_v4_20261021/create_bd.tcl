# Private lm_head v4 selector standalone PL DDR system; offline only.
# Derived from accepted v3.1 topology; both HLS masters map only to MIG.
set module [file normalize [file join [file dirname [info script]] .. ..]]
set project_dir [file normalize {D:/program/LLM_FPGA/.cache/e10_bd}]
set ip_repo [file join $module ip_repo lm_head_v4_selector]
if {[file exists $project_dir]} {error "Preserve existing v4 experimental project"}

set project_name "m14_v4"
set design_name "m14_v4_system"
set part_name "xczu9eg-ffvb1156-2-i"

if {![file exists [file join $ip_repo "component.xml"]]} {
    error "v4 experimental M14 IP repository is missing component.xml: $ip_repo"
}

set_param general.maxThreads 2
create_project $project_name $project_dir -part $part_name
set_property target_language Verilog [current_project]
set_property simulator_language Mixed [current_project]
set_property ip_repo_paths [list $ip_repo] [current_project]
update_ip_catalog

set lmh_ipdefs [get_ipdefs -all -filter {
    VLNV =~ "exp10.local:hls:lm_head_v4_selector:*"
}]
if {[llength $lmh_ipdefs] != 1} {
    error "Expected exactly one lm_head_v4_selector IP definition, got: $lmh_ipdefs"
}
puts "M14_V4_IP_VLNV=[get_property VLNV [lindex $lmh_ipdefs 0]]"

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
    CONFIG.PSU__MAXIGP0__DATA_WIDTH {128} \
    CONFIG.PSU__USE__M_AXI_GP1 {0} \
    CONFIG.PSU__USE__M_AXI_GP2 {0} \
    CONFIG.PSU__USE__S_AXI_GP2 {0} \
    CONFIG.PSU__USE__S_AXI_GP4 {0} \
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

# ---------------------------------------------------------------------------
# PL DDR4 controller: 2 x MT40A512M16LY (x16, single rank) = 32-bit, 2 GiB.
# DDR4-1600 (800 MHz memory clock) with a 4:1 PHY ratio gives a 200 MHz ui_clk,
# matching the 200 MHz user clock; the AXI clock converter still isolates the
# two sources so calibration/reset does not disturb the PS clock domain.
# ---------------------------------------------------------------------------
set ddr [create_bd_cell -type ip -vlnv xilinx.com:ip:ddr4:2.2 ddr4_0]
set_property -dict [list \
    CONFIG.C0.DDR4_MemoryType {Components} \
    CONFIG.C0.DDR4_MemoryPart {MT40A512M16LY-075} \
    CONFIG.C0.DDR4_DataWidth {32} \
    CONFIG.C0.DDR4_TimePeriod {1250} \
    CONFIG.C0.DDR4_InputClockPeriod {5000} \
    CONFIG.C0.DDR4_PhyClockRatio {4:1} \
    CONFIG.C0.DDR4_Slot {Single} \
    CONFIG.C0.DDR4_ChipSelect {true} \
    CONFIG.C0.DDR4_Clamshell {false} \
    CONFIG.C0.DDR4_DataMask {DM_NO_DBI} \
    CONFIG.C0.DDR4_Ecc {false} \
    CONFIG.C0.DDR4_MemoryVoltage {1.2V} \
    CONFIG.C0.DDR4_Ordering {Normal} \
    CONFIG.C0.DDR4_Mem_Add_Map {ROW_COLUMN_BANK} \
    CONFIG.C0.DDR4_BurstLength {8} \
    CONFIG.C0.DDR4_BurstType {Sequential} \
    CONFIG.C0.DDR4_OnDieTermination {RZQ/6} \
    CONFIG.C0.DDR4_OutputDriverImpedenceControl {RZQ/7} \
    CONFIG.C0.DDR4_AxiSelection {true} \
    CONFIG.C0.DDR4_AxiDataWidth {128} \
    CONFIG.C0.DDR4_AxiAddressWidth {31} \
    CONFIG.C0.DDR4_AxiIDWidth {4} \
    CONFIG.C0.DDR4_AxiArbitrationScheme {RD_PRI_REG} \
    CONFIG.C0.DDR4_AxiNarrowBurst {false} \
    CONFIG.C0.DDR4_EN_PARITY {false} \
    CONFIG.C0.DDR4_isCKEShared {false} \
    CONFIG.C0.DDR4_Enable_LVAUX {false} \
    CONFIG.System_Clock {Differential} \
    CONFIG.Reference_Clock {Differential} \
    CONFIG.Enable_SysPorts {true} \
] $ddr

set memory_part [get_property CONFIG.C0.DDR4_MemoryPart $ddr]
set axi_addr_width [get_property CONFIG.C0.DDR4_AxiAddressWidth $ddr]
set axi_data_width [get_property CONFIG.C0.DDR4_AxiDataWidth $ddr]
set data_width [get_property CONFIG.C0.DDR4_DataWidth $ddr]
puts "M14_V4_MIG_PART=$memory_part"
puts "M14_V4_MIG_AXI=$axi_data_width/$axi_addr_width"
puts "M14_V4_MIG_DATA_WIDTH=$data_width"
if {$memory_part ne "MT40A512M16LY-075"} {error "MIG part fell back to $memory_part"}
if {$axi_addr_width != 31} {error "MIG AXI address width must be 31 (2 GiB), got $axi_addr_width"}
if {$data_width != 32} {error "MIG data width must be 32, got $data_width"}

set lmh [create_bd_cell -type ip \
    -vlnv exp10.local:hls:lm_head_v4_selector:4.10 selector_0]

set smc [create_bd_cell -type ip -vlnv xilinx.com:ip:smartconnect:* axi_smc]
set_property -dict [list CONFIG.NUM_SI {3} CONFIG.NUM_MI {3}] $smc

set cvt [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_clock_converter:* axi_cc_ddr]
set_property -dict [list \
    CONFIG.DATA_WIDTH {128} \
    CONFIG.ADDR_WIDTH {31} \
    CONFIG.ID_WIDTH {4} \
] $cvt

set gpio [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_gpio:* calib_gpio]
set_property -dict [list \
    CONFIG.C_GPIO_WIDTH {1} \
    CONFIG.C_ALL_INPUTS {1} \
    CONFIG.C_IS_DUAL {1} \
    CONFIG.C_GPIO2_WIDTH {32} \
    CONFIG.C_ALL_INPUTS_2 {1} \
] $gpio
set build_signature [create_bd_cell -type ip -vlnv xilinx.com:ip:xlconstant:* selector_build_signature]
set_property -dict [list CONFIG.CONST_WIDTH {32} CONFIG.CONST_VAL [expr {0x4D345A0A}]] $build_signature
connect_bd_net [get_bd_pins $build_signature/dout] [get_bd_pins $gpio/gpio2_io_i]

set rst_pl [create_bd_cell -type ip \
    -vlnv xilinx.com:ip:proc_sys_reset:* rst_pl_200M]
set rst_ui [create_bd_cell -type ip \
    -vlnv xilinx.com:ip:proc_sys_reset:* rst_ui_ddr]

set const_zero [create_bd_cell -type ip -vlnv xilinx.com:ip:xlconstant:* const_zero]
set_property -dict [list CONFIG.CONST_VAL {0}] $const_zero
set const_one [create_bd_cell -type ip -vlnv xilinx.com:ip:xlconstant:* const_one]
set_property -dict [list CONFIG.CONST_VAL {1}] $const_one
set calib_gate [create_bd_cell -type ip -vlnv xilinx.com:ip:util_vector_logic:* calib_gate]
set_property -dict [list CONFIG.C_OPERATION {and} CONFIG.C_SIZE {1}] $calib_gate

# Control and data share one PS master port so that the PL aperture has exactly
# one decoder; the AXI-Lite slaves and the DDR path are separate MIs.
connect_bd_intf_net [get_bd_intf_pins $ps/M_AXI_HPM0_FPD] \
    [get_bd_intf_pins $smc/S00_AXI]
set memory_interfaces [list m_axi_plmem m_axi_histmem]
set si_index 1
foreach interface_name $memory_interfaces {
    set si_pin [format "S%02d_AXI" $si_index]
    connect_bd_intf_net [get_bd_intf_pins $lmh/$interface_name] \
        [get_bd_intf_pins $smc/$si_pin]
    incr si_index
}

connect_bd_intf_net [get_bd_intf_pins $smc/M00_AXI] \
    [get_bd_intf_pins $lmh/s_axi_control]
connect_bd_intf_net [get_bd_intf_pins $smc/M01_AXI] \
    [get_bd_intf_pins $gpio/S_AXI]
connect_bd_intf_net [get_bd_intf_pins $smc/M02_AXI] \
    [get_bd_intf_pins $cvt/S_AXI]
connect_bd_intf_net [get_bd_intf_pins $cvt/M_AXI] \
    [get_bd_intf_pins $ddr/C0_DDR4_S_AXI]

# ---------------------------------------------------------------------------
# Clocks.  ps pl_clk0 = 200 MHz user clock.  ddr4 ui_clk = 200 MHz from MIG.
# ---------------------------------------------------------------------------
set pl_clk0 [get_bd_pins $ps/pl_clk0]
set ui_clk [get_bd_pins $ddr/c0_ddr4_ui_clk]
foreach clock_pin [list \
    $ps/maxihpm0_fpd_aclk \
    $smc/aclk \
    $lmh/ap_clk \
    $cvt/s_axi_aclk \
    $rst_pl/slowest_sync_clk \
    $gpio/s_axi_aclk \
] {
    connect_bd_net $pl_clk0 [get_bd_pins $clock_pin]
}
foreach clock_pin [list $cvt/m_axi_aclk $rst_ui/slowest_sync_clk] {
    connect_bd_net $ui_clk [get_bd_pins $clock_pin]
}

# ---------------------------------------------------------------------------
# Resets.  pl domain is released by the PS; ui domain is released by the PS
# reset synchronised to ui_clk.  The AXI clock converter master side is held in
# reset until DDR calibration completes, so no user transaction can reach an
# uncalibrated MIG.
# ---------------------------------------------------------------------------
connect_bd_net [get_bd_pins $ps/pl_resetn0] [get_bd_pins $rst_pl/ext_reset_in]
connect_bd_net [get_bd_pins $ps/pl_resetn0] [get_bd_pins $rst_ui/ext_reset_in]
connect_bd_net [get_bd_pins $const_zero/dout] \
    [get_bd_pins $rst_pl/mb_debug_sys_rst] \
    [get_bd_pins $rst_ui/mb_debug_sys_rst] \
    [get_bd_pins $ddr/sys_rst]
connect_bd_net [get_bd_pins $const_one/dout] \
    [get_bd_pins $rst_pl/aux_reset_in] \
    [get_bd_pins $rst_pl/dcm_locked] \
    [get_bd_pins $rst_ui/dcm_locked]
connect_bd_net [get_bd_pins $rst_ui/aux_reset_in] \
    [get_bd_pins $ddr/c0_ddr4_ui_clk_sync_rst]
connect_bd_net [get_bd_pins $rst_pl/interconnect_aresetn] [get_bd_pins $smc/aresetn]
connect_bd_net [get_bd_pins $rst_pl/peripheral_aresetn] \
    [get_bd_pins $lmh/ap_rst_n] \
    [get_bd_pins $cvt/s_axi_aresetn] \
    [get_bd_pins $gpio/s_axi_aresetn]
connect_bd_net [get_bd_pins $ddr/c0_init_calib_complete] \
    [get_bd_pins $calib_gate/Op2] \
    [get_bd_pins $gpio/gpio_io_i]
connect_bd_net [get_bd_pins $calib_gate/Res] [get_bd_pins $cvt/m_axi_aresetn]
connect_bd_net [get_bd_pins $ddr/c0_ddr4_aresetn] \
    [get_bd_pins $rst_ui/peripheral_aresetn] [get_bd_pins $calib_gate/Op1]

# sys clock / DDR pins become top-level ports (pin XDC constrains them).
make_bd_intf_pins_external [get_bd_intf_pins $ddr/C0_SYS_CLK]
set_property name pl_ddr_refclk [get_bd_intf_ports C0_SYS_CLK_0]
set_property CONFIG.FREQ_HZ 200000000 [get_bd_intf_ports pl_ddr_refclk]
foreach pin_name [list c0_ddr4_adr c0_ddr4_ba c0_ddr4_bg c0_ddr4_act_n \
                       c0_ddr4_ck_t c0_ddr4_ck_c c0_ddr4_cke c0_ddr4_cs_n \
                       c0_ddr4_odt c0_ddr4_reset_n c0_ddr4_dm_dbi_n \
                       c0_ddr4_dq c0_ddr4_dqs_t c0_ddr4_dqs_c] {
    make_bd_pins_external [get_bd_pins $ddr/$pin_name]
}

# ---------------------------------------------------------------------------
# Address map.
# ---------------------------------------------------------------------------
set mig_seg [get_bd_addr_segs -of_objects [get_bd_intf_pins $ddr/C0_DDR4_S_AXI]]
if {[llength $mig_seg] != 1} {error "Expected one MIG address segment, got $mig_seg"}
set mig_seg [lindex $mig_seg 0]
puts "M14_V4_MIG_SEGMENT=$mig_seg"

assign_bd_address -offset 0xA0000000 -range 0x00010000 \
    -target_address_space [get_bd_addr_spaces $ps/Data] \
    [get_bd_addr_segs $lmh/s_axi_control/Reg]
assign_bd_address -offset 0xA0020000 -range 0x00010000 \
    -target_address_space [get_bd_addr_spaces $ps/Data] \
    [get_bd_addr_segs $gpio/S_AXI/Reg]
assign_bd_address -offset 0x400000000 -range 0x80000000 \
    -target_address_space [get_bd_addr_spaces $ps/Data] $mig_seg

foreach interface_name $memory_interfaces {
    set master_space [get_bd_addr_spaces $lmh/Data_${interface_name}]
    assign_bd_address -offset 0x400000000 -range 0x80000000 \
        -target_address_space $master_space $mig_seg
    exclude_bd_addr_seg -target_address_space $master_space [get_bd_addr_segs $lmh/s_axi_control/Reg]
    exclude_bd_addr_seg -target_address_space $master_space [get_bd_addr_segs $gpio/S_AXI/Reg]
    set width [get_property CONFIG.ADDR_WIDTH [get_bd_intf_pins $lmh/$interface_name]]
    if {$width != 64} {error "$interface_name address width must be 64, got $width"}
}

foreach id {41-1353 41-1356 41-1267} {set_msg_config -id "BD $id" -new_severity ERROR}
set critical_before [get_msg_config -count -severity {CRITICAL WARNING}]
validate_bd_design
if {[get_msg_config -count -severity {CRITICAL WARNING}] > $critical_before} {
    error "BD validation has critical warnings"
}
save_bd_design

set bd_file [get_files [format "*/%s.bd" $design_name]]
generate_target all $bd_file
set wrapper_files [make_wrapper -files $bd_file -top]
add_files -norecurse $wrapper_files
set_property top ${design_name}_wrapper [current_fileset]
update_compile_order -fileset sources_1

set actual [get_property CONFIG.PSU__CRL_APB__PL0_REF_CTRL__ACT_FREQMHZ $ps]
if {$actual < 199.9 || $actual > 200.1} {error "PL0 actual frequency not 200 MHz: $actual"}
puts "M14_V4_PL0_MHZ=$actual"
puts "M14_V4_CONTROL_BASE=0xA0000000"
puts "M14_V4_CALIB_GPIO_BASE=0xA0020000"
puts "M14_V4_PL_DDR_BASE=0x400000000"
puts "M14_V4_PL_DDR_RANGE=0x80000000"
puts "M14_V4_HLS_LOCAL_RANGE=0x80000000"
foreach address_space [lsort [get_bd_addr_spaces]] {
    puts "M14_V4_ADDR_SPACE=$address_space"
    foreach segment [lsort [get_bd_addr_segs -of_objects $address_space]] {
        puts "M14_V4_ADDR_SEGMENT=$address_space|$segment|[get_property OFFSET $segment]|[get_property RANGE $segment]"
    }
}
foreach port [lsort [get_bd_ports]] {
    puts "M14_V4_PORT=$port"
}
puts "M14_V4_BD_CREATED=PASS"
close_project
exit
