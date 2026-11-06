proc fail {message options_dict} {
    puts stderr "M14_BOARD_RUN_ERROR: $message"
    if {[dict exists $options_dict -errorinfo]} {
        puts stderr [dict get $options_dict -errorinfo]
    }
    catch {disconnect}
    exit 1
}

if {$argc != 7} {
    puts stderr "usage: run_step.tcl <hidden> <history> <mailbox> <elf> <mailbox_dump> <logits_dump_or_dash> <timeout_s>"
    exit 2
}

set hidden_file [file normalize [lindex $argv 0]]
set history_file [file normalize [lindex $argv 1]]
set mailbox_file [file normalize [lindex $argv 2]]
set elf_file [file normalize [lindex $argv 3]]
set mailbox_dump [file normalize [lindex $argv 4]]
set logits_arg [lindex $argv 5]
set timeout_s [lindex $argv 6]
foreach path [list $hidden_file $history_file $mailbox_file $elf_file] {
    if {![file exists $path]} {
        puts stderr "M14_BOARD_RUN_ERROR: missing file $path"
        exit 2
    }
}

if {[catch {
    puts "M14_BOARD_RUN_BEGIN"
    connect
    targets -set -nocase -filter {name =~ "Cortex-A53 #0"}
    catch {stop}
    rst -processor
    dow -data $hidden_file 0x503A8000
    dow -data $history_file 0x503A8700
    dow -data $mailbox_file 0x51000000
    dow $elf_file
    con

    set state 0
    set deadline [expr {[clock milliseconds] + ($timeout_s * 1000)}]
    targets -set -nocase -filter {name =~ "PSU"}
    while {[clock milliseconds] < $deadline} {
        set state [lindex [mrd -force -value 0x51000008 1] 0]
        if {$state == 0x444F4E45 || $state == 0x4641494C} {
            break
        }
        after 100
    }
    if {$state != 0x444F4E45 && $state != 0x4641494C} {
        error [format "mailbox timeout state=0x%08X" $state]
    }

    mrd -force -bin -file $mailbox_dump -size w 0x51000000 64
    if {$logits_arg ne "-"} {
        set logits_dump [file normalize $logits_arg]
        mrd -force -bin -file $logits_dump -size w 0x503AD140 151936
        puts "M14_BOARD_LOGITS_DUMP=$logits_dump"
    }
    puts [format "M14_BOARD_MAILBOX_STATE=0x%08X" $state]
    puts "M14_BOARD_MAILBOX_DUMP=$mailbox_dump"
    disconnect
} message options_dict]} {
    fail $message $options_dict
}

puts "M14_BOARD_RUN_STEP=PASS"
exit 0
