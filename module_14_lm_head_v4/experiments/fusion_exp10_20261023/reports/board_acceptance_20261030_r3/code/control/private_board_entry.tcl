# Only the explicit Python --execute path invokes XSCT with this entry point.
source [file join [file dirname [info script]] private_board_common.tcl]
if {[catch {
    set action [lindex $argv 0]
    if {$action eq "loader" && [llength $argv] == 5} {
        lmh4_loader_start {*}[lrange $argv 1 end]
    } elseif {$action eq "campaign" && [llength $argv] == 8} {
        lmh4_run_campaign {*}[lrange $argv 1 end]
    } elseif {$action eq "quiesce" && [llength $argv] == 2} {
        lmh4_quiesce [lindex $argv 1]
    } else {error "Expected loader plus4 args, or campaign plus7 args"}
} message options]} {
    puts stderr "M4_PRIVATE_BOARD_ERROR: $message"
    puts stderr [dict get $options -errorinfo]
    catch {disconnect}
    exit 1
}
exit 0
