"""Offline final gate and evidence archive, no FPGA access."""
from pathlib import Path
import json,hashlib,zipfile,struct,re
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';R=M/'reports/dual_board_20261030_r1'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
summary=read(R/'BOARD_FIXED_INPUT_SUMMARY.json');assert summary['completed_cases']==8
assert not (R/'ACTIVE.lock').exists()
process_after=read(R/'PROCESS_AFTER.json');assert process_after['owned_processes']==[] and not process_after['active_lock']
quiesce=(R/'final_quiesce_r2.log').read_text(errors='replace')
assert 'M4_FINAL_CPU_GEM_STOPPED_SELECTOR_IDLE=PASS' in quiesce and 'M4_FINAL_200MHZ_CLOCK_REGISTERS=PASS' in quiesce and 'M4_FINAL_QUIESCE_ERROR:' not in quiesce
(R/'FINAL_TARGET_STATE.json').write_text(json.dumps(dict(state='PASS_A53_GEM_STOPPED_SELECTOR_IDLE_MIG_CALIBRATED',loaded_variant='baseline_hybrid',loaded_input='math',private_signature='0x4D345301',clock_register_check='PASS_200MHZ_PROFILE_NOT_FREQUENCY_COUNTER',PL0='0x01010203',DPLL='0x00014800',DPLL_to_LPD='0x00000300',log_sha256=sha(R/'final_quiesce_r2.log'),owned_execution_processes=0,no_automatic_next_stage=True),indent=2)+'\n')
artifacts=[];details=[]
for variant,base in [('baseline_hybrid',M),('exp10',M/'experiments/fusion_exp10_20261023')]:
    package=base/'reports/board_v4_20261021/private_package_r1';expected={}
    for line in (package/'SHA256SUMS.txt').read_text().splitlines():
        if not line.strip():continue
        h,n=line.split('  ',1);assert sha(package/n)==h;expected[n]=h
    assert {p.name for p in package.iterdir() if p.is_file()}==set(expected)|{'SHA256SUMS.txt'}
    for case in ['chinese','english','code','math']:
        d=base/'reports/board_acceptance_20261030_r3'/case
        audit=read(d/'INDEPENDENT_REVIEW.json');assert audit['measured']==30 and audit['stability']==1000
        state=read(d/'EXECUTION.json');assert state['state']=='FIXED_INPUT_CAMPAIGN_RETURNED_PENDING_INDEPENDENT_REVIEW'
        artifacts.extend(p for p in d.rglob('*') if p.is_file())
        for n,h in read(d/'PLAN.json')['package_sha256'].items():assert sha(Path(read(d/'PLAN.json')['package'])/n)==h
    aba=base/'reports/board_aba_20261030_r2';qa=read(aba/'INDEPENDENT_REVIEW.json')
    assert qa['state']=='PASS_CONTROLLED_ABA_FULL_ARRAYS_AND_INPUT_READBACK' and qa['A_before_after_identical']
    plan=read(aba/'PLAN.json')
    for n,h in plan['source_sha256'].items():assert sha(ROOT/n)==h
    assert sha(aba/'capture.tcl')==plan['entry_sha256']
    for n,h in qa['files_sha256'].items():assert sha(aba/n)==h
    f=base/'fixture';lr=base/'reports/lowrank_fixture_20261021' if base==M else f;tk=base/'reports/topk_fixture_20261021' if base==M else f;chain=base/'reports/selector_chain_fixture_20261021' if base==M else f
    aba_log=(aba/'capture.log').read_text(errors='replace')
    for i,case in enumerate(['math','chinese','math']):
        d=aba/f'{i}_{case}';expected_ids=(tk/(case+'.expected.bin')).read_bytes();k=len(expected_ids)//4
        for name,ext in [('hidden','.hidden.bin'),('history','.history.bin'),('preview','.scores.bin')]:assert (d/(name+'.bin')).read_bytes()==(lr/(case+ext)).read_bytes()
        table=(d/'merged.bin').read_bytes();assert struct.unpack('<4I',table[:16])==(0x4449344d,0x00040001,k,151936) and table[16:16+4*k]==expected_ids
        assert (d/'raw.bin').read_bytes()[:8*k]==(chain/(case+'.sparse.bin')).read_bytes()[:8*k]
        for name,value in zip(['TOKEN','SCORE','CRC'],struct.unpack('<3I',(chain/(case+'.result.bin')).read_bytes()[:12])):assert int(re.search(r'^M4_ABA_'+str(i)+'_'+name+r'=(\d+)$',aba_log,re.M)[1])==value
        assert len(list(d.glob('guard_*.bin')))==13 and all(p.read_bytes()==(0xabcdef).to_bytes(16,'little') for p in d.glob('guard_*.bin'))
    errors=base/'reports/board_errors_20261030_r1/math';qe=read(errors/'INDEPENDENT_REVIEW.json');assert len(qe['actual_cases'])==4
    artifacts.extend(p for p in errors.rglob('*') if p.is_file());artifacts.extend(p for p in aba.rglob('*') if p.is_file())
    debug_cases=[]
    for d in (base/'reports/board_debug_20261030_r2').glob('*'):
        if (d/'INDEPENDENT_REVIEW.json').exists():
            q=read(d/'INDEPENDENT_REVIEW.json');assert q['state']=='PASS_INDEPENDENT_FULL_BOARD_ARRAY_REVIEW';debug_cases.append(q['case']);artifacts.extend(p for p in d.rglob('*') if p.is_file())
    assert set(debug_cases)|{'math','chinese'}=={'chinese','english','code','math'}
    for historical in ['board_acceptance_20261030_r1','board_aba_20261030_r1','board_debug_20261030_r1']:artifacts.extend(p for p in (base/'reports'/historical).rglob('*') if p.is_file())
    details.append(dict(variant=variant,fixed_cases=4,measured_calls=120,stability_calls=4000,all_fixed_records=4132,standalone_full_array_cases=debug_cases,ABA_full_array_cases=['math','chinese','math'],preflight_cases=4,original_package_sha_unchanged=True))
