# All masters use the same 64-bit system address; MIG receives its low 31 bits.
# No implicit per-master relocation is assumed inside the shared SmartConnect.
set here [file dirname [file normalize [info script]]]
set module [file normalize [file join $here .. ..]]
open_project [file join $module board build m14_board_v31_20261019 m14_board_v31_20261019.xpr]
open_bd_design [get_files */m14_v31_system.bd]
if {![llength [get_bd_intf_ports -quiet pl_ddr_refclk]]} {
    foreach name {c0_sys_clk_p_0 c0_sys_clk_n_0} {
        set port [get_bd_ports $name]
        delete_bd_objs [get_bd_nets -of_objects $port]
        delete_bd_objs $port
    }
    make_bd_intf_pins_external [get_bd_intf_pins ddr4_0/C0_SYS_CLK]
    set_property name pl_ddr_refclk [get_bd_intf_ports C0_SYS_CLK_0]
}
set_property CONFIG.FREQ_HZ 200000000 [get_bd_intf_ports pl_ddr_refclk]
foreach id {41-1353 41-1356 41-1267} {
    set_msg_config -id "BD $id" -new_severity ERROR
}
foreach interface_name {m_axi_hidden m_axi_weight m_axi_history m_axi_logits} {
    set space [get_bd_addr_spaces lm_head_v2_0/Data_${interface_name}]
    set mapped [get_bd_addr_segs lm_head_v2_0/Data_${interface_name}/SEG_ddr4_0_C0_DDR4_ADDRESS_BLOCK]
    if {[llength $mapped] != 1} {error "Missing DDR mapping for $interface_name"}
    set_property offset 0x400000000 $mapped
    exclude_bd_addr_seg -target_address_space $space [get_bd_addr_segs lm_head_v2_0/s_axi_control/Reg]
    exclude_bd_addr_seg -target_address_space $space [get_bd_addr_segs calib_gpio/S_AXI/Reg]
    puts "M14_V31_COMMON_ADDRESS=$interface_name,[get_property offset $mapped],[get_property range $mapped]"
}
set critical_before [get_msg_config -count -severity {CRITICAL WARNING}]
validate_bd_design
if {[get_msg_config -count -severity {CRITICAL WARNING}] > $critical_before} {
    error "BD validation has critical warnings; do not build"
}
save_bd_design
puts "M14_V31_COMMON_ADDRESS_BD=PASS"
if {$argc == 1 && [lindex $argv 0] eq "build"} {
    generate_target all [get_files */m14_v31_system.bd]
    make_wrapper -files [get_files */m14_v31_system.bd] -top -force
    reset_run impl_1
    reset_run synth_1
    update_compile_order -fileset sources_1
    close_project
    source [file join $here build.tcl]
}
close_project
exit
