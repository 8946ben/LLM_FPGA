proc inspect_fail {message options_dict} {
    puts stderr "HLS_RUNTIME_INSPECT_ERROR: $message"
    if {[dict exists $options_dict -errorinfo]} {
        puts stderr [dict get $options_dict -errorinfo]
    }
    exit 1
}

puts "HLS_RUNTIME_INSPECT_BEGIN"
if {[catch {
    connect
    targets -set -nocase -filter {name =~ "PSU"}
    puts "TARGETS=[targets]"
    configparams force-mem-access 1

    puts "HLS_REGISTERS_BEGIN"
    mrd 0xA0000000 32
    puts "HLS_REGISTERS_END"

    puts "DDR_WEIGHT_BEGIN"
    mrd 0x40000000 8
    puts "DDR_WEIGHT_END"
    puts "DDR_HIDDEN_BEGIN"
    mrd 0x503A8000 4
    puts "DDR_HIDDEN_END"
    puts "DDR_HISTORY_BEGIN"
    mrd 0x503A8700 2
    puts "DDR_HISTORY_END"

    targets -set -nocase -filter {name =~ "Cortex-A53 #0"}
    stop
    puts "A53_REGISTERS_BEGIN"
    rrd
    puts "A53_REGISTERS_END"
    configparams force-mem-access 0
    disconnect
} message options_dict]} {
    catch {configparams force-mem-access 0}
    catch {disconnect}
    inspect_fail $message $options_dict
}
puts "HLS_RUNTIME_INSPECT_PASS"
exit 0
