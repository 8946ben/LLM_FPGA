source {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_acceptance_20261030_r3/math/control/private_board_common.tcl}
if {[catch {
connect
targets -set -nocase -filter {name =~ "PSU"}
lmh4_require_ready
if {[lmh4_r32 0x400100000]!=0x4353344d} {error "Initial descriptor differs"}
if {[lmh4_r32 0x400100004]!=0xd0002} {error "Initial descriptor differs"}
if {[lmh4_r32 0x400100008]!=0xf0} {error "Initial descriptor differs"}
if {[lmh4_r32 0x40010000c]!=0x0} {error "Initial descriptor differs"}
if {[lmh4_r32 0x400100010]!=0x6} {error "Initial descriptor differs"}
if {[lmh4_r32 0x400100014]!=0x3f8ccccd} {error "Initial descriptor differs"}
if {[lmh4_r32 0x400100018]!=0x4000} {error "Initial descriptor differs"}
if {[lmh4_r32 0x40010001c]!=0x8507826e} {error "Initial descriptor differs"}
if {[lmh4_r32 0x400100020]!=0x100100} {error "Initial descriptor differs"}
if {[lmh4_r32 0x400100024]!=0x0} {error "Initial descriptor differs"}
if {[lmh4_r32 0x400100028]!=0x103a8000} {error "Initial descriptor differs"}
if {[lmh4_r32 0x40010002c]!=0x0} {error "Initial descriptor differs"}
if {[lmh4_r32 0x400100030]!=0x104a8140} {error "Initial descriptor differs"}
if {[lmh4_r32 0x400100034]!=0x0} {error "Initial descriptor differs"}
if {[lmh4_r32 0x400100038]!=0x700} {error "Initial descriptor differs"}
if {[lmh4_r32 0x40010003c]!=0x0} {error "Initial descriptor differs"}
if {[lmh4_r32 0x400100040]!=0x104a8880} {error "Initial descriptor differs"}
if {[lmh4_r32 0x400100044]!=0x0} {error "Initial descriptor differs"}
if {[lmh4_r32 0x400100048]!=0x4a30} {error "Initial descriptor differs"}
if {[lmh4_r32 0x40010004c]!=0x0} {error "Initial descriptor differs"}
if {[lmh4_r32 0x400100050]!=0x104ad300} {error "Initial descriptor differs"}
if {[lmh4_r32 0x400100054]!=0x0} {error "Initial descriptor differs"}
if {[lmh4_r32 0x400100058]!=0x128c000} {error "Initial descriptor differs"}
if {[lmh4_r32 0x40010005c]!=0x0} {error "Initial descriptor differs"}
if {[lmh4_r32 0x400100060]!=0x11739340} {error "Initial descriptor differs"}
if {[lmh4_r32 0x400100064]!=0x0} {error "Initial descriptor differs"}
if {[lmh4_r32 0x400100068]!=0x1c000} {error "Initial descriptor differs"}
if {[lmh4_r32 0x40010006c]!=0x0} {error "Initial descriptor differs"}
if {[lmh4_r32 0x400100070]!=0x11755380} {error "Initial descriptor differs"}
if {[lmh4_r32 0x400100074]!=0x0} {error "Initial descriptor differs"}
if {[lmh4_r32 0x400100078]!=0x70000} {error "Initial descriptor differs"}
if {[lmh4_r32 0x40010007c]!=0x0} {error "Initial descriptor differs"}
if {[lmh4_r32 0x400100080]!=0x117c53c0} {error "Initial descriptor differs"}
if {[lmh4_r32 0x400100084]!=0x0} {error "Initial descriptor differs"}
if {[lmh4_r32 0x400100088]!=0x400} {error "Initial descriptor differs"}
if {[lmh4_r32 0x40010008c]!=0x0} {error "Initial descriptor differs"}
if {[lmh4_r32 0x400100090]!=0x117c5800} {error "Initial descriptor differs"}
if {[lmh4_r32 0x400100094]!=0x0} {error "Initial descriptor differs"}
if {[lmh4_r32 0x400100098]!=0x800000} {error "Initial descriptor differs"}
if {[lmh4_r32 0x40010009c]!=0x0} {error "Initial descriptor differs"}
if {[lmh4_r32 0x4001000a0]!=0x11fc5840} {error "Initial descriptor differs"}
if {[lmh4_r32 0x4001000a4]!=0x0} {error "Initial descriptor differs"}
if {[lmh4_r32 0x4001000a8]!=0x400} {error "Initial descriptor differs"}
if {[lmh4_r32 0x4001000ac]!=0x0} {error "Initial descriptor differs"}
if {[lmh4_r32 0x4001000b0]!=0x11fc5c80} {error "Initial descriptor differs"}
if {[lmh4_r32 0x4001000b4]!=0x0} {error "Initial descriptor differs"}
if {[lmh4_r32 0x4001000b8]!=0x94600} {error "Initial descriptor differs"}
if {[lmh4_r32 0x4001000bc]!=0x0} {error "Initial descriptor differs"}
if {[lmh4_r32 0x4001000c0]!=0x1205a2c0} {error "Initial descriptor differs"}
if {[lmh4_r32 0x4001000c4]!=0x0} {error "Initial descriptor differs"}
if {[lmh4_r32 0x4001000c8]!=0x94610} {error "Initial descriptor differs"}
if {[lmh4_r32 0x4001000cc]!=0x0} {error "Initial descriptor differs"}
if {[lmh4_r32 0x4001000d0]!=0x120ee940} {error "Initial descriptor differs"}
if {[lmh4_r32 0x4001000d4]!=0x0} {error "Initial descriptor differs"}
if {[lmh4_r32 0x4001000d8]!=0x94610} {error "Initial descriptor differs"}
if {[lmh4_r32 0x4001000dc]!=0x0} {error "Initial descriptor differs"}
if {[lmh4_r32 0x4001000e0]!=0x0} {error "Initial descriptor differs"}
if {[lmh4_r32 0x4001000e4]!=0x0} {error "Initial descriptor differs"}
if {[lmh4_r32 0x4001000e8]!=0x0} {error "Initial descriptor differs"}
if {[lmh4_r32 0x4001000ec]!=0x0} {error "Initial descriptor differs"}
mwr -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/selector_integration_fixture_20261021/descriptor_debug.bin} -size w 0x400100000
lmh4_require_ready
mwr -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/fixture/math.hidden.bin} -size w 0x4104a8140
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/0_math/hidden.bin} -size w 0x4104a8140 448
mwr -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/fixture/math.history.bin} -size w 0x4104a8880
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/0_math/history.bin} -size w 0x4104a8880 4748
mwr -force 0xa0000040 0
mwr -force 0xa0000000 1
set deadline [expr {[clock milliseconds]+60000}]
while {([lmh4_r32 0xa0000000]&2)==0} {
 if {[clock milliseconds]>=$deadline} {error "ABA timeout; do not mutate/reload"}
 after 1
}
if {[lmh4_r32 0xa0000048]!=0 || [lmh4_r32 0xa0000058]!=6 || [lmh4_r32 0xa0000068]!=0} {error "ABA hardware failure"}
if {[lmh4_r32 0xa0000088]!=17106} {error "ABA candidate count differs"}
puts "M4_ABA_0_TOKEN=[lmh4_r32 0xa00000a8]"
puts "M4_ABA_0_SCORE=[lmh4_r32 0xa00000b8]"
puts "M4_ABA_0_CRC=[lmh4_r32 0xa00000c8]"
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/0_math/preview.bin} -size w 0x411fc5c80 151936
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/0_math/merged.bin} -size w 0x4120ee940 17112
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/0_math/raw.bin} -size w 0x412182fc0 34212
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/0_math/guard_weight.bin} -size w 0x4104a8100 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/0_math/guard_hidden.bin} -size w 0x4104a8840 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/0_math/guard_history.bin} -size w 0x4104ad2b0 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/0_math/guard_a.bin} -size w 0x411739300 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/0_math/guard_bt.bin} -size w 0x411755340 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/0_math/guard_centers.bin} -size w 0x4117c5380 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/0_math/guard_norms.bin} -size w 0x4117c57c0 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/0_math/guard_ranked.bin} -size w 0x411fc5800 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/0_math/guard_counts.bin} -size w 0x411fc5c40 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/0_math/guard_preview.bin} -size w 0x41205a280 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/0_math/guard_routed.bin} -size w 0x4120ee8d0 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/0_math/guard_merged.bin} -size w 0x412182f50 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/0_math/guard_sparse.bin} -size w 0x4122abbc0 4
puts "M4_ABA_STEP_RETURNED 0 math K=17106"
lmh4_require_ready
mwr -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/fixture/chinese.hidden.bin} -size w 0x4104a8140
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/1_chinese/hidden.bin} -size w 0x4104a8140 448
mwr -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/fixture/chinese.history.bin} -size w 0x4104a8880
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/1_chinese/history.bin} -size w 0x4104a8880 4748
mwr -force 0xa0000040 0
mwr -force 0xa0000000 1
set deadline [expr {[clock milliseconds]+60000}]
while {([lmh4_r32 0xa0000000]&2)==0} {
 if {[clock milliseconds]>=$deadline} {error "ABA timeout; do not mutate/reload"}
 after 1
}
if {[lmh4_r32 0xa0000048]!=0 || [lmh4_r32 0xa0000058]!=6 || [lmh4_r32 0xa0000068]!=0} {error "ABA hardware failure"}
if {[lmh4_r32 0xa0000088]!=17764} {error "ABA candidate count differs"}
puts "M4_ABA_1_TOKEN=[lmh4_r32 0xa00000a8]"
puts "M4_ABA_1_SCORE=[lmh4_r32 0xa00000b8]"
puts "M4_ABA_1_CRC=[lmh4_r32 0xa00000c8]"
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/1_chinese/preview.bin} -size w 0x411fc5c80 151936
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/1_chinese/merged.bin} -size w 0x4120ee940 17768
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/1_chinese/raw.bin} -size w 0x412182fc0 35528
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/1_chinese/guard_weight.bin} -size w 0x4104a8100 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/1_chinese/guard_hidden.bin} -size w 0x4104a8840 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/1_chinese/guard_history.bin} -size w 0x4104ad2b0 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/1_chinese/guard_a.bin} -size w 0x411739300 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/1_chinese/guard_bt.bin} -size w 0x411755340 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/1_chinese/guard_centers.bin} -size w 0x4117c5380 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/1_chinese/guard_norms.bin} -size w 0x4117c57c0 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/1_chinese/guard_ranked.bin} -size w 0x411fc5800 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/1_chinese/guard_counts.bin} -size w 0x411fc5c40 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/1_chinese/guard_preview.bin} -size w 0x41205a280 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/1_chinese/guard_routed.bin} -size w 0x4120ee8d0 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/1_chinese/guard_merged.bin} -size w 0x412182f50 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/1_chinese/guard_sparse.bin} -size w 0x4122abbc0 4
puts "M4_ABA_STEP_RETURNED 1 chinese K=17764"
lmh4_require_ready
mwr -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/fixture/math.hidden.bin} -size w 0x4104a8140
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/2_math/hidden.bin} -size w 0x4104a8140 448
mwr -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/fixture/math.history.bin} -size w 0x4104a8880
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/2_math/history.bin} -size w 0x4104a8880 4748
mwr -force 0xa0000040 0
mwr -force 0xa0000000 1
set deadline [expr {[clock milliseconds]+60000}]
while {([lmh4_r32 0xa0000000]&2)==0} {
 if {[clock milliseconds]>=$deadline} {error "ABA timeout; do not mutate/reload"}
 after 1
}
if {[lmh4_r32 0xa0000048]!=0 || [lmh4_r32 0xa0000058]!=6 || [lmh4_r32 0xa0000068]!=0} {error "ABA hardware failure"}
if {[lmh4_r32 0xa0000088]!=17106} {error "ABA candidate count differs"}
puts "M4_ABA_2_TOKEN=[lmh4_r32 0xa00000a8]"
puts "M4_ABA_2_SCORE=[lmh4_r32 0xa00000b8]"
puts "M4_ABA_2_CRC=[lmh4_r32 0xa00000c8]"
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/2_math/preview.bin} -size w 0x411fc5c80 151936
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/2_math/merged.bin} -size w 0x4120ee940 17112
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/2_math/raw.bin} -size w 0x412182fc0 34212
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/2_math/guard_weight.bin} -size w 0x4104a8100 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/2_math/guard_hidden.bin} -size w 0x4104a8840 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/2_math/guard_history.bin} -size w 0x4104ad2b0 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/2_math/guard_a.bin} -size w 0x411739300 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/2_math/guard_bt.bin} -size w 0x411755340 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/2_math/guard_centers.bin} -size w 0x4117c5380 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/2_math/guard_norms.bin} -size w 0x4117c57c0 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/2_math/guard_ranked.bin} -size w 0x411fc5800 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/2_math/guard_counts.bin} -size w 0x411fc5c40 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/2_math/guard_preview.bin} -size w 0x41205a280 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/2_math/guard_routed.bin} -size w 0x4120ee8d0 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/2_math/guard_merged.bin} -size w 0x412182f50 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/2_math/guard_sparse.bin} -size w 0x4122abbc0 4
puts "M4_ABA_STEP_RETURNED 2 math K=17106"
mwr -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/selector_integration_fixture_20261021/descriptor_production.bin} -size w 0x400100000
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_aba_20261030_r1/descriptor_restored.bin} -size w 0x400100000 60
lmh4_require_ready
disconnect
puts "M4_ABA_CAPTURE_RETURNED_PENDING_REVIEW"
} message options]} {puts stderr "M4_ABA_ERROR: $message";puts stderr [dict get $options -errorinfo];catch {disconnect};exit 1}
exit 0
