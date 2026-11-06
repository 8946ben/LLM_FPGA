"""Read-only numerical audit of preserved failed CoSim TV; never runs EDA."""
from pathlib import Path
import datetime, hashlib, json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / 'module_14_lm_head_v4/reports/partial_rtl_20261024_r1/full_r3'
FIX = ROOT / 'module_14_lm_head_v4/experiments/partial_hw_20261024/fixtures'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def values(p):
    lines = p.read_text().splitlines()
    assert lines[0] == '[[[runtime]]]' and lines[-1] == '[[[/runtime]]]'
    return [int(x, 16) for x in lines if x.startswith('0x')]

def main():
    workflow = json.loads((R / 'FULL_WORKFLOW.json').read_text())
    after = json.loads((R / 'PROCESS_AFTER.json').read_text())
    assert workflow['state'] == 'FAILED_NO_AUTOMATIC_RETRY'
    assert not after['owned_process_group_members'] and after['active_locks'] == 0
    files = sorted((R / 'returned_tv').glob('*/*.dat'))
    manifest = {str(p.relative_to(R)).replace('\\', '/'): dict(bytes=p.stat().st_size, sha256=sha(p)) for p in files}
    cdir, adir = R / 'returned_tv/cdatafile', R / 'returned_tv/rtldatafile'
    def path(d, name):
        return next(d.glob('*_{}.dat'.format(name)))
    def words(d):
        return np.array([[(v >> (32*j)) & 0xffffffff for j in range(4)]
                         for v in values(path(d, 'meta'))], dtype='<u4').reshape(-1)
    c, a = words(cdir), words(adir)
    assert len(c) == len(a) == 80591 * 4
    # Both C pointers share the meta master: 1523 input beats then workspace.
    # Generated ref.tcl reports meta depth 80591, including the last workspace beat.
    origin = 1523 * 4
    assert np.array_equal(a[:origin], np.fromfile(FIX/'old_chinese.meta.bin', dtype='<u4'))
    assert np.array_equal(c[:origin], a[:origin])
    scalar = {}
    for name in ['status', 'token', 'score_bits', 'candidate_count', 'output_crc', 'preview_read_beats']:
        cv, av = values(path(cdir, name)), values(path(adir, name))
        assert len(cv) == len(av) == 1
        scalar[name] = dict(reference=cv[0], rtl=av[0], equal=cv == av)
    k = scalar['candidate_count']['reference']
    assert k == 4109
    sections = dict(keys=(0,151936), preview=(37984,151936),
                    table_header=(75968,4), candidate_ids=(75969,k),
                    candidate_raw_records=(76997,2*k), dims=(79052,64),
                    end_guard=(79068,4))
    comparisons = {}
    for name, (beat, count) in sections.items():
        off = origin + beat*4
        expected, actual = c[off:off+count], a[off:off+count]
        bad = np.flatnonzero(actual != expected)
        comparisons[name] = dict(values=count, mismatches=len(bad),
            first_mismatches=[dict(index=int(i), reference_bits=hex(int(expected[i])),
                                  rtl_bits=hex(int(actual[i]))) for i in bad[:8]])
        if name in ['keys','preview','dims','candidate_ids']:
            ext = 'ids' if name == 'candidate_ids' else name
            fixture = np.fromfile(FIX/('old_chinese.'+ext+'.bin'), dtype='<u4')
            assert np.array_equal(expected, fixture), 'C TV differs from frozen fixture: '+name
    preview = a[origin+37984*4:origin+75968*4]
    expected = c[origin+37984*4:origin+75968*4]
    bad = np.flatnonzero(preview != expected)
    runs = []
    for chunk in np.split(bad, np.flatnonzero(np.diff(bad) != 1)+1):
        if len(chunk): runs.append([int(chunk[0]), int(chunk[-1])])
    eids = c[origin+75969*4:origin+75969*4+k]
    aids = a[origin+75969*4:origin+75969*4+k]
    changed_set = dict(reference_only=len(set(map(int,eids))-set(map(int,aids))),
                       rtl_only=len(set(map(int,aids))-set(map(int,eids))))
    assert comparisons['preview']['mismatches'] == 5120
    assert runs == [[0,5119]]
    # A reference-stage actual_RTL_full_chinese.bin is not RTL output: TB fails
    # before writing that filename during C postcheck. Audit raw returned TV only.
    a[origin:].tofile(R/'RTL_RETURNED_WORKSPACE.u32.bin')
    result = dict(state='CONFIRMED_FULL_COSIM_NUMERICAL_FAILURE',
        reviewed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        workflow_state=workflow['state'], finished_utc=workflow['finished'],
        primary_error='CSIM_FAIL full preview bits RTL_full_chinese',
        report_status='Verilog Fail', observed_pressure_latency_cycles=83748670,
        latency_is_not_fpga_decode=True, scalar_returns=scalar, comparisons=comparisons,
        preview_mismatch_word_id_ranges_inclusive=runs,
        changed_candidate_set=changed_set, returned_tv_files=manifest,
        returned_workspace_sha256=sha(R/'RTL_RETURNED_WORKSPACE.u32.bin'),
        root_cause='UNRESOLVED', dsp_warning_causality='UNRESOLVED',
        qualification='FAIL: full arrays required; matching final scalars do not override mismatch',
        reference_actual_file_is_not_rtl_evidence=True,
        source_stop_audit=after, automatic_retry=False, board='NOT_RUN')
    (R/'FAILURE_REVIEW.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(state=result['state'], preview_mismatches=len(bad),
                         changed_candidate_set=changed_set, scalar_equal=all(x['equal'] for x in scalar.values()))))

if __name__ == '__main__':
    main()
