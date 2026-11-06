"""Read generated testbench evidence, without modifying any simulation output."""
from pathlib import Path
import hashlib, json, re

M = Path(__file__).resolve().parents[1]
S = M / 'build/selector_full_cosim_r2/hls/solution1/sim'
REPORT = S / 'verilog/lm_head_v4_selector.performance.result.transaction.xml'

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()

def transactions(report=REPORT):
    # Despite its .xml suffix, Vitis HLS 2021.1 writes a text table here.
    content = report.read_text(encoding='utf-8-sig')
    rows = re.findall(r'^transaction\s+(\d+):\s+(\d+)\s+(\d+|x)\s*$', content, re.M)
    assert [int(i) for i, _, _ in rows] == [0, 1], 'Missing/duplicate/unordered transactions'
    assert len(re.findall(r'^transaction\b', content, re.M)) == 2
    return [dict(index=int(i), cycles=int(c)) for i, c, _ in rows]

def preserved_completion():
    checkpoint_path = M / 'reports/pause_20261022/CHECKPOINT.json'
    checkpoint = json.loads(checkpoint_path.read_text(encoding='utf-8-sig'))
    assert checkpoint['state'] == 'PAUSED_BY_USER'
    verified = {}
    for name, digest in checkpoint['evidence_sha256'].items():
        p = M / name
        assert sha(p) == digest, 'Preserved evidence changed: ' + name
        verified[p.relative_to(M).as_posix()] = digest
    expected_names = {'plmem', 'status', 'stage', 'child_status', 'route_count',
                      'candidate_count', 'dense_fallback', 'token', 'score', 'output_crc'}
    expected_paths = {S / f'tv/rtldatafile/rtl.lm_head_v4_selector.autotvout_{n}.dat'
                      for n in expected_names}
    assert {M / e['path'] for e in checkpoint['outputs']} == expected_paths
    for e in checkpoint['outputs']:
        p = M / e['path']
        assert p.stat().st_size == e['bytes'] and sha(p) == e['sha256'], p.name
        with p.open('rb') as f:
            f.seek(max(0, p.stat().st_size - 64))
            assert f.read().strip().endswith(b'[[[/runtime]]]'), p.name
        verified[p.relative_to(M).as_posix()] = e['sha256']
    finish = []
    with (M / 'reports/selector_repaired_xsim_r5_20261021.log').open(encoding='utf-8-sig') as f:
        for line in f:
            assert 'ERROR:' not in line and 'Fatal:' not in line, 'Simulation error'
            if line.startswith('$finish called at time'):
                finish.append(line.strip())
    assert finish == checkpoint['raw_testbench_finish_lines'] and len(finish) == 1
    assert 'lm_head_v4_selector.autotb.v" Line 638' in finish[0]
    tb = (S / 'verilog/lm_head_v4_selector.autotb.v').read_text().splitlines()
    assert '$finish;' in tb[637]
    assert 'wait (all_finish == 1)' in '\n'.join(tb[630:638])
    cases = transactions()
    assert [{'index':c['index'], 'raw_report_cycles':c['cycles']} for c in cases] == checkpoint['raw_transactions_not_qualified']
    lat = (S / 'verilog/lm_head_v4_selector.result.lat.rb').read_text()
    assert f'$MAX_LATENCY = "{max(c["cycles"] for c in cases)}"' in lat
    assert f'$MIN_LATENCY = "{min(c["cycles"] for c in cases)}"' in lat
    return dict(state='PASS_PRESERVED_COMPLETION_ONLY_NOT_NUMERICS',
                checkpoint_sha256=sha(checkpoint_path), evidence_sha256=verified,
                finish=finish, transactions=cases,
                actual_report=REPORT.relative_to(M).as_posix(),
                correction='Read the actual generated .performance.result.transaction.xml text table; '
                           'original Tcl wrongly awaited report/verilog/result.transaction.rpt. '
                           'Original log/Tcl/output untouched. No synthetic completion marker.',
                numerical_validation='PENDING_FULL_TRACE_AND_ORIGINAL_C_POSTCHECK', board='NOT_RUN')
