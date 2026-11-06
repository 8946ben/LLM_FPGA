if {$argc!=1} {puts stderr "usage: read_tcp_diagnostics.tcl <binary_dump>"; exit 2}
if {[catch {
    connect
    targets -set -nocase -filter {name =~ "PSU"}
    mrd -force -bin -file [lindex $argv 0] -size w 0x51001000 256
    disconnect
    puts "M14_TCP_DIAGNOSTICS=PASS"
} message]} {puts stderr $message; catch {disconnect}; exit 1}
exit 0
