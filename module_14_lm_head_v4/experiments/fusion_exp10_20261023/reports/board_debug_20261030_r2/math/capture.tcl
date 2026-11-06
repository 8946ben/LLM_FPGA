source {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_acceptance_20261030_r3/math/control/private_board_common.tcl}
if {[catch {
connect
targets -set -nocase -filter {name =~ "PSU"}
lmh4_require_ready
if {[lmh4_r32 0x400100000] != 0x4353344d} {error "Production descriptor word 0 changed"}
if {[lmh4_r32 0x400100004] != 0xd0002} {error "Production descriptor word 1 changed"}
if {[lmh4_r32 0x400100008] != 0xf0} {error "Production descriptor word 2 changed"}
if {[lmh4_r32 0x40010000c] != 0x0} {error "Production descriptor word 3 changed"}
if {[lmh4_r32 0x400100010] != 0x6} {error "Production descriptor word 4 changed"}
if {[lmh4_r32 0x400100014] != 0x3f8ccccd} {error "Production descriptor word 5 changed"}
if {[lmh4_r32 0x400100018] != 0x4000} {error "Production descriptor word 6 changed"}
if {[lmh4_r32 0x40010001c] != 0x8507826e} {error "Production descriptor word 7 changed"}
if {[lmh4_r32 0x400100020] != 0x100100} {error "Production descriptor word 8 changed"}
if {[lmh4_r32 0x400100024] != 0x0} {error "Production descriptor word 9 changed"}
if {[lmh4_r32 0x400100028] != 0x103a8000} {error "Production descriptor word 10 changed"}
if {[lmh4_r32 0x40010002c] != 0x0} {error "Production descriptor word 11 changed"}
if {[lmh4_r32 0x400100030] != 0x104a8140} {error "Production descriptor word 12 changed"}
if {[lmh4_r32 0x400100034] != 0x0} {error "Production descriptor word 13 changed"}
if {[lmh4_r32 0x400100038] != 0x700} {error "Production descriptor word 14 changed"}
if {[lmh4_r32 0x40010003c] != 0x0} {error "Production descriptor word 15 changed"}
if {[lmh4_r32 0x400100040] != 0x104a8880} {error "Production descriptor word 16 changed"}
if {[lmh4_r32 0x400100044] != 0x0} {error "Production descriptor word 17 changed"}
if {[lmh4_r32 0x400100048] != 0x4a30} {error "Production descriptor word 18 changed"}
if {[lmh4_r32 0x40010004c] != 0x0} {error "Production descriptor word 19 changed"}
if {[lmh4_r32 0x400100050] != 0x104ad300} {error "Production descriptor word 20 changed"}
if {[lmh4_r32 0x400100054] != 0x0} {error "Production descriptor word 21 changed"}
if {[lmh4_r32 0x400100058] != 0x128c000} {error "Production descriptor word 22 changed"}
if {[lmh4_r32 0x40010005c] != 0x0} {error "Production descriptor word 23 changed"}
if {[lmh4_r32 0x400100060] != 0x11739340} {error "Production descriptor word 24 changed"}
if {[lmh4_r32 0x400100064] != 0x0} {error "Production descriptor word 25 changed"}
if {[lmh4_r32 0x400100068] != 0x1c000} {error "Production descriptor word 26 changed"}
if {[lmh4_r32 0x40010006c] != 0x0} {error "Production descriptor word 27 changed"}
if {[lmh4_r32 0x400100070] != 0x11755380} {error "Production descriptor word 28 changed"}
if {[lmh4_r32 0x400100074] != 0x0} {error "Production descriptor word 29 changed"}
if {[lmh4_r32 0x400100078] != 0x70000} {error "Production descriptor word 30 changed"}
if {[lmh4_r32 0x40010007c] != 0x0} {error "Production descriptor word 31 changed"}
if {[lmh4_r32 0x400100080] != 0x117c53c0} {error "Production descriptor word 32 changed"}
if {[lmh4_r32 0x400100084] != 0x0} {error "Production descriptor word 33 changed"}
if {[lmh4_r32 0x400100088] != 0x400} {error "Production descriptor word 34 changed"}
if {[lmh4_r32 0x40010008c] != 0x0} {error "Production descriptor word 35 changed"}
if {[lmh4_r32 0x400100090] != 0x117c5800} {error "Production descriptor word 36 changed"}
if {[lmh4_r32 0x400100094] != 0x0} {error "Production descriptor word 37 changed"}
if {[lmh4_r32 0x400100098] != 0x800000} {error "Production descriptor word 38 changed"}
if {[lmh4_r32 0x40010009c] != 0x0} {error "Production descriptor word 39 changed"}
if {[lmh4_r32 0x4001000a0] != 0x11fc5840} {error "Production descriptor word 40 changed"}
if {[lmh4_r32 0x4001000a4] != 0x0} {error "Production descriptor word 41 changed"}
if {[lmh4_r32 0x4001000a8] != 0x400} {error "Production descriptor word 42 changed"}
if {[lmh4_r32 0x4001000ac] != 0x0} {error "Production descriptor word 43 changed"}
if {[lmh4_r32 0x4001000b0] != 0x11fc5c80} {error "Production descriptor word 44 changed"}
if {[lmh4_r32 0x4001000b4] != 0x0} {error "Production descriptor word 45 changed"}
if {[lmh4_r32 0x4001000b8] != 0x94600} {error "Production descriptor word 46 changed"}
if {[lmh4_r32 0x4001000bc] != 0x0} {error "Production descriptor word 47 changed"}
if {[lmh4_r32 0x4001000c0] != 0x1205a2c0} {error "Production descriptor word 48 changed"}
if {[lmh4_r32 0x4001000c4] != 0x0} {error "Production descriptor word 49 changed"}
if {[lmh4_r32 0x4001000c8] != 0x94610} {error "Production descriptor word 50 changed"}
if {[lmh4_r32 0x4001000cc] != 0x0} {error "Production descriptor word 51 changed"}
if {[lmh4_r32 0x4001000d0] != 0x120ee940} {error "Production descriptor word 52 changed"}
if {[lmh4_r32 0x4001000d4] != 0x0} {error "Production descriptor word 53 changed"}
if {[lmh4_r32 0x4001000d8] != 0x94610} {error "Production descriptor word 54 changed"}
if {[lmh4_r32 0x4001000dc] != 0x0} {error "Production descriptor word 55 changed"}
if {[lmh4_r32 0x4001000e0] != 0x0} {error "Production descriptor word 56 changed"}
if {[lmh4_r32 0x4001000e4] != 0x0} {error "Production descriptor word 57 changed"}
if {[lmh4_r32 0x4001000e8] != 0x0} {error "Production descriptor word 58 changed"}
if {[lmh4_r32 0x4001000ec] != 0x0} {error "Production descriptor word 59 changed"}
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_debug_20261030_r2/math/descriptor_before.bin} -size w 0x400100000 60
mwr -force 0x400100010 0x7
mwr -force 0x4001000e0 0x12182fc0
mwr -force 0x4001000e8 0x128c00
if {[lmh4_r32 0x400100000] != 0x4353344d} {error "Debug descriptor word 0 differs"}
if {[lmh4_r32 0x400100004] != 0xd0002} {error "Debug descriptor word 1 differs"}
if {[lmh4_r32 0x400100008] != 0xf0} {error "Debug descriptor word 2 differs"}
if {[lmh4_r32 0x40010000c] != 0x0} {error "Debug descriptor word 3 differs"}
if {[lmh4_r32 0x400100010] != 0x7} {error "Debug descriptor word 4 differs"}
if {[lmh4_r32 0x400100014] != 0x3f8ccccd} {error "Debug descriptor word 5 differs"}
if {[lmh4_r32 0x400100018] != 0x4000} {error "Debug descriptor word 6 differs"}
if {[lmh4_r32 0x40010001c] != 0x8507826e} {error "Debug descriptor word 7 differs"}
if {[lmh4_r32 0x400100020] != 0x100100} {error "Debug descriptor word 8 differs"}
if {[lmh4_r32 0x400100024] != 0x0} {error "Debug descriptor word 9 differs"}
if {[lmh4_r32 0x400100028] != 0x103a8000} {error "Debug descriptor word 10 differs"}
if {[lmh4_r32 0x40010002c] != 0x0} {error "Debug descriptor word 11 differs"}
if {[lmh4_r32 0x400100030] != 0x104a8140} {error "Debug descriptor word 12 differs"}
if {[lmh4_r32 0x400100034] != 0x0} {error "Debug descriptor word 13 differs"}
if {[lmh4_r32 0x400100038] != 0x700} {error "Debug descriptor word 14 differs"}
if {[lmh4_r32 0x40010003c] != 0x0} {error "Debug descriptor word 15 differs"}
if {[lmh4_r32 0x400100040] != 0x104a8880} {error "Debug descriptor word 16 differs"}
if {[lmh4_r32 0x400100044] != 0x0} {error "Debug descriptor word 17 differs"}
if {[lmh4_r32 0x400100048] != 0x4a30} {error "Debug descriptor word 18 differs"}
if {[lmh4_r32 0x40010004c] != 0x0} {error "Debug descriptor word 19 differs"}
if {[lmh4_r32 0x400100050] != 0x104ad300} {error "Debug descriptor word 20 differs"}
if {[lmh4_r32 0x400100054] != 0x0} {error "Debug descriptor word 21 differs"}
if {[lmh4_r32 0x400100058] != 0x128c000} {error "Debug descriptor word 22 differs"}
if {[lmh4_r32 0x40010005c] != 0x0} {error "Debug descriptor word 23 differs"}
if {[lmh4_r32 0x400100060] != 0x11739340} {error "Debug descriptor word 24 differs"}
if {[lmh4_r32 0x400100064] != 0x0} {error "Debug descriptor word 25 differs"}
if {[lmh4_r32 0x400100068] != 0x1c000} {error "Debug descriptor word 26 differs"}
if {[lmh4_r32 0x40010006c] != 0x0} {error "Debug descriptor word 27 differs"}
if {[lmh4_r32 0x400100070] != 0x11755380} {error "Debug descriptor word 28 differs"}
if {[lmh4_r32 0x400100074] != 0x0} {error "Debug descriptor word 29 differs"}
if {[lmh4_r32 0x400100078] != 0x70000} {error "Debug descriptor word 30 differs"}
if {[lmh4_r32 0x40010007c] != 0x0} {error "Debug descriptor word 31 differs"}
if {[lmh4_r32 0x400100080] != 0x117c53c0} {error "Debug descriptor word 32 differs"}
if {[lmh4_r32 0x400100084] != 0x0} {error "Debug descriptor word 33 differs"}
if {[lmh4_r32 0x400100088] != 0x400} {error "Debug descriptor word 34 differs"}
if {[lmh4_r32 0x40010008c] != 0x0} {error "Debug descriptor word 35 differs"}
if {[lmh4_r32 0x400100090] != 0x117c5800} {error "Debug descriptor word 36 differs"}
if {[lmh4_r32 0x400100094] != 0x0} {error "Debug descriptor word 37 differs"}
if {[lmh4_r32 0x400100098] != 0x800000} {error "Debug descriptor word 38 differs"}
if {[lmh4_r32 0x40010009c] != 0x0} {error "Debug descriptor word 39 differs"}
if {[lmh4_r32 0x4001000a0] != 0x11fc5840} {error "Debug descriptor word 40 differs"}
if {[lmh4_r32 0x4001000a4] != 0x0} {error "Debug descriptor word 41 differs"}
if {[lmh4_r32 0x4001000a8] != 0x400} {error "Debug descriptor word 42 differs"}
if {[lmh4_r32 0x4001000ac] != 0x0} {error "Debug descriptor word 43 differs"}
if {[lmh4_r32 0x4001000b0] != 0x11fc5c80} {error "Debug descriptor word 44 differs"}
if {[lmh4_r32 0x4001000b4] != 0x0} {error "Debug descriptor word 45 differs"}
if {[lmh4_r32 0x4001000b8] != 0x94600} {error "Debug descriptor word 46 differs"}
if {[lmh4_r32 0x4001000bc] != 0x0} {error "Debug descriptor word 47 differs"}
if {[lmh4_r32 0x4001000c0] != 0x1205a2c0} {error "Debug descriptor word 48 differs"}
if {[lmh4_r32 0x4001000c4] != 0x0} {error "Debug descriptor word 49 differs"}
if {[lmh4_r32 0x4001000c8] != 0x94610} {error "Debug descriptor word 50 differs"}
if {[lmh4_r32 0x4001000cc] != 0x0} {error "Debug descriptor word 51 differs"}
if {[lmh4_r32 0x4001000d0] != 0x120ee940} {error "Debug descriptor word 52 differs"}
if {[lmh4_r32 0x4001000d4] != 0x0} {error "Debug descriptor word 53 differs"}
if {[lmh4_r32 0x4001000d8] != 0x94610} {error "Debug descriptor word 54 differs"}
if {[lmh4_r32 0x4001000dc] != 0x0} {error "Debug descriptor word 55 differs"}
if {[lmh4_r32 0x4001000e0] != 0x12182fc0} {error "Debug descriptor word 56 differs"}
if {[lmh4_r32 0x4001000e4] != 0x0} {error "Debug descriptor word 57 differs"}
if {[lmh4_r32 0x4001000e8] != 0x128c00} {error "Debug descriptor word 58 differs"}
if {[lmh4_r32 0x4001000ec] != 0x0} {error "Debug descriptor word 59 differs"}
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_debug_20261030_r2/math/descriptor_debug.bin} -size w 0x400100000 60
if {[lmh4_r32 0xa0000010] != 0x0 || [lmh4_r32 0xa0000014] != 0x4} {error "64-bit argument 0x10 changed"}
if {[lmh4_r32 0xa000001c] != 0x104a8880 || [lmh4_r32 0xa0000020] != 0x4} {error "64-bit argument 0x1c changed"}
if {[lmh4_r32 0xa0000028] != 0x14000000 || [lmh4_r32 0xa000002c] != 0x0} {error "64-bit argument 0x28 changed"}
if {[lmh4_r32 0xa0000034] != 0x100000 || [lmh4_r32 0xa0000038] != 0x0} {error "64-bit argument 0x34 changed"}
mwr -force 0xa0000040 0
mwr -force 0xa0000000 1
set deadline [expr {[clock milliseconds]+60000}]
while {([lmh4_r32 0xa0000000] & 2) == 0} {
 if {[clock milliseconds]>=$deadline} {error "Debug call timeout; do not mutate/reload"}
 after 1
}
puts "M4_DEBUG_STATUS=[lmh4_r32 0xa0000048]"
puts "M4_DEBUG_STAGE=[lmh4_r32 0xa0000058]"
puts "M4_DEBUG_CHILD=[lmh4_r32 0xa0000068]"
puts "M4_DEBUG_ROUTE_COUNT=[lmh4_r32 0xa0000078]"
puts "M4_DEBUG_COUNT=[lmh4_r32 0xa0000088]"
puts "M4_DEBUG_FALLBACK=[lmh4_r32 0xa0000098]"
puts "M4_DEBUG_TOKEN=[lmh4_r32 0xa00000a8]"
puts "M4_DEBUG_SCORE=[lmh4_r32 0xa00000b8]"
puts "M4_DEBUG_CRC=[lmh4_r32 0xa00000c8]"
if {[lmh4_r32 0xa0000048]!=0 || [lmh4_r32 0xa0000068]!=0 || [lmh4_r32 0xa0000058]!=6} {error "Debug hardware failed"}
if {[lmh4_r32 0xa0000088]!=17106} {error "Candidate count differs"}
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_debug_20261030_r2/math/preview.bin} -size w 0x411fc5c80 151936
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_debug_20261030_r2/math/merged.bin} -size w 0x4120ee940 17112
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_debug_20261030_r2/math/sparse.bin} -size w 0x412182fc0 34212
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_debug_20261030_r2/math/guard_weight.bin} -size w 0x4104a8100 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_debug_20261030_r2/math/guard_hidden.bin} -size w 0x4104a8840 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_debug_20261030_r2/math/guard_history.bin} -size w 0x4104ad2b0 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_debug_20261030_r2/math/guard_a.bin} -size w 0x411739300 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_debug_20261030_r2/math/guard_bt.bin} -size w 0x411755340 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_debug_20261030_r2/math/guard_centers.bin} -size w 0x4117c5380 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_debug_20261030_r2/math/guard_norms.bin} -size w 0x4117c57c0 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_debug_20261030_r2/math/guard_ranked.bin} -size w 0x411fc5800 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_debug_20261030_r2/math/guard_counts.bin} -size w 0x411fc5c40 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_debug_20261030_r2/math/guard_preview.bin} -size w 0x41205a280 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_debug_20261030_r2/math/guard_routed.bin} -size w 0x4120ee8d0 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_debug_20261030_r2/math/guard_merged.bin} -size w 0x412182f50 4
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_debug_20261030_r2/math/guard_sparse.bin} -size w 0x4122abbc0 4
mwr -force 0x400100010 0x6
mwr -force 0x4001000e0 0x0
mwr -force 0x4001000e8 0x0
mrd -force -bin -file {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_debug_20261030_r2/math/descriptor_restored.bin} -size w 0x400100000 60
lmh4_require_ready
disconnect
puts "M4_FULL_DEBUG_CAPTURE_RETURNED_PENDING_BIT_REVIEW"
} message options]} {
 puts stderr "M4_DEBUG_ERROR: $message"
 puts stderr [dict get $options -errorinfo]
 catch {disconnect}
 exit 1
}
exit 0
