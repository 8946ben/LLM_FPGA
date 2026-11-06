"""Portable offline handoff checks; never connects to FPGA hardware."""
from __future__ import annotations
import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

MODULE = Path(__file__).resolve().parents[1]

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for data in iter(lambda: stream.read(8 << 20), b''):
            h.update(data)
    return h.hexdigest()

def verify_sums(base):
    count = 0
    for line in (base / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        expected, relative = line.split('  ', 1)
        path = (base / relative).resolve()
        if not path.is_relative_to(base.resolve()) or digest(path) != expected:
            raise AssertionError('SHA256 mismatch: ' + relative)
        count += 1
    print(f'SHA256SUMS=PASS files={count}', flush=True)

def check_ip():
    ns = {'s': 'http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009'}
    ip = MODULE / 'ip_repo/lm_head_v2'
    root = ET.parse(ip / 'component.xml').getroot()
    names = root.findall('s:fileSets/s:fileSet/s:file/s:name', ns)
    for node in names:
        path = (ip / node.text).resolve()
        if not path.is_relative_to(ip.resolve()) or not path.is_file():
            raise AssertionError('Missing IP file reference: ' + node.text)
    contract = json.loads((MODULE / 'interface/interface_contract.json').read_text(encoding='utf-8'))
    actual = []
    for reg in root.findall('s:memoryMaps/s:memoryMap/s:addressBlock/s:register', ns):
        reset = reg.find('s:reset/s:value', ns)
        actual.append({'name': reg.findtext('s:name', namespaces=ns),
                       'offset': int(reg.findtext('s:addressOffset', namespaces=ns), 0),
                       'width_bits': int(reg.findtext('s:size', namespaces=ns), 0),
                       'access': reg.findtext('s:access', namespaces=ns),
                       'reset': int(reset.text, 0) if reset is not None else None})
    if actual != contract['control_registers']:
        raise AssertionError('Interface register table differs from exported IP')
    header = MODULE / 'drivers/generated/xlm_head_v2_hw.h'
    if digest(header) != digest(MODULE / 'reports/hls/xlm_head_v2_hw.h'):
        raise AssertionError('Generated driver header differs from archived HLS header')
    print(f'IP_REFERENCES_AND_REGISTERS=PASS files={len(names)} registers={len(actual)}', flush=True)

def check_raw_mailboxes():
    spec = importlib.util.spec_from_file_location('delivery_mailbox_parser', MODULE / 'standalone/parse_mailbox.py')
    parser = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser)
    campaign = json.loads((MODULE / 'reports/board_runs/20261010_104006_168_acceptance/campaign_portable.json').read_text(encoding='utf-8'))
    for record in campaign['records']:
        path = MODULE / record['source_run'] / 'mailbox_output.bin'
        saved = sys.argv
        captured = io.StringIO()
        try:
            sys.argv = ['parse_mailbox.py', str(path), '--step', record['step']]
            with contextlib.redirect_stdout(captured):
                code = parser.main()
        finally:
            sys.argv = saved
        expected_code = 1 if record['campaign_phase'] == 'golden_failure' else 0
        if code != expected_code:
            raise AssertionError('Unexpected raw mailbox state: ' + record['source_run'])
        decoded, _ = json.JSONDecoder().raw_decode(captured.getvalue())
        for key, value in decoded.items():
            if key != 'source_run' and record[key] != value:
                raise AssertionError('Raw mailbox differs from campaign: ' + record['source_run'] + ':' + key)
    print(f'RAW_MAILBOX_CAMPAIGN_CROSS_CHECK=PASS runs={len(campaign["records"])}', flush=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-hashes', action='store_true')
    args = parser.parse_args()
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    if not args.skip_hashes:
        verify_sums(MODULE.parent)
        verify_sums(MODULE)
    check_ip()
    check_raw_mailboxes()
    def run(arguments, cwd=MODULE):
        print('RUN ' + ' '.join(str(x) for x in arguments), flush=True)
        subprocess.run([sys.executable, '-B', *map(str, arguments)], cwd=cwd, check=True)
    run(['-m', 'unittest', 'discover', '-p', 'test_*.py', '-v'], MODULE / 'reference')
    run(['reference/validate_source_contract.py'])
    run(['reference/verify_assets.py', '--asset-root', MODULE.parent / 'artifacts/module14_v2_assets',
         '--manifest', MODULE / 'golden/v2_trace_manifest.json'])
    temp_root = MODULE / 'build/delivery_checks'
    temp_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='m14_delivery_', dir=temp_root) as directory:
        output = Path(directory) / 'summary.json'
        run(['scripts/summarize_acceptance.py',
             'reports/board_runs/20261010_104006_168_acceptance/campaign_portable.json',
             '--manifest', 'golden/v2_trace_manifest.json', '--output', output])
        summary = json.loads(output.read_text(encoding='utf-8'))
        if summary['state'] != 'PASS':
            raise AssertionError(summary)
    print('DELIVERY_OFFLINE_VERIFY=PASS (no hardware access)', flush=True)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
