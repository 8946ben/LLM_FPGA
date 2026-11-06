set here [file dirname [file normalize [info script]]]
read_xdc [file join $here lm_head_v4_ddr4_pins.xdc]
set reset [get_ports c0_ddr4_reset_n_0]
if {[get_property PACKAGE_PIN $reset] ne "AM5" || [get_property IOSTANDARD $reset] ne "LVCMOS12" || [get_property DRIVE $reset] != 8} {error "DDR RESET I/O mismatch"}
puts "M14_D64_RESET_IO=AM5,LVCMOS12,DRIVE8"
