proc stage_d_fail {message options_dict} {
    puts stderr "STAGE_D_ERROR: $message"
    if {[dict exists $options_dict -errorinfo]} {
        puts stderr [dict get $options_dict -errorinfo]
    }
    exit 1
}

set workspace_dir "D:/program/LLM_FPGA/realFpga/vitis/workspace"
set platform_name "lm_head_axu9eg_platform"
set domain_name "standalone_domain"
set app_name "lm_head_net_diag"
set phy_patch_file "$workspace_dir/$platform_name/psu_cortexa53_0/$domain_name/bsp/psu_cortexa53_0/libsrc/lwip211_v1_5/src/contrib/ports/xilinx/netif/xemacpsif_physpeed.c"
set app_debug_dir "$workspace_dir/$app_name/Debug"
set app_elf "$app_debug_dir/$app_name.elf"
set app_map "$app_debug_dir/$app_name.map"

puts "STAGE_D_NET_APP_BUILD_BEGIN"
if {[catch {
    set patch_channel [open $phy_patch_file r]
    set patch_text [read $patch_channel]
    close $patch_channel
    if {[string first "get_Generic_phy_speed" $patch_text] < 0} {
        error "The required AXU9EGB generic PHY patch is missing from the BSP."
    }
    puts "PHY_PATCH_MARKER=PASS"

    setws $workspace_dir
    platform active $platform_name
    domain active $domain_name
    platform generate -domains $domain_name
    set patch_channel [open $phy_patch_file r]
    set patch_text [read $patch_channel]
    close $patch_channel
    if {[string first "get_Generic_phy_speed" $patch_text] < 0} {
        error "Platform generation overwrote the required AXU9EGB PHY patch."
    }
    puts "PHY_PATCH_AFTER_PLATFORM_GENERATE=PASS"
    app build -name $app_name

    # Vitis 2021.1 may regenerate/clean the managed Makefile yet return from
    # "app build" without producing an ELF. Run the generated Makefile
    # explicitly and verify concrete artifacts instead of trusting status text.
    puts "APP_DIRECT_MAKE_BEGIN"
    puts [exec make -C $app_debug_dir all 2>@1]
    puts "APP_DIRECT_MAKE_END"
    if {![file exists $app_elf]} {
        error "Application build reported success but ELF is missing: $app_elf"
    }
    if {![file exists $app_map]} {
        error "Application build reported success but linker map is missing: $app_map"
    }
    puts "APP_ELF_AND_MAP=PASS"

    puts "APP_REPORT_BEGIN"
    puts [app report -name $app_name]
    puts "APP_REPORT_END"
} message options_dict]} {
    stage_d_fail $message $options_dict
}
puts "STAGE_D_NET_APP_BUILD_PASS"
exit 0
