set here [file dirname [file normalize [info script]]]
set module [file normalize [file join $here .. ..]]
set workspace [file join $module build d64_matching_ps_20261106_r2 workspace]
set xsa [file join $module reports d64_bit_xsa_20261106_r1 hardware m14_d64_200m.xsa]
set platform_name m14_d64_200m
if {[catch {
 if {[file exists $workspace]} {error "Preserve existing workspace"}
 if {![file isfile $xsa]} {error "Matching audited XSA missing"}
 file mkdir $workspace
 setws $workspace
 platform create -name $platform_name -hw $xsa -proc psu_cortexa53_0 -os standalone
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
 set phy_files [glob -nocomplain [file join $workspace $platform_name psu_cortexa53_0 standalone_domain bsp psu_cortexa53_0 libsrc lwip211* src contrib ports xilinx netif xemacpsif_physpeed.c]]
 if {[llength $phy_files] != 1} {error "Expected exactly one generated PHY source"}
 file copy -force [file join $here xemacpsif_physpeed.c] [lindex $phy_files 0]
 platform write
 platform generate
 puts "D64_MATCHING_BSP_RETURNED=PASS_OFFLINE_ONLY"
} message options]} {
 puts stderr "D64_MATCHING_BSP_ERROR: $message"
 if {[dict exists $options -errorinfo]} {puts stderr [dict get $options -errorinfo]}
 exit 1
}
exit 0
