source {D:/program/LLM_FPGA/module_14_lm_head_v4/experiments/fusion_exp10_20261023/reports/board_acceptance_20261030_r3/math/control/private_board_common.tcl}
if {[catch {
connect
targets -set -nocase -filter {name =~ "PSU"}
lmh4_require_ready
if {[lmh4_r32 0x400100000]!=0x4353344d} {error "Descriptor word 0 differs"}
if {[lmh4_r32 0x400100004]!=0xd0002} {error "Descriptor word 1 differs"}
if {[lmh4_r32 0x400100008]!=0xf0} {error "Descriptor word 2 differs"}
if {[lmh4_r32 0x40010000c]!=0x0} {error "Descriptor word 3 differs"}
if {[lmh4_r32 0x400100010]!=0x6} {error "Descriptor word 4 differs"}
if {[lmh4_r32 0x400100014]!=0x3f8ccccd} {error "Descriptor word 5 differs"}
if {[lmh4_r32 0x400100018]!=0x4000} {error "Descriptor word 6 differs"}
if {[lmh4_r32 0x40010001c]!=0x8507826e} {error "Descriptor word 7 differs"}
if {[lmh4_r32 0x400100020]!=0x100100} {error "Descriptor word 8 differs"}
if {[lmh4_r32 0x400100024]!=0x0} {error "Descriptor word 9 differs"}
if {[lmh4_r32 0x400100028]!=0x103a8000} {error "Descriptor word 10 differs"}
if {[lmh4_r32 0x40010002c]!=0x0} {error "Descriptor word 11 differs"}
if {[lmh4_r32 0x400100030]!=0x104a8140} {error "Descriptor word 12 differs"}
if {[lmh4_r32 0x400100034]!=0x0} {error "Descriptor word 13 differs"}
if {[lmh4_r32 0x400100038]!=0x700} {error "Descriptor word 14 differs"}
if {[lmh4_r32 0x40010003c]!=0x0} {error "Descriptor word 15 differs"}
if {[lmh4_r32 0x400100040]!=0x104a8880} {error "Descriptor word 16 differs"}
if {[lmh4_r32 0x400100044]!=0x0} {error "Descriptor word 17 differs"}
if {[lmh4_r32 0x400100048]!=0x4a30} {error "Descriptor word 18 differs"}
if {[lmh4_r32 0x40010004c]!=0x0} {error "Descriptor word 19 differs"}
if {[lmh4_r32 0x400100050]!=0x104ad300} {error "Descriptor word 20 differs"}
if {[lmh4_r32 0x400100054]!=0x0} {error "Descriptor word 21 differs"}
if {[lmh4_r32 0x400100058]!=0x128c000} {error "Descriptor word 22 differs"}
if {[lmh4_r32 0x40010005c]!=0x0} {error "Descriptor word 23 differs"}
if {[lmh4_r32 0x400100060]!=0x11739340} {error "Descriptor word 24 differs"}
if {[lmh4_r32 0x400100064]!=0x0} {error "Descriptor word 25 differs"}
if {[lmh4_r32 0x400100068]!=0x1c000} {error "Descriptor word 26 differs"}
if {[lmh4_r32 0x40010006c]!=0x0} {error "Descriptor word 27 differs"}
if {[lmh4_r32 0x400100070]!=0x11755380} {error "Descriptor word 28 differs"}
if {[lmh4_r32 0x400100074]!=0x0} {error "Descriptor word 29 differs"}
if {[lmh4_r32 0x400100078]!=0x70000} {error "Descriptor word 30 differs"}
if {[lmh4_r32 0x40010007c]!=0x0} {error "Descriptor word 31 differs"}
if {[lmh4_r32 0x400100080]!=0x117c53c0} {error "Descriptor word 32 differs"}
if {[lmh4_r32 0x400100084]!=0x0} {error "Descriptor word 33 differs"}
if {[lmh4_r32 0x400100088]!=0x400} {error "Descriptor word 34 differs"}
if {[lmh4_r32 0x40010008c]!=0x0} {error "Descriptor word 35 differs"}
if {[lmh4_r32 0x400100090]!=0x117c5800} {error "Descriptor word 36 differs"}
if {[lmh4_r32 0x400100094]!=0x0} {error "Descriptor word 37 differs"}
if {[lmh4_r32 0x400100098]!=0x800000} {error "Descriptor word 38 differs"}
if {[lmh4_r32 0x40010009c]!=0x0} {error "Descriptor word 39 differs"}
if {[lmh4_r32 0x4001000a0]!=0x11fc5840} {error "Descriptor word 40 differs"}
if {[lmh4_r32 0x4001000a4]!=0x0} {error "Descriptor word 41 differs"}
if {[lmh4_r32 0x4001000a8]!=0x400} {error "Descriptor word 42 differs"}
if {[lmh4_r32 0x4001000ac]!=0x0} {error "Descriptor word 43 differs"}
if {[lmh4_r32 0x4001000b0]!=0x11fc5c80} {error "Descriptor word 44 differs"}
if {[lmh4_r32 0x4001000b4]!=0x0} {error "Descriptor word 45 differs"}
if {[lmh4_r32 0x4001000b8]!=0x94600} {error "Descriptor word 46 differs"}
if {[lmh4_r32 0x4001000bc]!=0x0} {error "Descriptor word 47 differs"}
if {[lmh4_r32 0x4001000c0]!=0x1205a2c0} {error "Descriptor word 48 differs"}
if {[lmh4_r32 0x4001000c4]!=0x0} {error "Descriptor word 49 differs"}
if {[lmh4_r32 0x4001000c8]!=0x94610} {error "Descriptor word 50 differs"}
if {[lmh4_r32 0x4001000cc]!=0x0} {error "Descriptor word 51 differs"}
if {[lmh4_r32 0x4001000d0]!=0x120ee940} {error "Descriptor word 52 differs"}
if {[lmh4_r32 0x4001000d4]!=0x0} {error "Descriptor word 53 differs"}
if {[lmh4_r32 0x4001000d8]!=0x94610} {error "Descriptor word 54 differs"}
if {[lmh4_r32 0x4001000dc]!=0x0} {error "Descriptor word 55 differs"}
if {[lmh4_r32 0x4001000e0]!=0x0} {error "Descriptor word 56 differs"}
if {[lmh4_r32 0x4001000e4]!=0x0} {error "Descriptor word 57 differs"}
if {[lmh4_r32 0x4001000e8]!=0x0} {error "Descriptor word 58 differs"}
if {[lmh4_r32 0x4001000ec]!=0x0} {error "Descriptor word 59 differs"}
set old_routed_0 [lmh4_r32 0x41205a2c0]
set old_routed_1 [lmh4_r32 0x41205a2c4]
set old_routed_2 [lmh4_r32 0x41205a2c8]
set old_routed_3 [lmh4_r32 0x41205a2cc]
set old_merged_0 [lmh4_r32 0x4120ee940]
set old_merged_1 [lmh4_r32 0x4120ee944]
set old_merged_2 [lmh4_r32 0x4120ee948]
set old_merged_3 [lmh4_r32 0x4120ee94c]
set old_sparse_0 [lmh4_r32 0x412182fc0]
set old_sparse_1 [lmh4_r32 0x412182fc4]
set old_sparse_2 [lmh4_r32 0x412182fc8]
set old_sparse_3 [lmh4_r32 0x412182fcc]
lmh4_require_ready
mwr -force 0xa0000040 1
mwr -force 0xa0000000 1
set deadline [expr {[clock milliseconds]+10000}]
while {([lmh4_r32 0xa0000000]&2)==0} {
 if {[clock milliseconds]>=$deadline} {error "Preflight test timeout; do not mutate/reload"}
 after 1
}
if {[lmh4_r32 0xa0000048]!=0} {error "validate_only register 0x48 mismatch"}
if {[lmh4_r32 0xa0000058]!=1} {error "validate_only register 0x58 mismatch"}
if {[lmh4_r32 0xa0000068]!=0} {error "validate_only register 0x68 mismatch"}
if {[lmh4_r32 0xa0000078]!=0} {error "validate_only register 0x78 mismatch"}
if {[lmh4_r32 0xa0000088]!=0} {error "validate_only register 0x88 mismatch"}
if {[lmh4_r32 0xa0000098]!=0} {error "validate_only register 0x98 mismatch"}
if {[lmh4_r32 0xa00000a8]!=0} {error "validate_only register 0xa8 mismatch"}
if {[lmh4_r32 0xa00000b8]!=0} {error "validate_only register 0xb8 mismatch"}
if {[lmh4_r32 0xa00000c8]!=0} {error "validate_only register 0xc8 mismatch"}
if {[lmh4_r32 0x41205a2c0]!=$old_routed_0} {error "validate_only changed scratch header"}
if {[lmh4_r32 0x41205a2c4]!=$old_routed_1} {error "validate_only changed scratch header"}
if {[lmh4_r32 0x41205a2c8]!=$old_routed_2} {error "validate_only changed scratch header"}
if {[lmh4_r32 0x41205a2cc]!=$old_routed_3} {error "validate_only changed scratch header"}
if {[lmh4_r32 0x4120ee940]!=$old_merged_0} {error "validate_only changed scratch header"}
if {[lmh4_r32 0x4120ee944]!=$old_merged_1} {error "validate_only changed scratch header"}
if {[lmh4_r32 0x4120ee948]!=$old_merged_2} {error "validate_only changed scratch header"}
if {[lmh4_r32 0x4120ee94c]!=$old_merged_3} {error "validate_only changed scratch header"}
if {[lmh4_r32 0x412182fc0]!=$old_sparse_0} {error "validate_only changed scratch header"}
if {[lmh4_r32 0x412182fc4]!=$old_sparse_1} {error "validate_only changed scratch header"}
if {[lmh4_r32 0x412182fc8]!=$old_sparse_2} {error "validate_only changed scratch header"}
if {[lmh4_r32 0x412182fcc]!=$old_sparse_3} {error "validate_only changed scratch header"}
puts "M4_ERROR_CASE_PASS validate_only status=0 stage=1 no_token=1 scratch_headers_preserved=1"
lmh4_require_ready
mwr -force 0x400100000 0x0
mwr -force 0xa0000040 0
mwr -force 0xa0000000 1
set deadline [expr {[clock milliseconds]+10000}]
while {([lmh4_r32 0xa0000000]&2)==0} {
 if {[clock milliseconds]>=$deadline} {error "Preflight test timeout; do not mutate/reload"}
 after 1
}
if {[lmh4_r32 0xa0000048]!=1} {error "bad_magic register 0x48 mismatch"}
if {[lmh4_r32 0xa0000058]!=1} {error "bad_magic register 0x58 mismatch"}
if {[lmh4_r32 0xa0000068]!=0} {error "bad_magic register 0x68 mismatch"}
if {[lmh4_r32 0xa0000078]!=0} {error "bad_magic register 0x78 mismatch"}
if {[lmh4_r32 0xa0000088]!=0} {error "bad_magic register 0x88 mismatch"}
if {[lmh4_r32 0xa0000098]!=0} {error "bad_magic register 0x98 mismatch"}
if {[lmh4_r32 0xa00000a8]!=0} {error "bad_magic register 0xa8 mismatch"}
if {[lmh4_r32 0xa00000b8]!=0} {error "bad_magic register 0xb8 mismatch"}
if {[lmh4_r32 0xa00000c8]!=0} {error "bad_magic register 0xc8 mismatch"}
if {[lmh4_r32 0x41205a2c0]!=$old_routed_0} {error "bad_magic changed scratch header"}
if {[lmh4_r32 0x41205a2c4]!=$old_routed_1} {error "bad_magic changed scratch header"}
if {[lmh4_r32 0x41205a2c8]!=$old_routed_2} {error "bad_magic changed scratch header"}
if {[lmh4_r32 0x41205a2cc]!=$old_routed_3} {error "bad_magic changed scratch header"}
if {[lmh4_r32 0x4120ee940]!=$old_merged_0} {error "bad_magic changed scratch header"}
if {[lmh4_r32 0x4120ee944]!=$old_merged_1} {error "bad_magic changed scratch header"}
if {[lmh4_r32 0x4120ee948]!=$old_merged_2} {error "bad_magic changed scratch header"}
if {[lmh4_r32 0x4120ee94c]!=$old_merged_3} {error "bad_magic changed scratch header"}
if {[lmh4_r32 0x412182fc0]!=$old_sparse_0} {error "bad_magic changed scratch header"}
if {[lmh4_r32 0x412182fc4]!=$old_sparse_1} {error "bad_magic changed scratch header"}
if {[lmh4_r32 0x412182fc8]!=$old_sparse_2} {error "bad_magic changed scratch header"}
if {[lmh4_r32 0x412182fcc]!=$old_sparse_3} {error "bad_magic changed scratch header"}
mwr -force 0x400100000 0x4353344d
puts "M4_ERROR_CASE_PASS bad_magic status=1 stage=1 no_token=1 scratch_headers_preserved=1"
lmh4_require_ready
mwr -force 0x4001000c0 0x120ee940
mwr -force 0xa0000040 0
mwr -force 0xa0000000 1
set deadline [expr {[clock milliseconds]+10000}]
while {([lmh4_r32 0xa0000000]&2)==0} {
 if {[clock milliseconds]>=$deadline} {error "Preflight test timeout; do not mutate/reload"}
 after 1
}
if {[lmh4_r32 0xa0000048]!=3} {error "overlap register 0x48 mismatch"}
if {[lmh4_r32 0xa0000058]!=1} {error "overlap register 0x58 mismatch"}
if {[lmh4_r32 0xa0000068]!=0} {error "overlap register 0x68 mismatch"}
if {[lmh4_r32 0xa0000078]!=0} {error "overlap register 0x78 mismatch"}
if {[lmh4_r32 0xa0000088]!=0} {error "overlap register 0x88 mismatch"}
if {[lmh4_r32 0xa0000098]!=0} {error "overlap register 0x98 mismatch"}
if {[lmh4_r32 0xa00000a8]!=0} {error "overlap register 0xa8 mismatch"}
if {[lmh4_r32 0xa00000b8]!=0} {error "overlap register 0xb8 mismatch"}
if {[lmh4_r32 0xa00000c8]!=0} {error "overlap register 0xc8 mismatch"}
if {[lmh4_r32 0x41205a2c0]!=$old_routed_0} {error "overlap changed scratch header"}
if {[lmh4_r32 0x41205a2c4]!=$old_routed_1} {error "overlap changed scratch header"}
if {[lmh4_r32 0x41205a2c8]!=$old_routed_2} {error "overlap changed scratch header"}
if {[lmh4_r32 0x41205a2cc]!=$old_routed_3} {error "overlap changed scratch header"}
if {[lmh4_r32 0x4120ee940]!=$old_merged_0} {error "overlap changed scratch header"}
if {[lmh4_r32 0x4120ee944]!=$old_merged_1} {error "overlap changed scratch header"}
if {[lmh4_r32 0x4120ee948]!=$old_merged_2} {error "overlap changed scratch header"}
if {[lmh4_r32 0x4120ee94c]!=$old_merged_3} {error "overlap changed scratch header"}
if {[lmh4_r32 0x412182fc0]!=$old_sparse_0} {error "overlap changed scratch header"}
if {[lmh4_r32 0x412182fc4]!=$old_sparse_1} {error "overlap changed scratch header"}
if {[lmh4_r32 0x412182fc8]!=$old_sparse_2} {error "overlap changed scratch header"}
if {[lmh4_r32 0x412182fcc]!=$old_sparse_3} {error "overlap changed scratch header"}
mwr -force 0x4001000c0 0x1205a2c0
puts "M4_ERROR_CASE_PASS overlap status=3 stage=1 no_token=1 scratch_headers_preserved=1"
lmh4_require_ready
mwr -force 0xa0000040 2
mwr -force 0xa0000000 1
set deadline [expr {[clock milliseconds]+10000}]
while {([lmh4_r32 0xa0000000]&2)==0} {
 if {[clock milliseconds]>=$deadline} {error "Preflight test timeout; do not mutate/reload"}
 after 1
}
if {[lmh4_r32 0xa0000048]!=4} {error "bad_command register 0x48 mismatch"}
if {[lmh4_r32 0xa0000058]!=1} {error "bad_command register 0x58 mismatch"}
if {[lmh4_r32 0xa0000068]!=0} {error "bad_command register 0x68 mismatch"}
if {[lmh4_r32 0xa0000078]!=0} {error "bad_command register 0x78 mismatch"}
if {[lmh4_r32 0xa0000088]!=0} {error "bad_command register 0x88 mismatch"}
if {[lmh4_r32 0xa0000098]!=0} {error "bad_command register 0x98 mismatch"}
if {[lmh4_r32 0xa00000a8]!=0} {error "bad_command register 0xa8 mismatch"}
if {[lmh4_r32 0xa00000b8]!=0} {error "bad_command register 0xb8 mismatch"}
if {[lmh4_r32 0xa00000c8]!=0} {error "bad_command register 0xc8 mismatch"}
if {[lmh4_r32 0x41205a2c0]!=$old_routed_0} {error "bad_command changed scratch header"}
if {[lmh4_r32 0x41205a2c4]!=$old_routed_1} {error "bad_command changed scratch header"}
if {[lmh4_r32 0x41205a2c8]!=$old_routed_2} {error "bad_command changed scratch header"}
if {[lmh4_r32 0x41205a2cc]!=$old_routed_3} {error "bad_command changed scratch header"}
if {[lmh4_r32 0x4120ee940]!=$old_merged_0} {error "bad_command changed scratch header"}
if {[lmh4_r32 0x4120ee944]!=$old_merged_1} {error "bad_command changed scratch header"}
if {[lmh4_r32 0x4120ee948]!=$old_merged_2} {error "bad_command changed scratch header"}
if {[lmh4_r32 0x4120ee94c]!=$old_merged_3} {error "bad_command changed scratch header"}
if {[lmh4_r32 0x412182fc0]!=$old_sparse_0} {error "bad_command changed scratch header"}
if {[lmh4_r32 0x412182fc4]!=$old_sparse_1} {error "bad_command changed scratch header"}
if {[lmh4_r32 0x412182fc8]!=$old_sparse_2} {error "bad_command changed scratch header"}
if {[lmh4_r32 0x412182fcc]!=$old_sparse_3} {error "bad_command changed scratch header"}
puts "M4_ERROR_CASE_PASS bad_command status=4 stage=1 no_token=1 scratch_headers_preserved=1"
mwr -force 0xa0000040 0
lmh4_require_ready
disconnect
puts "M4_FINITE_ERROR_TESTS_COMPLETE"
} message options]} {puts stderr "M4_ERROR_TEST_FAILED: $message";puts stderr [dict get $options -errorinfo];catch {disconnect};exit 1}
exit 0
