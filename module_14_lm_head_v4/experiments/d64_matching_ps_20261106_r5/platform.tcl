set here [file dirname [file normalize [info script]]]
set module [file normalize [file join $here .. ..]]
set output [file join $module build d64_matching_ps_20261106_r5]
set xsa [file join $module reports d64_bit_xsa_20261106_r1 hardware m14_d64_200m.xsa]
if {[catch {
 if {[file exists $output]} {error "Preserve existing HSI output"}
 file mkdir [file join $output hw]
 file copy $xsa [file join $output hw m14_d64_200m.xsa]
 hsi::open_hw_design $xsa
 hsi::set_repo_path [list [file join $module ip_repo lm_head_v4_partial_proto_d64_r1]]
 hsi::create_sw_design m14_d64_bsp -proc psu_cortexa53_0 -os standalone
 set lib [hsi::add_library lwip211]
 foreach {name value} {mem_size 262144 tcp_snd_buf 32768 tcp_wnd 32768 pbuf_pool_size 256 memp_n_tcp_seg 512} {
  common::set_property CONFIG.$name $value $lib
 }
 hsi::generate_bsp -dir [file join $output bsp]
 puts "D64_MATCHING_BSP_RETURNED=PASS_OFFLINE_ONLY"
 hsi::close_sw_design [hsi::current_sw_design]
 hsi::close_hw_design [hsi::current_hw_design]
} message options]} {
 puts stderr "D64_MATCHING_BSP_ERROR: $message"
 if {[dict exists $options -errorinfo]} {puts stderr [dict get $options -errorinfo]}
 exit 1
}
exit 0
