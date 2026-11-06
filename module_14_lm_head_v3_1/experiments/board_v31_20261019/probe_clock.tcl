# Read back the PS clock chain after initialization (not a frequency counter).
set mhz 200
if {$argc == 1} {set mhz [lindex $argv 0]}
if {$mhz ni {100 200}} {error "Expected 100 or 200 MHz"}
if {[catch {
    connect
    targets -set -nocase -filter {name =~ "PSU"}
    set pl0 [lindex [mrd -force -value 0xFF5E00C0 1] 0]
    set dpll [lindex [mrd -force -value 0xFD1A002C 1] 0]
    set to_lpd [lindex [mrd -force -value 0xFD1A004C 1] 0]
    puts [format "M14_CLOCK_PL0_REF_CTRL=0x%08X" $pl0]
    puts [format "M14_CLOCK_DPLL_CTRL=0x%08X" $dpll]
    puts [format "M14_CLOCK_DPLL_TO_LPD_CTRL=0x%08X" $to_lpd]
    set expected 0x01010203
    if {$mhz == 100} {set expected 0x01010403}
    if {($pl0 & 0x013F3F07) != $expected} {error "PL0 source/dividers do not match $mhz MHz profile"}
    if {($dpll & 0x00717F09) != 0x00014800} {error "DPLL FBDIV/DIV2/bypass/reset differs from XSA"}
    if {($to_lpd & 0x00003F00) != 0x00000300} {error "DPLL-to-LPD divisor differs from XSA"}
    disconnect
    puts "M14_BOARD${mhz}_CLOCK_REGISTERS=PASS"
} message options]} {
    puts stderr "M14_BOARD200_CLOCK_ERROR: $message"
    catch {disconnect}
    exit 1
}
exit 0
