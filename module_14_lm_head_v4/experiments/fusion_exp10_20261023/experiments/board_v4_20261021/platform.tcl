# Offline BSP generation only. No connect/targets/fpga/dow/mrd/mwr commands.
set here [file dirname [file normalize [info script]]]
set module [file normalize [file join $here .. ..]]
set root [file normalize {D:/program/LLM_FPGA}]
set workspace [file normalize {D:/program/LLM_FPGA/.cache/e10_ps}]
set xsa [file join $module reports board_v4_20261021 hardware_r2 m14_v4_single.xsa]
set platform_name m14_v4_private_r2
if {[catch {
    if {![file isfile $xsa]} {error "Matching v4 XSA missing"}
    set resume [expr {[llength $argv] == 1 && [lindex $argv 0] eq "resume"}]
    if {[llength $argv] > 1 || ([llength $argv] == 1 && !$resume)} {error "Only explicit resume is supported"}
    set spr [file join $workspace $platform_name platform.spr]
    if {!$resume && [file exists [file dirname $spr]]} {error "Preserve existing platform; use audited resume"}
    file mkdir $workspace
    setws $workspace
    if {$resume} {
        if {![file isfile $spr]} {error "No platform to resume"}
        platform read $spr
    } else {
        platform create -name $platform_name -hw $xsa -proc psu_cortexa53_0 -os standalone
    }
    platform active $platform_name
    domain active standalone_domain
    bsp setlib -name lwip211
    bsp config mem_size 262144
    bsp config tcp_snd_buf 32768
    bsp config tcp_wnd 32768
    bsp config pbuf_pool_size 256
    bsp config memp_n_tcp_seg 512
    bsp write
    bsp regenerate
    set phy [file join $workspace $platform_name psu_cortexa53_0 standalone_domain bsp psu_cortexa53_0 libsrc lwip211_v1_5 src contrib ports xilinx netif xemacpsif_physpeed.c]
    if {![file isfile $phy]} {error "Generated BSP PHY source missing"}
    file copy -force [file join $root ref xemacpsif_physpeed.c] $phy
    platform write
    platform generate
    puts "M14_V4_PRIVATE_PLATFORM=PASS_OFFLINE_BSP_ONLY"
} message options]} {
    puts stderr "M14_V4_PRIVATE_PLATFORM_ERROR: $message"
    if {[dict exists $options -errorinfo]} {puts stderr [dict get $options -errorinfo]}
    exit 1
}
exit 0
