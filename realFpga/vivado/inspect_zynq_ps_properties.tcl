# Stage C helper: enumerate the Zynq UltraScale+ MPSoC properties exposed by
# Vivado 2021.1.  This prevents the board-build script from relying on guessed
# property names that vary between Vivado releases.

set script_dir [file normalize [file dirname [info script]]]
set probe_dir [file normalize [file join $script_dir "build" "ps_property_probe"]]

create_project -force lmh_ps_property_probe $probe_dir \
    -part xczu9eg-ffvb1156-2-i
create_bd_design ps_property_probe

set ps [create_bd_cell -type ip \
    -vlnv xilinx.com:ip:zynq_ultra_ps_e:* zynq_ultra_ps_e_0]

puts "LMH_PS_PROBE_BEGIN"
puts "LMH_PS_PROBE_PART=[get_property PART [current_project]]"
puts "LMH_PS_PROBE_VLNV=[get_property VLNV $ps]"

set interesting_pattern {
    DDR|ENET|GEM|MDIO|UART|M_AXI|S_AXI|PL_CLK|PL_RESET|RST|FABRIC|PSS_REF|CRL_APB|CRF_APB
}

foreach property_name [lsort [list_property $ps]] {
    if {[regexp -nocase $interesting_pattern $property_name]} {
        set property_value [get_property $property_name $ps]
        puts "LMH_PS_PROPERTY=$property_name=$property_value"
    }
}

puts "LMH_PS_PROBE_END"
close_project
exit
