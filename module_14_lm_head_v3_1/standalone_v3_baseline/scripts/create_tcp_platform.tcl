# Build-only: this script never connects to the board.
set standalone [file dirname [file dirname [file normalize [info script]]]]
set module [file dirname $standalone]
set root [file dirname $module]
set workspace [file join $standalone tcp_workspace]
if {[catch {
    file mkdir $workspace
    setws $workspace
    if {![file isdirectory [file join $workspace m14_tcp_platform]]} {
        platform create -name m14_tcp_platform -hw [file join $module reports board_package_20261009 m14_v2_single.xsa] -proc psu_cortexa53_0 -os standalone
    }
    platform active m14_tcp_platform
    domain active standalone_domain
    bsp setlib -name lwip211
    bsp config mem_size 262144
    bsp config tcp_snd_buf 32768
    bsp config tcp_wnd 32768
    bsp config pbuf_pool_size 256
    bsp config memp_n_tcp_seg 512
    bsp write
    bsp regenerate
    # Same AXU9EGB generic PHY fallback as the previously tested TCP service.
    set phy [file join $workspace m14_tcp_platform psu_cortexa53_0 standalone_domain bsp psu_cortexa53_0 libsrc lwip211_v1_5 src contrib ports xilinx netif xemacpsif_physpeed.c]
    file copy -force [file join $root ref xemacpsif_physpeed.c] $phy
    platform write
    platform generate
    puts "M14_TCP_PLATFORM=PASS"
} message options]} {
    puts stderr "M14_TCP_PLATFORM_ERROR: $message"
    if {[dict exists $options -errorinfo]} {puts stderr [dict get $options -errorinfo]}
    exit 1
}
exit 0
