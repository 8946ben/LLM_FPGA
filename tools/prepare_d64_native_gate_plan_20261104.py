"""Freeze a local draft gate plan. Does not compile, upload, or launch anything."""
from pathlib import Path
import json, hashlib, datetime, ast

ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4'
E=M/'experiments/d64_native_memory_20261103_r1';R=M/'reports/d64_native_memory_20261103_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    changes=json.loads((E/'CHANGES.json').read_text())
    model=E/'d64_native_memory.sv';text=model.read_text()
    assert sha(model)==changes['candidate_sha256']=='48153808aa8c001a9174fa45d161e9a03867df0b6ba6d9f47b758cde3973db38'
    original=ROOT/changes['original_path'];assert sha(original)==changes['original_sha256']
    for before,after in reversed(changes['edits']):
        assert text.count(after)==1;text=text.replace(after,before)
    assert text==original.read_text()
    ast.parse((ROOT/'tools/review_d64_native_gate_20261104.py').read_text())
    cases={
        'positive':None,
        'readonly':'NATIVE_MODEL_READ_ONLY_WRITE',
        'wlast':'WLAST mismatch',
        'xstrobe':'NATIVE_MODEL_UNKNOWN_WSTRB',
        'ar_stability':'AR unstable during stall',
        'aw_stability':'AW unstable during stall',
        'w_stability':'W unstable during stall',
        **{x:'NATIVE_MODEL_RANGE_REJECT' for x in ['below','end','over_end','high','alignment','size','burst','length']},
        '4k':'AXI crossed4KiB',
        **{x:'NATIVE_MODEL_UNKNOWN_ADDRESS_CONTROL' for x in ['xaddr','xlen','xsize','xburst']},
        'xid':'NATIVE_MODEL_UNKNOWN_ARID'}
    out=dict(state='PREPARED_NOT_COMPILED_OR_QUALIFIED',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        sources={p.relative_to(ROOT).as_posix():sha(p) for p in [model,E/'native_gate_tb.sv',E/'CHANGES.json',ROOT/'tools/review_d64_native_gate_20261104.py']},
        backing_model_sha256='07e2f1b17f10b989bdb980cc208c463c914170c14fc598851f71aeba21e74c40',
        cases=[dict(case=k,expected_fatal=v) for k,v in cases.items()],
        positive=dict(data_bits=128,base_address_hex='0x100000000',logical_bytes=536870976,
            storage_guard_bytes=16,read_requests=1038,read_beats=131108,write_requests=11,write_beats=152,
            b_responses=10,reset_canceled_read_requests=1,reset_canceled_b_responses=1,epochs=4,
            repeated_epoch_read_beats=131072,memory_capacity_growth_during_epochs=False,
            checks=['Host four-state replay every R/W byte, IDs/LAST/order/WSTRB',
                    'Distinct 512MiB address pairs and first/last logical word',
                    'Separate legal AXI bursts on both sides of1MiB backing boundary',
                    'R/B prolonged backpressure and W-before-AW',
                    'Concurrent disjoint read/write',
                    'Reset cancels outstanding R/B without clearing storage',
                    'Partial/zero strobes preserve unwritten X lanes and actual extra end guard']),
        planned_guards=dict(group_gib=8,system_available_gib=32,elaborate_seconds=300,each_case_seconds=180,sim_watchdog_ns=5000000),
        required_before_eda='Current full strong-stress run must return, independent process/lock-empty and full numerical/FIFO PASS; manual decision and bounded runner still required.',
        required_before_M14='This new model must pass actual compiled-source, positive trace, every expected rejection, resource and independent audits.',
        qualifications_not_granted=['No SV compilation','No native AXI execution','No full M14 A/B/A/modes','No performance numbers'],
        eda='NOT_RUN',board='NOT_RUN',automatic_next_stage=False)
    target=R/'GATE_PREPARATION_PLAN.json';assert not target.exists()
    target.write_text(json.dumps(out,indent=2)+'\n')
    (R/'RESUME.md').write_text('DRAFT additional normal-response model and bounded gate only. No EDA executed. '
        'See GATE_PREPARATION_PLAN.json. Original current full strong-random-delay call is preserved; '
        'no parallel EDA or substitution. Actual model qualification and persistent full-DUT suite remain pending.\n')
    print(json.dumps(dict(state=out['state'],cases=len(cases),model_sha256=sha(model)),indent=2))

if __name__=='__main__':main()
