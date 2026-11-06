proc fail {message options_dict} {
    puts stderr "M14_BOARD_PROGRAM_ERROR: $message"
    if {[dict exists $options_dict -errorinfo]} {
        puts stderr [dict get $options_dict -errorinfo]
    }
    catch {disconnect}
    exit 1
}

if {$argc != 3} {
    puts stderr "usage: program_and_load.tcl <bit> <psu_init.tcl> <weight.bin>"
    exit 2
}

set bit_file [file normalize [lindex $argv 0]]
set psu_init_file [file normalize [lindex $argv 1]]
set weight_file [file normalize [lindex $argv 2]]
foreach path [list $bit_file $psu_init_file $weight_file] {
    if {![file exists $path]} {
        puts stderr "M14_BOARD_PROGRAM_ERROR: missing file $path"
        exit 2
    }
}

if {[catch {
    puts "M14_BOARD_PROGRAM_BEGIN"
    connect
    targets -set -nocase -filter {name =~ "PSU"}
    rst -system
    after 2000

    targets -set -nocase -filter {name =~ "PSU"}
    source $psu_init_file
    psu_init
    puts "M14_BOARD_PSU_INIT_PASS"

    fpga -file $bit_file
    psu_ps_pl_isolation_removal
    psu_ps_pl_reset_config
    psu_post_config
    puts "M14_BOARD_FPGA_PROGRAM_PASS"

    targets -set -nocase -filter {name =~ "Cortex-A53 #0"}
    catch {stop}
    rst -processor
    dow -data $weight_file 0x40000000
    puts "M14_BOARD_WEIGHT_LOAD_PASS bytes=[file size $weight_file]"

    set first_words [mrd -force -value 0x40000000 4]
    set last_words [mrd -force -value 0x503A7FF0 4]
    puts "M14_BOARD_WEIGHT_FIRST=$first_words"
    puts "M14_BOARD_WEIGHT_LAST=$last_words"
    disconnect
} message options_dict]} {
    fail $message $options_dict
}

puts "M14_BOARD_PROGRAM_AND_LOAD=PASS"
exit 0
