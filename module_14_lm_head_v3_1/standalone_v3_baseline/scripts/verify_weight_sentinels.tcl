if {$argc != 1} {
    puts stderr "usage: verify_weight_sentinels.tcl <weight.bin>"
    exit 2
}
set weight_file [file normalize [lindex $argv 0]]
proc host_words {path offset} {
    set input [open $path rb]
    seek $input $offset start
    set data [read $input 16]
    close $input
    if {[string length $data] != 16} { error "short sentinel read" }
    binary scan $data cu* bytes
    set words {}
    for {set index 0} {$index < 16} {incr index 4} {
        lappend words [expr {[lindex $bytes $index] |
            ([lindex $bytes [expr {$index+1}]] << 8) |
            ([lindex $bytes [expr {$index+2}]] << 16) |
            ([lindex $bytes [expr {$index+3}]] << 24)}]
    }
    return $words
}
puts "M14_SENTINEL_VERIFY_BEGIN"
if {[catch {
    set size [file size $weight_file]
    if {$size != 272269312} { error "unexpected weight size=$size" }
    connect
    targets -set -nocase -filter {name =~ "PSU"}
    foreach {label offset} [list FIRST 0 LAST [expr {$size-16}]] {
        set expected [host_words $weight_file $offset]
        set actual [mrd -force -value [expr {0x40000000+$offset}] 4]
        if {[llength $actual] != 4} { error "$label sentinel length mismatch" }
        for {set index 0} {$index < 4} {incr index} {
            if {[expr {[lindex $actual $index] & 0xffffffff}] != [lindex $expected $index]} {
                error "$label word $index mismatch actual=$actual expected=$expected"
            }
        }
        puts "M14_SENTINEL_${label}=PASS words=$actual"
    }
    disconnect
} message options_dict]} {
    puts stderr "M14_SENTINEL_VERIFY_ERROR=$message"
    catch {disconnect}
    exit 1
}
puts "M14_SENTINEL_VERIFY=PASS"
exit 0
