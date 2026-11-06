# Read-only recovery: no stop/reset/download/write or PS initialization.
puts "M14_RETAINED_STATE_BEGIN"
if {[catch {
    connect
    puts [targets]
    targets -set -nocase -filter {name =~ "PSU"}
    set read_errors 0
    foreach {label address count} {
        WEIGHT_FIRST 0x40000000 4
        WEIGHT_LAST 0x503A7FF0 4
        BUILD_CONFIG 0xA0000150 1
        CAPABILITIES 0xA0000160 1
    } {
        if {[catch {mrd -force -value $address $count} values]} {
            incr read_errors
            puts "M14_RETAINED_${label}_ERROR=$values"
        } else {
            puts "M14_RETAINED_$label=$values"
        }
    }
    disconnect
    if {$read_errors != 0} { error "$read_errors retained-state reads failed" }
} message options_dict]} {
    puts stderr "M14_RETAINED_STATE_ERROR: $message"
    catch {disconnect}
    exit 1
}
puts "M14_RETAINED_STATE=PASS"
exit 0
