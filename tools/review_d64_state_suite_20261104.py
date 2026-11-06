"""Independent byte/ABI checks of r2 preparations; does not grant RTL qualification."""
import datetime, hashlib, json, struct
from prepare_d64_state_suite_20261104 import ROOT, M, E, R, OLD, sha

def main():
    old = M / 'reports' / OLD
    p = json.loads((R / 'MANIFEST.json').read_text())
    c = json.loads((E / 'control_sequences.json').read_text())
    assert p['state'] == 'PREPARED_AND_SOURCE_REFERENCE_BOUND_NOT_SIMULATED'
    assert c['state'] == 'CONTROL_SEQUENCES_PREPARED_NOT_EXECUTED'
    assert c['manifest_sha256'] == sha(R / 'MANIFEST.json')
    assert p['predecessor']['manifest_sha256'] == sha(old / 'MANIFEST.json')
    assert p['predecessor']['review_sha256'] == sha(old / 'INDEPENDENT_PREPARATION_REVIEW.json')
    assert not (R / 'WORKFLOW.json').exists() and not (R / 'ACTIVE.lock').exists()
    labels = ['A0_debug', 'B0_debug', 'A1_debug', 'A_production', 'Z0_ties', 'E_capacity',
              'E_flag', 'E_hidden_nan', 'E_rms_nan', 'E_rms_negative', 'E_preview_nan', 'A2_after_errors']
    assert [s['label'] for s in p['scenarios']] == labels
    assert len(c['sequences']) == 12
    assert json.loads((E / 'scenarios.json').read_text()) == p['scenarios']
    for n, h in p['source_sha256'].items():
        assert sha(ROOT / n) == h, n
    weight_bytes = 0
    for n, asset in p['weight_assets'].items():
        path = ROOT / n; digest = hashlib.sha256()
        assert path.stat().st_size == asset['bytes']
        with path.open('rb') as source:
            for chunk in iter(lambda: source.read(1048576), b''):
                digest.update(chunk)
        assert digest.hexdigest() == asset['sha256'], n
        weight_bytes += asset['bytes']
    assert weight_bytes == 545685504
    data = []
    for i, (s, seq) in enumerate(zip(p['scenarios'], c['sequences'], strict=True)):
        b = (ROOT / s['input_path']).read_bytes(); data.append(b)
        assert len(b) == 24368 and sha(ROOT / s['input_path']) == s['input_sha256']
        assert s['case_index'] == seq['case_index'] == i and s['label'] == seq['label']
        assert not seq['reset_dut_before_case'] and not seq['reload_full_weights'] and seq['workspace_persists']
        writes = {x['address']: x['value'] for x in seq['parameter_writes']}
        assert writes == {0x10: 0, 0x14: 0, 0x1c: 0, 0x20: 0, 0x28: 273416192,
                          0x2c: 0, 0x34: 24368, 0x38: 0, 0x40: s['capacity'], 0x48: s['debug']}
        assert {x['address']: x['expected'] for x in seq['parameter_readbacks']} == writes
        assert all(x['strobe'] == 15 for x in seq['parameter_writes'])
        assert seq['output_validity_clear_before_start'] == seq['output_validity_required_after_done'] == [84,100,116,132,148,168]
        assert seq['output_reads'] == {'status':[80], 'token':[96], 'score_bits':[112],
                                      'candidate_count':[128], 'output_crc':[144], 'preview_read_beats':[160,164]}
        assert seq['start_write'] == {'address':0, 'value':1, 'strobe':15}
    f = M / 'experiments/partial_hw_20261024/fixtures'
    a = (f / 'old_chinese.meta.bin').read_bytes()
    assert all(data[i] == a for i in [0,2,3,5,6,10,11])
    assert data[1] == (f / 'old_english.meta.bin').read_bytes() != a
    assert data[4] == (f / 'zero_hidden.meta.bin').read_bytes() and data[4][:1792] == bytes(1792)
    assert [s['debug'] for s in p['scenarios'][:5]] == [1,1,1,0,1]
    for i, offset, replacement in [(7,0,b'\xc0\x7f'), (8,1792,b'\0\0\xc0\x7f'), (9,1792,b'\0\0\x80\xbf')]:
        assert data[i] == a[:offset] + replacement + a[offset+len(replacement):]
    for i in [5,6,7,8,9,10]:
        s = p['scenarios'][i]
        assert s['expected'] == dict(expected_status=1 if i in [5,6] else 2, token=0, score_bits=0, crc=0, k=0, preview_read_beats=0)
        if i < 10:
            assert s['access_invariants']['weight_reads'] == s['access_invariants']['workspace_writes'] == 0
    injection = p['scenarios'][10]['mutations'][0]
    dims = struct.unpack('<64I', (f / 'old_chinese.dims.bin').read_bytes())
    assert injection['offset_bytes'] == dims[0] * 2048 and injection['replacement_hex'] == 'c07f' and injection['restore_after']
    # Same token/raw expectation in production; raw writes themselves must be absent.
    assert p['scenarios'][0]['expected'] == p['scenarios'][2]['expected'] == p['scenarios'][3]['expected'] == p['scenarios'][11]['expected']
    out = dict(state='PASS_INDEPENDENT_PREPARATION_ONLY', utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               cases=12, full_debug_ABA_prepared=True, separate_A_production_prepared=True,
               weight_bytes_sha_rechecked=weight_bytes,
               manifest_sha256=sha(R/'MANIFEST.json'), control_sha256=sha(E/'control_sequences.json'),
               not_proven=['RTL compile/run', 'Full persistent-DUT A/B/A', 'Mode/error response', 'Normal-response model', 'Timing'],
               eda='NOT_RUN', board='NOT_RUN', automatic_next_stage=False)
    (R / 'INDEPENDENT_PREPARATION_REVIEW.json').write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps(out, indent=2))

if __name__ == '__main__':
    main()
