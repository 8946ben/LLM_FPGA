"""One isolated full-array debug capture after qualified fixed production campaign."""
from pathlib import Path
import argparse,json,struct,subprocess,hashlib,sys,datetime,re
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/dual_board_20261030_r1'
p=argparse.ArgumentParser();p.add_argument('variant',choices=['baseline_hybrid','exp10']);p.add_argument('case',choices=['chinese','english','code','math']);p.add_argument('--execute',action='store_true');a=p.parse_args()
base=M if a.variant=='baseline_hybrid' else M/'experiments/fusion_exp10_20261023';D=base/'reports/board_debug_20261030_r2'/a.case
assert not D.exists();D.mkdir(parents=True)
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
campaign=base/'reports/board_acceptance_20261030_r3'/a.case;proof=read(campaign/'INDEPENDENT_REVIEW.json')
assert proof['state']=='PASS_FIXED_INPUT_TARGET_TRANSFER_AND_1033_OUTPUT_CALLS'
fixture=base/'reports/selector_integration_fixture_20261021';prod=(fixture/'descriptor_production.bin').read_bytes();debug=(fixture/'descriptor_debug.bin').read_bytes()
assert len(prod)==len(debug)==240
pr=list(struct.unpack('<60I',prod));db=list(struct.unpack('<60I',debug));assert pr[4]==6 and db[4]==7
assert [i for i,(x,y) in enumerate(zip(pr,db)) if x!=y]==[4,56,58]
layout=read(base/'interface/PL_DDR_LAYOUT_V4.json');regions=layout['regions'];pl=0x400000000;desc=pl+1048576
preview=next(x for x in regions if x['name']=='preview');merged=next(x for x in regions if x['name']=='merged');sparse=next(x for x in regions if x['name']=='sparse')
topk=base/'reports/topk_fixture_20261021' if a.variant=='baseline_hybrid' else base/'fixture'
lowrank=base/'reports/lowrank_fixture_20261021' if a.variant=='baseline_hybrid' else base/'fixture'
chain=base/'reports/selector_chain_fixture_20261021' if a.variant=='baseline_hybrid' else base/'fixture'
expected=(topk/(a.case+'.expected.bin')).read_bytes();k=len(expected)//4
assert k==proof['candidate_count']
references={'preview':lowrank/(a.case+'.scores.bin'),'ids':topk/(a.case+'.expected.bin'),'sparse':chain/(a.case+'.sparse.bin'),'result':chain/(a.case+'.result.bin')}
def capture(name,address,words):return f'mrd -force -bin -file {{{(D/(name+".bin")).as_posix()}}} -size w {address:#x} {words}\n'
text=f'''source {{{(campaign/'control/private_board_common.tcl').as_posix()}}}
if {{[catch {{
connect
targets -set -nocase -filter {{name =~ "PSU"}}
lmh4_require_ready
'''
# Verify every descriptor word before any mutation; production inputs are fixed.
for i,x in enumerate(pr):text+=f'if {{[lmh4_r32 {desc+i*4:#x}] != {x:#x}}} {{error "Production descriptor word {i} changed"}}\n'
text+=capture('descriptor_before',desc,60)
for i in [4,56,58]:text+=f'mwr -force {desc+i*4:#x} {db[i]:#x}\n'
for i,x in enumerate(db):text+=f'if {{[lmh4_r32 {desc+i*4:#x}] != {x:#x}}} {{error "Debug descriptor word {i} differs"}}\n'
text+=capture('descriptor_debug',desc,60)
# Existing A53 campaign left these checked 64-bit arguments; assert them again.
args={0x10:pl,0x1c:pl+next(x['offset'] for x in regions if x['name']=='history'),0x28:335544320,0x34:1048576}
for offset,value in args.items():
    text+=f'if {{[lmh4_r32 {0xa0000000+offset:#x}] != {value&0xffffffff:#x} || [lmh4_r32 {0xa0000004+offset:#x}] != {value>>32:#x}}} {{error "64-bit argument {offset:#x} changed"}}\n'
