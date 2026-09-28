proc read_register {name address} {
    if {[catch {set value [mrd -force $address]} message]} {
        puts "${name}=READ_ERROR|$message"
    } else {
        puts "${name}=$value"
    }
}

puts "PS_PL_STATE_INSPECT_BEGIN"
connect
if {![catch {
    targets -set -nocase -filter {name =~ "Cortex-A53 #0"}
    stop
    puts "A53_STOP=PASS"
} message]} {
    # A halted A53 also allows XSCT to fall back to processor-assisted reads
    # if the requested address is not served through direct DAP access.
} else {
    puts "A53_STOP=ERROR|$message"
}
targets -set -nocase -filter {name =~ "PSU"}
configparams force-mem-access 1

# PS GPIO bank 5 bit 31 drives pl_resetn0 in the generated psu_init sequence.
read_register "GPIO_DATA_5_PL_RESETN0" 0xFF0A0054
# PL0 reference clock: bit 24 is CLKACT.
read_register "PL0_REF_CTRL" 0xFF5E00C0
# AFI reset bits 7..12 include the FPD fabric interfaces.
read_register "RST_FPD_TOP" 0xFD1A0100
# PL power-up status.
read_register "PL_PWRUP_STATUS" 0xFFD80110
# HLS AXI-Lite control register, included last because this path is suspect.
read_register "LM_HEAD_AP_CTRL" 0xA0000000

configparams force-mem-access 0
disconnect
puts "PS_PL_STATE_INSPECT_END"
exit
