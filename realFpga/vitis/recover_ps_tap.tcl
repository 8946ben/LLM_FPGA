proc recovery_fail {message options_dict} {
    puts stderr "PS_TAP_RECOVERY_ERROR: $message"
    if {[dict exists $options_dict -errorinfo]} {
        puts stderr [dict get $options_dict -errorinfo]
    }
    exit 1
}

puts "PS_TAP_RECOVERY_BEGIN"
if {[catch {
    connect
    puts "TARGETS_BEFORE=[targets]"
    targets -set -nocase -filter {name =~ "PL"}
    fpga -file "D:/program/LLM_FPGA/realFpga/vitis/workspace/lm_head_axu9eg_platform/export/lm_head_axu9eg_platform/hw/lm_head_axu9eg.bit"
    after 3000
    puts "TARGETS_AFTER=[targets]"
    disconnect
} message options_dict]} {
    catch {disconnect}
    recovery_fail $message $options_dict
}
puts "PS_TAP_RECOVERY_PASS"
exit 0
