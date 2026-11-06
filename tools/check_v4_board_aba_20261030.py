"""Controlled math(A)-Chinese(B)-math(A) actual board full-array state check."""
from pathlib import Path
import argparse,json,struct,subprocess,re,hashlib
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4'
p=argparse.ArgumentParser();p.add_argument('variant',choices=['baseline_hybrid','exp10']);a=p.parse_args()
base=M if a.variant=='baseline_hybrid' else M/'experiments/fusion_exp10_20261023'
current=base/'reports/board_debug_20261030_r2/math';assert json.loads((current/'INDEPENDENT_REVIEW.json').read_text())['state']=='PASS_INDEPENDENT_FULL_BOARD_ARRAY_REVIEW'
D=base/'reports/board_aba_20261030_r2';assert not D.exists();D.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
layout=json.loads((base/'interface/PL_DDR_LAYOUT_V4.json').read_text());regions={x['name']:x for x in layout['regions']};pl=0x400000000;desc=pl+1048576
fixture=base/'reports/selector_integration_fixture_20261021';production=fixture/'descriptor_production.bin';debug=fixture/'descriptor_debug.bin'
prod=struct.unpack('<60I',production.read_bytes());debug_words=struct.unpack('<60I',debug.read_bytes())
lr=base/'reports/lowrank_fixture_20261021' if a.variant=='baseline_hybrid' else base/'fixture'
tk=base/'reports/topk_fixture_20261021' if a.variant=='baseline_hybrid' else base/'fixture'
chain=base/'reports/selector_chain_fixture_20261021' if a.variant=='baseline_hybrid' else base/'fixture'
bindings={};steps=[]
for step,case in enumerate(['math','chinese','math']):
    folder=D/f'{step}_{case}';folder.mkdir();refs={k:folder2/(case+ext) for k,folder2,ext in [('hidden',lr,'.hidden.bin'),('history',lr,'.history.bin'),('preview',lr,'.scores.bin'),('ids',tk,'.expected.bin'),('raw',chain,'.sparse.bin'),('result',chain,'.result.bin')]}
    for f in refs.values():bindings[str(f.relative_to(ROOT))]=sha(f)
    assert refs['hidden'].stat().st_size==regions['hidden']['capacity'] and refs['history'].stat().st_size==regions['history']['capacity']
    steps.append((case,folder,refs,refs['ids'].stat().st_size//4))
bindings[str(production.relative_to(ROOT))]=sha(production);bindings[str(debug.relative_to(ROOT))]=sha(debug)
def capture(folder,name,address,count):return f'mrd -force -bin -file {{{(folder/(name+".bin")).as_posix()}}} -size w {address:#x} {count}\n'
text=f'source {{{(base/"reports/board_acceptance_20261030_r3/math/control/private_board_common.tcl").as_posix()}}}\nif {{[catch {{\nconnect\ntargets -set -nocase -filter {{name =~ "PSU"}}\nlmh4_require_ready\n'
for i,x in enumerate(prod):text+=f'if {{[lmh4_r32 {desc+4*i:#x}]!={x:#x}}} {{error "Initial descriptor differs"}}\n'
text+=f'mwr -force -bin -file {{{debug.as_posix()}}} -size w {desc:#x} 60\n'
for i,(case,folder,refs,k) in enumerate(steps):
    text+='lmh4_require_ready\n'
    for name in ['hidden','history']:
        address=pl+regions[name]['offset'];count=regions[name]['capacity']//4
        text+=f'mwr -force -bin -file {{{refs[name].as_posix()}}} -size w {address:#x} {count}\n'+capture(folder,name,address,count)
    text+='''mwr -force 0xa0000040 0
mwr -force 0xa0000000 1
set deadline [expr {[clock milliseconds]+60000}]
while {([lmh4_r32 0xa0000000]&2)==0} {
 if {[clock milliseconds]>=$deadline} {error "ABA timeout; do not mutate/reload"}
 after 1
}
if {[lmh4_r32 0xa0000048]!=0 || [lmh4_r32 0xa0000058]!=6 || [lmh4_r32 0xa0000068]!=0} {error "ABA hardware failure"}
'''
    text+=f'if {{[lmh4_r32 0xa0000088]!={k}}} {{error "ABA candidate count differs"}}\n'
    for name,off in [('TOKEN',0xa8),('SCORE',0xb8),('CRC',0xc8)]:text+=f'puts "M4_ABA_{i}_{name}=[lmh4_r32 {0xa0000000+off:#x}]"\n'
    text+=capture(folder,'preview',pl+regions['preview']['offset'],151936)+capture(folder,'merged',pl+regions['merged']['offset'],4+4*((k+3)//4))+capture(folder,'raw',pl+regions['sparse']['offset'],4*((k+1)//2))
    for name,region in regions.items():text+=capture(folder,'guard_'+name,pl+region['offset']+region['capacity'],4)
    text+=f'puts "M4_ABA_STEP_RETURNED {i} {case} K={k}"\n'
text+=f'mwr -force -bin -file {{{production.as_posix()}}} -size w {desc:#x} 60\n'+capture(D,'descriptor_restored',desc,60)
text+='lmh4_require_ready\ndisconnect\nputs "M4_ABA_CAPTURE_RETURNED_PENDING_REVIEW"\n} message options]} {puts stderr "M4_ABA_ERROR: $message";puts stderr [dict get $options -errorinfo];catch {disconnect};exit 1}\nexit 0\n'
(D/'capture.tcl').write_text(text);(D/'PLAN.json').write_text(json.dumps(dict(variant=a.variant,sequence=['math','chinese','math'],source_sha256=bindings,entry_sha256=sha(D/'capture.tcl'),scope='Same configured hardware, CPU remains halted, only hidden/history and debug descriptor updated; actual binary readback each step; not autoregressive/free generation'),indent=2)+'\n')
with (D/'capture.log').open('x') as f:proc=subprocess.run(['G:/Xilinx/Vitis/2021.1/bin/xsct.bat',(D/'capture.tcl').as_posix()],stdout=f,stderr=subprocess.STDOUT,timeout=600)
s=(D/'capture.log').read_text(errors='replace');assert proc.returncode==0 and 'M4_ABA_CAPTURE_RETURNED_PENDING_REVIEW' in s and 'M4_ABA_ERROR:' not in s,s[-2500:]
for n,h in bindings.items():assert sha(ROOT/n)==h
for i,(case,folder,refs,k) in enumerate(steps):
    for name in ['hidden','history','preview']:assert (folder/(name+'.bin')).read_bytes()==refs[name].read_bytes()
    ids=refs['ids'].read_bytes();merged=(folder/'merged.bin').read_bytes();assert struct.unpack('<4I',merged[:16])==(0x4449344d,0x00040001,k,151936) and merged[16:16+k*4]==ids
    assert (folder/'raw.bin').read_bytes()[:8*k]==refs['raw'].read_bytes()[:8*k]
    for name,value in zip(['TOKEN','SCORE','CRC'],struct.unpack('<3I',refs['result'].read_bytes()[:12])):assert int(re.search(r'^M4_ABA_'+str(i)+'_'+name+r'=(\d+)$',s,re.M)[1])==value
    assert all((folder/('guard_'+name+'.bin')).read_bytes()==(0xabcdef).to_bytes(16,'little') for name in regions)
for name in ['hidden','history','preview','merged','raw']:assert (steps[0][1]/(name+'.bin')).read_bytes()==(steps[2][1]/(name+'.bin')).read_bytes()
assert (D/'descriptor_restored.bin').read_bytes()==production.read_bytes()
review=dict(state='PASS_CONTROLLED_ABA_FULL_ARRAYS_AND_INPUT_READBACK',variant=a.variant,calls=3,sequence=['math','chinese','math'],full_preview_values_per_call=151936,all_ids_and_raw_per_call=[x[3] for x in steps],guards_per_call=13,A_before_after_identical=True,production_descriptor_and_math_input_restored=True,autoregressive_history='NOT_TESTED',files_sha256={str(p.relative_to(D)):sha(p) for p in D.rglob('*.bin')})
(D/'INDEPENDENT_REVIEW.json').write_text(json.dumps(review,indent=2)+'\n');print(json.dumps({k:v for k,v in review.items() if k!='files_sha256'},indent=2))
