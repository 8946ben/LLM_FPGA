set_param general.maxThreads 2
set here [file dirname [file normalize [info script]]]
set module [file normalize [file join $here .. ..]]
set project [file join $module board build m14_d64_200m_r4]
set out [file join $module reports d64_bit_xsa_20261106_r1 hardware]
file mkdir $out
open_project [file join $project m14_d64_200m.xpr]
if {![string match "*Complete*" [get_property STATUS [get_runs impl_1]]]} {error "Audited route no longer complete"}
if {[file exists [file join $project m14_d64_200m.runs impl_1 m14_d64_system_wrapper.bit]]} {error "Preserve existing bitstream"}
launch_runs impl_1 -to_step write_bitstream -jobs 1
wait_on_run impl_1
if {![string match "*Complete*" [get_property STATUS [get_runs impl_1]]]} {error "Bitstream stage failed"}
set bit [file join $project m14_d64_200m.runs impl_1 m14_d64_system_wrapper.bit]
if {![file isfile $bit]} {error "Bitstream file missing"}
file copy $bit [file join $out m14_d64_200m.bit]
write_hw_platform -fixed -include_bit -file [file join $out m14_d64_200m.xsa]
puts "D64_MATCHING_BIT_XSA_RETURNED=PASS_NOT_BOARD"
close_project
exit
