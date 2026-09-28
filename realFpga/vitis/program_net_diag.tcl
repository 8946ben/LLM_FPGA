proc stage_d_fail {message options_dict} {
    puts stderr "STAGE_D_ERROR: $message"
    if {[dict exists $options_dict -errorinfo]} {
        puts stderr [dict get $options_dict -errorinfo]
    }
    exit 1
}

set bit_file "D:/program/LLM_FPGA/realFpga/vitis/workspace/lm_head_axu9eg_platform/export/lm_head_axu9eg_platform/hw/lm_head_axu9eg.bit"
set elf_file "D:/program/LLM_FPGA/realFpga/vitis/workspace/lm_head_net_diag/Debug/lm_head_net_diag.elf"
set psu_init_file "D:/program/LLM_FPGA/realFpga/vitis/workspace/lm_head_axu9eg_platform/export/lm_head_axu9eg_platform/hw/psu_init.tcl"

puts "STAGE_D_BOARD_PROGRAM_BEGIN"
if {[catch {
    connect

    targets -set -nocase -filter {name =~ "PSU"}
    puts "BOARD_SYSTEM_RESET_BEGIN"
    rst -system
    after 3000
    puts "BOARD_SYSTEM_RESET_END"

    configparams force-mem-access 1
    targets -set -nocase -filter {name =~ "Cortex-A53 #0"}
    rst -processor -clear-registers

    # Initialize PS clocks, DDR and AFI before configuring PL.  This matches
    # the normal ZynqMP standalone download sequence and ensures that pl_clk0
    # and the HP0/HPM0 paths are valid when the PL image leaves reset.
    puts "PS_INITIALIZATION_BEGIN"
    source $psu_init_file
    psu_init
    puts "PS_INITIALIZATION_END"

    puts "FPGA_PROGRAM_BEGIN"
    fpga -file $bit_file
    puts "FPGA_PROGRAM_END"

    puts "PS_PL_RELEASE_BEGIN"
    psu_ps_pl_isolation_removal
    psu_ps_pl_reset_config
    after 1000
    puts "PS_PL_RELEASE_END"

    # Do not launch the application until a harmless AXI-Lite read/write/read
    # confirms that the HLS control slave is alive.  AP_CTRL is only read; the
    # hidden_size argument is written and restored without setting ap_start.
    puts "HLS_CONTROL_PREFLIGHT_BEGIN"
    targets -set -nocase -filter {name =~ "PSU"}
    configparams force-mem-accesses 1
    puts "HLS_AP_CTRL=[mrd -force 0xA0000000 1]"
    mwr -force 0xA0000040 0x00000004
    puts "HLS_HIDDEN_SIZE_TEST=[mrd -force 0xA0000040 1]"
    mwr -force 0xA0000040 0x00000000
    puts "HLS_CONTROL_PREFLIGHT_PASS"

    # The preflight deliberately targets the top-level PSU so AXI-Lite access
    # does not depend on executing debug instructions on A53.  ELF download and
    # `con` require a processor context, so explicitly select A53 #0 again.
    targets -set -nocase -filter {name =~ "Cortex-A53 #0"}
    puts "APPLICATION_DOWNLOAD_BEGIN"
    dow $elf_file
    puts "APPLICATION_DOWNLOAD_END"
    configparams force-mem-access 0

    con
    after 1000
    puts "A53_TARGET_STATUS=[targets]"
    disconnect
} message options_dict]} {
    catch {configparams force-mem-access 0}
    catch {disconnect}
    stage_d_fail $message $options_dict
}
puts "STAGE_D_BOARD_PROGRAM_PASS"
exit 0
