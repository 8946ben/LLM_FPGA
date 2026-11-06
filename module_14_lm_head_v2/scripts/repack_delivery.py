"""Repack an edited delivery directory in place, preserving its payload content."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

WORKSPACE = Path(__file__).resolve().parents[2]

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

def payload_files(base):
    return sorted(p for p in base.rglob('*') if p.is_file()
                  and not {'__pycache__', 'build', '.cache', '.Xil'}.intersection(p.relative_to(base).parts))

def manifest_state(base):
    changed, missing = [], []
    tracked = set()
    for line in (base / 'SHA256SUMS').read_text(encoding='utf-8-sig').splitlines():
        expected, relative = line.split('  ', 1)
        tracked.add(relative)
        path = (base / relative).resolve()
        if not path.is_relative_to(base.resolve()):
            raise ValueError('Manifest escapes delivery directory')
        if not path.is_file():
            missing.append(relative)
        elif sha(path) != expected:
            changed.append(relative)
    added = [p.relative_to(base).as_posix() for p in payload_files(base)
             if p != base / 'SHA256SUMS' and p.relative_to(base).as_posix() not in tracked]
    return {'changed': changed, 'removed': missing, 'added': added}

def refresh_manifest(base):
    content = ''.join(f'{sha(p)}  {p.relative_to(base).as_posix()}\n'
                      for p in payload_files(base) if p != base / 'SHA256SUMS')
    target = base / 'SHA256SUMS'
    if target.read_text(encoding='utf-8') != content:
        target.write_text(content, encoding='utf-8')

def dump(path, document):
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('delivery', type=Path)
    args = parser.parse_args()
    base = args.delivery.resolve()
    if not base.is_relative_to(WORKSPACE / 'deliverables') or not base.is_dir():
        raise ValueError('Expected existing delivery directory inside workspace/deliverables')
    output = base.parent
    module = base / 'module_14_lm_head_v2'
    timestamp = datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d_%H%M%S')
    backup = output / ('history/pre_repack_' + timestamp)
    backup.mkdir(parents=True)
    previous_path = output / 'DELIVERY_VALIDATION.json'
    previous = json.loads(previous_path.read_text(encoding='utf-8')) if previous_path.exists() else {}
    for name in ['DELIVERY_VALIDATION.json', 'ZIP_SHA256SUMS.txt', 'STAGING_VALIDATION.log', 'EXTRACTED_VALIDATION.log']:
        if (output / name).is_file():
            shutil.copy2(output / name, backup / name)
    shutil.copy2(base / 'SHA256SUMS', backup / 'ROOT_SHA256SUMS.previous')
    shutil.copy2(module / 'SHA256SUMS', backup / 'MODULE_SHA256SUMS.previous')
    edits = {'root': manifest_state(base), 'module': manifest_state(module)}
    dump(backup / 'payload_changes.json', edits)
    original_payload = {p.relative_to(base).as_posix(): sha(p) for p in payload_files(base)
                        if p.name != 'SHA256SUMS'}
    refresh_manifest(module)
    refresh_manifest(base)
    expected = {p.relative_to(base).as_posix(): sha(p) for p in payload_files(base)}
    def verify(directory, log):
        result = subprocess.run([sys.executable, '-B', str(directory / 'module_14_lm_head_v2/scripts/run_tests.py')],
                                cwd=directory, capture_output=True, text=True)
        log.write_text(result.stdout + result.stderr, encoding='utf-8')
        if result.returncode:
            raise RuntimeError('Offline validation failed; inspect ' + str(log))
    print('REPACK_STAGING_VERIFY=RUNNING', flush=True)
    verify(base, output / 'STAGING_VALIDATION.log')
    print('REPACK_STAGING_VERIFY=PASS', flush=True)
    temporary_zip = output / (base.name + '.repack.tmp.zip')
    if temporary_zip.exists():
        raise FileExistsError(temporary_zip)
    with zipfile.ZipFile(temporary_zip, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
        for relative in expected:
            if sha(base / relative) != expected[relative]:
                raise RuntimeError('Payload changed while repacking: ' + relative)
            archive.write(base / relative, base.name + '/' + relative)
    extracted = output / ('verify_repack_' + timestamp)
    with zipfile.ZipFile(temporary_zip) as archive:
        expected_names = {base.name + '/' + relative for relative in expected}
        if set(archive.namelist()) != expected_names or archive.testzip() is not None:
            raise RuntimeError('ZIP inventory/CRC failure')
        archive.extractall(extracted)
    restored = extracted / base.name
    verify(restored, output / 'EXTRACTED_VALIDATION.log')
    print('REPACK_EXTRACTED_VERIFY=PASS', flush=True)
    for relative, digest in original_payload.items():
        if sha(base / relative) != digest or sha(restored / relative) != digest:
            raise AssertionError('Edited payload not preserved: ' + relative)
    binaries = 0
    for name in ['board_package_20261009', 'tcp_loader_package_20261010']:
        package = restored / 'module_14_lm_head_v2/reports' / name
        for line in (package / 'ARTIFACTS.sha256').read_text(encoding='utf-8').splitlines():
            digest, relative = line.split('  ', 1)
            if sha(package / relative) != digest:
                raise AssertionError('Frozen artifact mismatch: ' + relative)
            binaries += 1
    archive = output / (base.name + '.zip')
    if archive.exists():
        shutil.move(str(archive), str(backup / archive.name))
    temporary_zip.replace(archive)
    result = {**previous, 'state': 'PASS', 'archive': archive.name, 'version': base.name,
              'updated_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
              'bytes': archive.stat().st_size, 'sha256': sha(archive), 'files': len(expected),
              'staging_validation': 'PASS', 'extracted_validation': 'PASS',
              'edited_payload_preserved': True, 'payload_changes': edits, 'hardware_access': False,
              'frozen_binary_hashes': {'state': 'PASS', 'files': binaries},
              'vivado_catalog_validation_note': 'Previous catalog check retained; IP bytes unchanged in documented wording-only revision',
              'previous_validation_backup': backup.relative_to(output).as_posix(),
              'previous_archive_sha256': previous.get('sha256')}
    dump(previous_path, result)
    (output / 'ZIP_SHA256SUMS.txt').write_text(f"{result['sha256']}  {archive.name}\n", encoding='utf-8')
    dump(output / 'REPACK_CHANGES.json', edits)
    # Only remove this newly created extraction after verifying its absolute scope.
    if extracted.parent != output or not extracted.name.startswith('verify_repack_'):
        raise AssertionError('Unexpected extraction cleanup target')
    shutil.rmtree(extracted)
    print(json.dumps(result, ensure_ascii=True, indent=2), flush=True)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
