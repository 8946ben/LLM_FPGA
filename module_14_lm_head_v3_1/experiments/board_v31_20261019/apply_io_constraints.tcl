# Reapply the implementation-only pin constraints when resuming an opt DCP.
set here [file dirname [file normalize [info script]]]
set module [file normalize [file join $here .. ..]]
read_xdc [file join $module constraints lm_head_v31_ddr4_pins.xdc]
set reset [get_ports c0_ddr4_reset_n_0]
if {[get_property PACKAGE_PIN $reset] ne "AM5" ||
    [get_property IOSTANDARD $reset] ne "LVCMOS12" ||
    [get_property DRIVE $reset] != 8} {error "DDR RESET I/O mismatch"}
puts "M14_V31_RESET_IO=AM5,LVCMOS12,DRIVE8"
