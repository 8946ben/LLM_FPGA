# Matching 200 MHz XSA; no reuse of the accepted 100 MHz workspace.
set here [file dirname [file normalize [info script]]]
set module [file normalize [file join $here .. ..]]
set root [file dirname $module]
set workspace [file join $module build board200_20261019 workspace]
set xsa [file join $module reports board200_20261019 hardware m14_v2_single.xsa]
if {[catch {
    if {![file exists $xsa]} {error "Matching XSA missing"}
    if {[file exists [file join $workspace m14_board200_platform]]} {error "Preserve existing platform"}
    file mkdir $workspace
    setws $workspace
    platform create -name m14_board200_platform -hw $xsa -proc psu_cortexa53_0 -os standalone
    platform active m14_board200_platform
    domain active standalone_domain
    bsp setlib -name lwip211
    bsp config mem_size 262144
    bsp config tcp_snd_buf 32768
    bsp config tcp_wnd 32768
    bsp config pbuf_pool_size 256
    bsp config memp_n_tcp_seg 512
    bsp write
    bsp regenerate
    set phy [file join $workspace m14_board200_platform psu_cortexa53_0 standalone_domain bsp psu_cortexa53_0 libsrc lwip211_v1_5 src contrib ports xilinx netif xemacpsif_physpeed.c]
    file copy -force [file join $root ref xemacpsif_physpeed.c] $phy
    platform write
    platform generate
    puts "M14_BOARD200_PLATFORM=PASS"
} message options]} {
    puts stderr "M14_BOARD200_PLATFORM_ERROR: $message"
    if {[dict exists $options -errorinfo]} {puts stderr [dict get $options -errorinfo]}
    exit 1
}
exit 0
