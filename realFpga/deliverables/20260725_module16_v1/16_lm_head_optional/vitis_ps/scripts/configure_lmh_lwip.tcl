proc stage_f_fail {message options_dict} {
    puts stderr "STAGE_F_BSP_CONFIG_ERROR: $message"
    if {[dict exists $options_dict -errorinfo]} {
        puts stderr [dict get $options_dict -errorinfo]
    }
    exit 1
}

set workspace_dir "D:/program/LLM_FPGA/realFpga/vitis/workspace"
set platform_name "lm_head_axu9eg_platform"
set domain_name "standalone_domain"
set phy_reference "D:/program/LLM_FPGA/ref/xemacpsif_physpeed.c"
set phy_target "$workspace_dir/$platform_name/psu_cortexa53_0/$domain_name/bsp/psu_cortexa53_0/libsrc/lwip211_v1_5/src/contrib/ports/xilinx/netif/xemacpsif_physpeed.c"

puts "STAGE_F_BSP_CONFIG_BEGIN"
if {[catch {
    setws $workspace_dir
    platform active $platform_name
    domain active $domain_name

    # 2026-07-24 zb: larger raw-API windows for 260 MiB weight uploads and
    # optional 303872-byte logits responses.
    bsp config mem_size 262144
    bsp config tcp_snd_buf 32768
    bsp config tcp_wnd 32768
    bsp config pbuf_pool_size 256
    # TCP_SND_QUEUELEN becomes about 359 at a 32 KiB send buffer.
    # lwIP's compile-time sanity check therefore requires more than the
    # template's 256 TCP segments.
    bsp config memp_n_tcp_seg 512
    bsp write
    bsp regenerate

    # bsp regenerate restores the vendor PHY implementation. AXU9EGB needs
    # the colleague-provided generic-PHY fallback, so restore it every time.
    file copy -force $phy_reference $phy_target
    set patch_channel [open $phy_target r]
    set patch_text [read $patch_channel]
    close $patch_channel
    if {[string first "get_Generic_phy_speed" $patch_text] < 0} {
        error "AXU9EGB generic PHY patch restoration failed"
    }
    puts "PHY_PATCH_RESTORED=PASS"
    platform write

    puts "STAGE_F_BSP_CONFIG_VALUES"
    puts [bsp listparams -lib lwip211]
} message options_dict]} {
    stage_f_fail $message $options_dict
}
puts "STAGE_F_BSP_CONFIG_PASS"
exit 0
