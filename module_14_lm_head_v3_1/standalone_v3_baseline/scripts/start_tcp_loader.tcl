# init=1 for a fresh boot; init=0 retains DDR/PL and only replaces the A53 ELF.
if {$argc!=4} {puts stderr "usage: start_tcp_loader.tcl <bit> <psu_init> <loader.elf> <init:0|1>"; exit 2}
lassign $argv bit init_script elf initialize
if {$initialize ni {0 1}} {exit 2}
foreach path [list $bit $init_script $elf] {if {![file exists $path]} {puts stderr "missing: $path"; exit 2}}
if {[catch {
    connect
    if {$initialize==1} {
        targets -set -nocase -filter {name =~ "PSU"}
        rst -system
        after 2000
        source $init_script
        psu_init
        fpga -file $bit
        psu_ps_pl_isolation_removal
        psu_ps_pl_reset_config
        psu_post_config
    }
    targets -set -nocase -filter {name =~ "Cortex-A53 #0"}
    catch {stop}
    rst -processor
    dow $elf
    con
    disconnect
    puts "M14_TCP_LOADER_START=PASS"
} message options]} {
    puts stderr "M14_TCP_LOADER_ERROR: $message"
    if {[dict exists $options -errorinfo]} {puts stderr [dict get $options -errorinfo]}
    catch {disconnect}
    exit 1
}
exit 0
