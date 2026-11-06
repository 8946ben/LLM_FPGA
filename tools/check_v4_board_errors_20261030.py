"""Finite preflight rejection checks after a completed numeric board capture."""
from pathlib import Path
import argparse,json,struct,subprocess,re,hashlib
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/dual_board_20261030_r1'
p=argparse.ArgumentParser();p.add_argument('variant',choices=['baseline_hybrid','exp10']);p.add_argument('case');a=p.parse_args()
base=M if a.variant=='baseline_hybrid' else M/'experiments/fusion_exp10_20261023';previous=base/'reports/board_debug_20261030_r2'/a.case
assert json.loads((previous/'INDEPENDENT_REVIEW.json').read_text())['state']=='PASS_INDEPENDENT_FULL_BOARD_ARRAY_REVIEW'
D=base/'reports/board_errors_20261030_r1'/a.case;assert not D.exists();D.mkdir(parents=True)
pr=struct.unpack('<60I',(base/'reports/selector_integration_fixture_20261021/descriptor_production.bin').read_bytes());desc=0x400100000
layout=json.loads((base/'interface/PL_DDR_LAYOUT_V4.json').read_text());scratch=[x for x in layout['regions'] if x['name'] in ['routed','merged','sparse']]
text=f'source {{{(base/"reports/board_acceptance_20261030_r3"/a.case/"control/private_board_common.tcl").as_posix()}}}\nif {{[catch {{\nconnect\ntargets -set -nocase -filter {{name =~ "PSU"}}\nlmh4_require_ready\n'
for i,x in enumerate(pr):text+=f'if {{[lmh4_r32 {desc+4*i:#x}]!={x:#x}}} {{error "Descriptor word {i} differs"}}\n'
for region in scratch:
    for word in range(4):text+=f'set old_{region["name"]}_{word} [lmh4_r32 {0x400000000+region["offset"]+4*word:#x}]\n'
tests=[('validate_only',1,0,{}),('bad_magic',0,1,{0:0}),('overlap',0,3,{48:pr[52]}),('bad_command',2,4,{})]
for name,command,status,changes in tests:
    text+='lmh4_require_ready\n'
    for i,x in changes.items():text+=f'mwr -force {desc+4*i:#x} {x:#x}\n'
    text+=f'mwr -force 0xa0000040 {command}\nmwr -force 0xa0000000 1\n'
    text+='''set deadline [expr {[clock milliseconds]+10000}]
while {([lmh4_r32 0xa0000000]&2)==0} {
 if {[clock milliseconds]>=$deadline} {error "Preflight test timeout; do not mutate/reload"}
 after 1
}
'''
    for offset,expected in [(0x48,status),(0x58,1),(0x68,0),(0x78,0),(0x88,0),(0x98,0),(0xa8,0),(0xb8,0),(0xc8,0)]:text+=f'if {{[lmh4_r32 {0xa0000000+offset:#x}]!={expected}}} {{error "{name} register {offset:#x} mismatch"}}\n'
    for region in scratch:
        for word in range(4):text+=f'if {{[lmh4_r32 {0x400000000+region["offset"]+4*word:#x}]!=$old_{region["name"]}_{word}}} {{error "{name} changed scratch header"}}\n'
    for i in changes:text+=f'mwr -force {desc+4*i:#x} {pr[i]:#x}\n'
    text+=f'puts "M4_ERROR_CASE_PASS {name} status={status} stage=1 no_token=1 scratch_headers_preserved=1"\n'
text+='mwr -force 0xa0000040 0\nlmh4_require_ready\ndisconnect\nputs "M4_FINITE_ERROR_TESTS_COMPLETE"\n} message options]} {puts stderr "M4_ERROR_TEST_FAILED: $message";puts stderr [dict get $options -errorinfo];catch {disconnect};exit 1}\nexit 0\n'
(D/'test.tcl').write_text(text);(D/'PLAN.json').write_text(json.dumps(dict(variant=a.variant,case=a.case,tests=[x[0] for x in tests],scope='Valid descriptor-only, invalid magic/overlap/command; exact preflight status, no stale result and first16B of three scratch regions unchanged. Does not prove every scratch byte or runtime failure handling.',source_sha256=hashlib.sha256((D/'test.tcl').read_bytes()).hexdigest()),indent=2)+'\n')
with (D/'test.log').open('x') as log:result=subprocess.run(['G:/Xilinx/Vitis/2021.1/bin/xsct.bat',(D/'test.tcl').as_posix()],stdout=log,stderr=subprocess.STDOUT,timeout=120)
s=(D/'test.log').read_text(errors='replace');events=re.findall(r'^M4_ERROR_CASE_PASS (\w+) status=(\d+) stage=1 no_token=1 scratch_headers_preserved=1$',s,re.M)
assert result.returncode==0 and events==[(x[0],str(x[2])) for x in tests] and 'M4_FINITE_ERROR_TESTS_COMPLETE' in s and 'M4_ERROR_TEST_FAILED:' not in s,s[-2000:]
review=dict(state='PASS_FOUR_TARGET_PREFLIGHT_CASES_NO_STALE_TOKEN',variant=a.variant,case=a.case,actual_cases=events,scope='Preflight only, first16B of routed/merged/sparse unchanged; full-array normal correctness separately verified')
(D/'INDEPENDENT_REVIEW.json').write_text(json.dumps(review,indent=2)+'\n');print(json.dumps(review,indent=2))
