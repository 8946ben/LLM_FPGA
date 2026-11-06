"""Extend audited preparation with debug A/B/A and separate production A. No EDA."""
from pathlib import Path
import copy, datetime, hashlib, json

ROOT = Path(__file__).resolve().parents[1]
M = ROOT / 'module_14_lm_head_v4'
OLD = 'd64_state_fixtures_20261103_r1'
NAME = 'd64_state_fixtures_20261104_r2'
E, R = M / 'experiments' / NAME, M / 'reports' / NAME

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    old_r, old_e = M / 'reports' / OLD, M / 'experiments' / OLD
    manifest = json.loads((old_r / 'MANIFEST.json').read_text())
    control = json.loads((old_e / 'control_sequences.json').read_text())
    audit = json.loads((old_r / 'INDEPENDENT_PREPARATION_REVIEW.json').read_text())
    assert audit['state'] == 'PASS_INDEPENDENT_PREPARED_STATE_FIXTURES_AND_CONTROL_ONLY'
    assert audit['manifest_sha256'] == sha(old_r / 'MANIFEST.json')
    assert audit['control_sequences_sha256'] == sha(old_e / 'control_sequences.json')
    assert not E.exists() and not R.exists()
    E.mkdir(); R.mkdir(); (E / 'cases').mkdir()
    # Full B debug raw is required for full-output ABA, beyond r1's B production.
    cases = copy.deepcopy(manifest['scenarios'])
    sequences = copy.deepcopy(control['sequences'])
    cases[1]['label'], cases[1]['debug'] = 'B0_debug', 1
    sequences[1]['label'] = 'B0_debug'
    production = copy.deepcopy(cases[0])
    production['label'], production['debug'] = 'A_production', 0
    cases.insert(3, production)
    sequences.insert(3, copy.deepcopy(sequences[0]))
    for i, (case, seq) in enumerate(zip(cases, sequences, strict=True)):
        data = (ROOT / case['input_path']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == case['input_sha256']
        target = E / 'cases' / ('%02d_%s.meta.bin' % (i, case['label']))
        target.write_bytes(data)
        case.update(case_index=i, input_path=target.relative_to(ROOT).as_posix(), input_sha256=sha(target))
        seq.update(case_index=i, label=case['label'])
        for write in seq['parameter_writes']:
            if write['address'] == 0x48:
                write['value'] = case['debug']
        for read in seq['parameter_readbacks']:
            if read['address'] == 0x48:
                read['expected'] = case['debug']
    manifest.update(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), scenarios=cases,
                    predecessor={'manifest_sha256': sha(old_r / 'MANIFEST.json'),
                                 'review_sha256': sha(old_r / 'INDEPENDENT_PREPARATION_REVIEW.json')},
                    revision_scope='A(debug)-B(debug)-A(debug) complete arrays; separate A production without resetting DUT or workspace.')
    (E / 'scenarios.json').write_text(json.dumps(cases, indent=2) + '\n')
    (R / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
    control.update(utc=manifest['utc'], manifest_sha256=sha(R / 'MANIFEST.json'), sequences=sequences,
                   normal_response_condition='Separate draft model exists, NOT_COMPILED_OR_QUALIFIED. No execution authorized by this preparation.')
    (E / 'control_sequences.json').write_text(json.dumps(control, indent=2) + '\n')
    (R / 'RESUME.md').write_text(
        'PREPARED_NOT_SIMULATED. Twelve persistent-DUT scenarios. Full debug A/B/A plus separate production A. '
        'Original r1 preserved. No EDA or board operation. Require current strong-stress full result and '
        'independent model qualification before manual execution.\n')
    print(json.dumps({'state': 'PREPARED_NOT_SIMULATED', 'cases': len(cases), 'report': str(R)}, indent=2))

if __name__ == '__main__':
    main()
