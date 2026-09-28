proc stage_d_fail {message options_dict} {
    puts stderr "STAGE_D_ERROR: $message"
    if {[dict exists $options_dict -errorinfo]} {
        puts stderr [dict get $options_dict -errorinfo]
    }
    exit 1
}

puts "STAGE_D_JTAG_PROBE_BEGIN"
if {[catch {
    connect
    puts "JTAG_TARGETS_BEGIN"
    puts [targets]
    puts "JTAG_TARGETS_END"
    disconnect
} message options_dict]} {
    stage_d_fail $message $options_dict
}
puts "STAGE_D_JTAG_PROBE_PASS"
exit 0