text+='''mwr -force 0xa0000040 0
mwr -force 0xa0000000 1
set deadline [expr {[clock milliseconds]+60000}]
while {([lmh4_r32 0xa0000000] & 2) == 0} {
 if {[clock milliseconds]>=$deadline} {error "Debug call timeout; do not mutate/reload"}
 after 1
}
'''
for name,offset in [('status',0x48),('stage',0x58),('child',0x68),('route_count',0x78),('count',0x88),('fallback',0x98),('token',0xa8),('score',0xb8),('crc',0xc8)]:text+=f'puts "M4_DEBUG_{name.upper()}=[lmh4_r32 {0xa0000000+offset:#x}]"\n'
text+='if {[lmh4_r32 0xa0000048]!=0 || [lmh4_r32 0xa0000068]!=0 || [lmh4_r32 0xa0000058]!=6} {error "Debug hardware failed"}\n'
text+=f'if {{[lmh4_r32 0xa0000088]!={k}}} {{error "Candidate count differs"}}\n'
text+=capture('preview',pl+preview['offset'],151936)+capture('merged',pl+merged['offset'],4+((k+3)//4)*4)+capture('sparse',pl+sparse['offset'],((k+1)//2)*4)
for region in regions:text+=capture('guard_'+region['name'],pl+region['offset']+region['capacity'],4)
# Restore descriptor only after actual debug call completed and all captures exist.
for i in [4,56,58]:text+=f'mwr -force {desc+i*4:#x} {pr[i]:#x}\n'
text+=capture('descriptor_restored',desc,60)
text+='''lmh4_require_ready
disconnect
puts "M4_FULL_DEBUG_CAPTURE_RETURNED_PENDING_BIT_REVIEW"
} message options]} {
 puts stderr "M4_DEBUG_ERROR: $message"
 puts stderr [dict get $options -errorinfo]
 catch {disconnect}
 exit 1
}
exit 0
'''
(D/'capture.tcl').write_text(text)
plan=dict(state='FROZEN_FULL_ARRAY_DEBUG_CAPTURE',variant=a.variant,case=a.case,k=k,expected_files={str(p.relative_to(ROOT)):sha(p) for p in references.values()},script_sha256=sha(D/'capture.tcl'),production_capture_sha256=sha(campaign/'records.bin'),scope='Actual full preview, merged IDs, canonical candidate raw; fixed input; separately untimed; no board reinit or stale ticket; preceding same-case production campaign qualified')
(D/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
if not a.execute:print('PREPARED_ONLY');sys.exit(0)
with (D/'capture.log').open('x') as log:proc=subprocess.run(['G:/Xilinx/Vitis/2021.1/bin/xsct.bat',(D/'capture.tcl').as_posix()],stdout=log,stderr=subprocess.STDOUT,timeout=600)
log=(D/'capture.log').read_text(errors='replace');assert proc.returncode==0 and 'M4_FULL_DEBUG_CAPTURE_RETURNED_PENDING_BIT_REVIEW' in log and 'M4_DEBUG_ERROR:' not in log,log[-3000:]
assert (D/'preview.bin').read_bytes()==references['preview'].read_bytes()
merged_data=(D/'merged.bin').read_bytes();assert merged_data[16:16+k*4]==expected
assert struct.unpack('<4I',merged_data[:16])==(0x4449344d,0x00040001,k,151936)
sparse_data=(D/'sparse.bin').read_bytes();reference=references['sparse'].read_bytes();assert sparse_data[:k*8]==reference[:k*8]
assert (D/'descriptor_before.bin').read_bytes()==prod and (D/'descriptor_debug.bin').read_bytes()==debug and (D/'descriptor_restored.bin').read_bytes()==prod
assert all((D/('guard_'+x['name']+'.bin')).read_bytes()==(0xabcdef).to_bytes(16,'little') for x in regions)
for name,expected_scalar in zip(['TOKEN','SCORE','CRC'],struct.unpack('<3I',references['result'].read_bytes()[:12])):
    assert int(re.search(r'^M4_DEBUG_'+name+r'=(\d+)$',log,re.M)[1])==expected_scalar
for name,digest in plan['expected_files'].items():assert sha(ROOT/name)==digest
result=dict(state='PASS_TARGET_FULL_PREVIEW_IDS_CANONICAL_RAW_AND_13_GUARDS',variant=a.variant,case=a.case,preview_values=151936,candidate_ids=k,candidate_raw=k,guards=13,files_sha256={p.name:sha(p) for p in D.glob('*.bin')},numerical_tolerance='EXACT_BITS',timing='NOT_A_PRODUCTION_MEASUREMENT',multistep='NOT_RUN')
(D/'NUMERIC_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
