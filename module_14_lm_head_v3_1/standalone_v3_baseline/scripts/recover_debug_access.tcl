# Recovery is within the user's explicit PS/PL reinitialization authorization.
# Use XSCT reset APIs only; do not guess memory-mapped reset registers.
puts "M14_DEBUG_RECOVERY_BEGIN"
if {[catch {
    connect
    puts "M14_TARGETS_BEFORE=[targets]"
    if {[catch {
        targets -set -nocase -filter {name =~ "DAP*"}
        rst -dap
    } message]} {
        puts "M14_DAP_RESET_UNAVAILABLE=$message"
    } else {
        puts "M14_DAP_RESET_DONE"
    }
    after 1000
    puts "M14_TARGETS_AFTER_DAP=[targets]"
    if {[catch {targets -set -nocase -filter {name =~ "PSU"}}]} {
        targets -set -nocase -filter {name =~ "PS TAP"}
        if {[catch {rst -por} message]} {
            puts "M14_POR_RESET_UNAVAILABLE=$message"
        } else {
            puts "M14_POR_RESET_DONE"
        }
        after 1000
        puts "M14_TARGETS_AFTER_POR=[targets]"
    }
    targets -set -nocase -filter {name =~ "PSU"}
    disconnect
} message options_dict]} {
    puts stderr "M14_DEBUG_RECOVERY_ERROR=$message"
    catch {disconnect}
    exit 1
}
puts "M14_DEBUG_RECOVERY=PASS"
exit 0