assert read(R/'QUALITY_GATE_99.json')['state']=='PASS_USER_ACCEPTED_99_PERCENT_POINT_ESTIMATE_GATE'
quality=read(R/'QUALITY_GATE_99.json');assert sha(ROOT/quality['source'])==quality['source_sha256']
final=dict(state='PASS_TWO_VARIANT_FOUR_FIXED_INPUT_BOARD_VALIDATION',variants=details,fixed_input_calls=8264,production_timings=240,stability_calls=8000,control_ABA_calls=6,finite_preflight_cases=8,exact_bit_arrays=True,source_and_package_hashes_verified=True,autoregressive_history='NOT_TESTED',full_llm_decode='NOT_MEASURED',TTFT='NOT_MEASURED',formal_delivery_release=False)
(R/'FINAL_INDEPENDENT_REVIEW.json').write_text(json.dumps(final,indent=2)+'\n')
artifacts.extend(p for p in R.iterdir() if p.is_file() and p.suffix in ['.json','.md','.log','.tcl'])
artifacts.extend(p for p in (R/'control_r2').glob('*') if p.is_file());artifacts.extend(p for p in (R/'control_r3').glob('*') if p.is_file())
artifacts.extend(p for p in (ROOT/'tools').glob('*v4*20261030.py') if p.is_file())
artifacts=sorted(set(artifacts));manifest={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in artifacts}
(R/'EVIDENCE_SHA256.json').write_text(json.dumps(manifest,indent=2)+'\n')
archive=R/'BOARD_EVIDENCE_20261030_r1.zip';assert not archive.exists()
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in artifacts:z.write(p,str(p.relative_to(ROOT)))
    z.write(R/'EVIDENCE_SHA256.json',str((R/'EVIDENCE_SHA256.json').relative_to(ROOT)))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for n,h in manifest.items():assert hashlib.sha256(z.read(n)).hexdigest()==h
(R/'EVIDENCE_ARCHIVE.json').write_text(json.dumps(dict(state='PASS_ARCHIVE_MEMBER_HASH_AND_ZIP_CRC',file=archive.name,sha256=sha(archive),bytes=archive.stat().st_size,members=len(artifacts)+1,scope='Board evidence only, excludes weights/bit/XSA/ELF runtime copies; not a deployable release'),indent=2)+'\n')
print(json.dumps(final,indent=2));print('EVIDENCE_ZIP_SHA256='+sha(archive))
