# Plain tclsh only: every hardware command is a mock. Never loads XSCT.
if {$argc != 1} {error "usage: test_retained_identity.tcl module_root"}
set module [file normalize [lindex $argv 0]]
set temp [file join $module build address_contract mock_retained_identity]
file mkdir $temp
foreach name {bit init elf input} {close [open [file join $temp $name] w]}
rename puts real_puts
proc puts {args} {return}
rename exit real_exit
proc exit {code} {error "MOCK_EXIT:$code"}
foreach name {connect disconnect targets stop rst con fpga} {proc $name {args} {return}}
proc after {args} {return}
proc dow {args} {incr ::download_count}
proc mrd {args} {
    if {[lsearch -exact $args -bin] >= 0} {return}
    if {[lsearch -exact $args 0xA0000150] >= 0} {return [list $::mock_build]}
    if {[lsearch -exact $args 0xA0000160] >= 0} {return [list $::mock_caps]}
    if {[lsearch -exact $args 0x51000008] >= 0} {return {0x444F4E45}}
    if {[lsearch -exact $args 0xA0020000] >= 0} {return {0x00000001}}
    error "Unexpected mocked memory read: $args"
}
set checks 0
foreach script {start_tcp_loader.tcl initialize_selftest.tcl} {
    if {$script eq "start_tcp_loader.tcl"} {
        set test_argv [list [file join $temp bit] [file join $temp init] [file join $temp elf] 0]
        set expected_downloads 1
    } else {
        set test_argv [list [file join $temp bit] [file join $temp init] [file join $temp elf] \
                           [file join $temp input] [file join $temp output] 0]
        set expected_downloads 2
    }
    foreach {build caps good} {0x30c08011 0x382 1 817922065 898 1 30c08011 00000382 1 0x20c08011 0x382 0 549486609 898 0 0x30c08011 0x182 0 invalid 0x382 0 0 0 0} {
        set mock_build $build
        set mock_caps $caps
        set download_count 0
        set argv $test_argv
        set argc [llength $argv]
        set result_code [catch {source [file join $module standalone scripts $script]} result]
        set wanted [expr {$good ? 0 : 1}]
        if {!$result_code || $result ne "MOCK_EXIT:$wanted" ||
            ($good && $download_count != $expected_downloads) || (!$good && $download_count != 0)} {
            real_puts stderr "MOCK_ONLY_FAILED $script build=$build caps=$caps result=$result downloads=$download_count"
            real_exit 1
        }
        incr checks
    }
}
# Cold-start branch: all commands remain mocked, including the identity call.
foreach name {psu_init psu_ps_pl_isolation_removal psu_ps_pl_reset_config psu_post_config} {proc $name {} {return}}
rename mrd retained_mrd
proc mwr {args} {
    set address [lindex $args 1]
    set value [lindex $args 2]
    if {$address == 0xA0000078 && $value == 0} {return}
    if {$address == 0xA0000000 && $value == 1} {set ::probe_started 1; return}
    error "Unexpected identity write: $args"
}
proc mrd {args} {
    set address [lindex $args 2]
    # Real DAP capture returned idle after the clear-on-read done was gone.
    if {$address == 0xA0000000} {return {4}}
    if {$address == 0xA00000C0} {return [list $::probe_status]}
    if {$address in {0xA0000110 0xA0000114 0xA0000128 0xA000012C 0xA0000180 0xA0000184}} {return [list $::probe_beats]}
    if {$::probe_started} {set ::mock_build $::probe_build;set ::mock_caps 0x382}
    return [retained_mrd {*}$args]
}
lset test_argv end 1
set cold_diag_argv $test_argv
foreach cold_script {initialize_selftest.tcl start_tcp_loader.tcl} {
    set test_argv $cold_diag_argv
    set cold_downloads 2
    if {$cold_script eq "start_tcp_loader.tcl"} {
        set test_argv [list [file join $temp bit] [file join $temp init] [file join $temp elf] 1]
        set cold_downloads 1
    }
foreach {status beats build good} {1 0 0x30c08011 1 0 0 0x30c08011 0 1 1 0x30c08011 0 1 0 0x20c08011 0} {
    set probe_started 0;set probe_status $status;set probe_beats $beats;set probe_build $build
    set mock_build 0;set mock_caps 0;set download_count 0
    set argv $test_argv;set argc [llength $argv]
    set result_code [catch {source [file join $module standalone scripts $cold_script]} result]
    set wanted [expr {$good ? 0 : 1}]
    if {!$result_code || $result ne "MOCK_EXIT:$wanted" || !$probe_started ||
        ($good && $download_count != $cold_downloads) || (!$good && $download_count != 0)} {
        real_puts stderr "MOCK_COLD_FAILED script=$cold_script status=$status beats=$beats build=$build result=$result downloads=$download_count"
        real_exit 1
    }
    incr checks
}
}
real_puts "OFFLINE_MOCK_ONLY_RETENTION_IDENTITY=PASS checks=$checks hardware_access=NONE"
real_exit 0
