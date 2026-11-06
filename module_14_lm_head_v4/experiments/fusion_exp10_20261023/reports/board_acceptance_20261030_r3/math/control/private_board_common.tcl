# Library only. Sourcing this file never connects to hardware.
proc lmh4_u32 {word} {
    if {[regexp {^0[xX][0-9a-fA-F]+$} $word]} {
        set n [expr {wide($word)}]
    } elseif {[regexp {^(0|[1-9][0-9]*)$} $word]} {
        scan $word %lld n
    } else {error "Invalid unsigned MMIO word: $word"}
    if {$n < 0 || $n > 0xffffffff} {error "MMIO word outside uint32"}
    return $n
}
proc lmh4_r32 {address} {return [lmh4_u32 [lindex [mrd -force -value $address 1] 0]]}
proc lmh4_require_ready {{timeout_ms 30000}} {
    if {[lmh4_r32 0xa0020008] != 0x4d345a0a} {error "Private image signature mismatch"}
    set deadline [expr {[clock milliseconds]+$timeout_ms}]
    while {([lmh4_r32 0xa0020000] & 1) == 0} {
        if {[clock milliseconds] >= $deadline} {error "MIG calibration timeout"}
        after 10
    }
    if {([lmh4_r32 0xa0000000] & 0x85) != 4} {error "Selector busy/auto-restart; refuse memory/ELF mutation"}
}
proc lmh4_stop_gem {base {timeout_ms 2000}} {
    if {$base ni {0xff0b0000 0xff0c0000 0xff0d0000 0xff0e0000}} {error "Unrecognized GEM base"}
    # Caller already halted the loader CPU. Values from the matched v4 BSP:
    # xemacps_hw.h NWCTRL=0, IDR=0x2c, TXSR=0x14; RXEN4/TXEN8/TXGO8.
    # XEmacPs_Stop disables interrupts and clears RX/TX; its documented DMA
    # channel stop blocks until DMA completes. Also request TX halt and verify
    # TXGO/readback before allowing any ELF replacement. Real target NOT_RUN.
    mwr -force [expr {$base+0x2c}] 0x7fff
    set ncr [lmh4_r32 $base]
    mwr -force $base [expr {($ncr & ~0x204) | 0x400}]
    set deadline [expr {[clock milliseconds]+$timeout_ms}]
    while {([lmh4_r32 [expr {$base+0x14}]] & 8) != 0} {
        if {[clock milliseconds] >= $deadline} {error "GEM TXGO stuck; do not replace ELF"}
        after 1
    }
    mwr -force $base [expr {[lmh4_r32 $base] & ~0x60c}]
    for {set i 0} {$i < 3} {incr i} {
        if {([lmh4_r32 $base] & 0xc) != 0 || ([lmh4_r32 [expr {$base+0x14}]] & 8) != 0} {
            error "GEM stop readback failed; do not replace ELF"
        }
        after 1
    }
    puts [format "M4_GEM_STOP_READBACK=PASS base=0x%08x" $base]
}
proc lmh4_loader_start {bit init elf xsa} {
    foreach p [list $bit $init $elf $xsa] {if {![file isfile $p]} {error "Missing bound file: $p"}}
    connect
    targets -set -nocase -filter {name =~ "PSU"}
    rst -system
    after 2000
    # Generated init data variables must live in the global namespace.
    uplevel #0 [list source $init]
    psu_init
    fpga -file $bit
    psu_ps_pl_isolation_removal
    psu_ps_pl_reset_config
    psu_post_config
    loadhw -hw $xsa
    lmh4_require_ready
    targets -set -nocase -filter {name =~ "Cortex-A53 #0"}
    if {[catch {stop} stop_message stop_options]} {
        if {![string match {*APU L2 cache is held in reset*} $stop_message]} {return -options $stop_options $stop_message}
        puts "M4_INITIAL_STOP_ALREADY_IN_RESET=$stop_message"
    }
    rst -processor
    dow $elf
    con
    disconnect
    puts "M4_PRIVATE_LOADER_STARTED"
}
proc lmh4_quiesce {gem} {
    connect
    targets -set -nocase -filter {name =~ "PSU"}
    lmh4_require_ready
    targets -set -nocase -filter {name =~ "Cortex-A53 #0"}
    stop
    targets -set -nocase -filter {name =~ "PSU"}
    lmh4_stop_gem $gem
    disconnect
    puts "M4_PRIVATE_CPU_GEM_QUIESCED"
}
proc lmh4_run_campaign {elf request xsa gem header records timeout_s} {
    if {![string is integer -strict $timeout_s] || $timeout_s < 1 || $timeout_s > 7200} {error "Invalid timeout"}
    foreach p [list $elf $request $xsa] {if {![file isfile $p]} {error "Missing bound file: $p"}}
    foreach p [list $header $records] {if {[file exists $p]} {error "Preserve prior capture: $p"}}
    connect
    targets -set -nocase -filter {name =~ "PSU"}
    lmh4_require_ready
    targets -set -nocase -filter {name =~ "Cortex-A53 #0"}
    stop
    targets -set -nocase -filter {name =~ "PSU"}
    lmh4_stop_gem $gem
    targets -set -nocase -filter {name =~ "Cortex-A53 #0"}
    rst -processor
    loadhw -hw $xsa
    dow $elf
    dow -data $request 0x51000000
    con
    targets -set -nocase -filter {name =~ "PSU"}
    set deadline [expr {[clock milliseconds]+1000*$timeout_s}]
    set phase 0
    while {[clock milliseconds] < $deadline} {
        set phase [lmh4_r32 0x51000034]
        if {$phase == 3 || $phase == 4} {break}
        after 100
    }
    if {$phase != 3 && $phase != 4} {
        # IP may still run. Halt CPU only, do not alter DDR or start next job.
        targets -set -nocase -filter {name =~ "Cortex-A53 #0"}
        stop
        error "Campaign timeout; IP may still be running, explicit recovery required"
    }
    mrd -force -bin -file $header -size w 0x51000000 32
    set count [lmh4_r32 0x51000038]
    if {$count > 2048} {error "Capture count exceeds reserved memory"}
    if {$count > 0} {mrd -force -bin -file $records -size w 0x51001000 [expr {$count*32}]} else {
        set f [open $records {WRONLY CREAT EXCL}];close $f
    }
    targets -set -nocase -filter {name =~ "Cortex-A53 #0"}
    stop
    disconnect
    if {$phase != 3} {error "Campaign failed; raw capture preserved"}
    puts "M4_PRIVATE_CAPTURE_COMPLETE_PENDING_HOST_VALIDATION"
}
