"""Offline verification of a staged/extracted v3.1 delivery (never hardware)."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
import zipfile


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(8 << 20), b''): h.update(chunk)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path)
    a = p.parse_args()
    root = a.root.resolve()
    module = root / 'module_14_lm_head_v3_1'
    sums = {}
    for line in (root / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        digest, name = line.split('  ', 1)
        f = (root / name).resolve()
        assert f.is_relative_to(root) and f.is_file() and name not in sums
        assert sha(f) == digest, 'SHA mismatch: ' + name
        sums[name] = digest
    actual = {f.relative_to(root).as_posix() for f in root.rglob('*') if f.is_file()
              and f != root / 'SHA256SUMS' and '__pycache__' not in f.parts}
    assert set(sums) == actual, 'Inventory mismatch'
    read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
    manifest = read(module / 'module_manifest.json')
    assert manifest['build_config'] == '0x30c08011' and manifest['module_revision'] == 3
    for name, digest in manifest['tested_source_sha256'].items():
        assert sha(module / name) == digest, 'Tested source mismatch: ' + name
    package = module / 'reports/board_v31_20261019/package'
    for line in (package / 'ARTIFACTS.sha256').read_text(encoding='utf-8').splitlines():
        digest, name = line.split('  ', 1)
        assert sha(package / name) == digest, name
    sys.path.insert(0, str(module / 'standalone'))
    from board_profile import load_profile, check_loader_pair
    assert load_profile(package)['data_memory'] == 'PL_DDR'
    assert check_loader_pair(package, package, '192.168.0.190')
    with zipfile.ZipFile(package / 'm14_v31_single.xsa') as z:
        name = next(n for n in z.namelist() if n.endswith('.bit'))
        assert hashlib.sha256(z.read(name)).hexdigest() == sha(package / 'm14_v31_system_wrapper.bit')
    hardware = module / 'reports/board_v31_20261019/hardware'
    for name in ('m14_v31_single.xsa', 'm14_v31_system_wrapper.bit'):
        assert sha(hardware / name) == sha(package / name), 'Rebuild/deployment hardware mismatch: ' + name
    build = read(package / 'BUILD_SOURCES.json')
    for name, digest in build['source_sha256'].items():
        assert sha(module / name) == digest, 'Compiled C source mismatch: ' + name
    for name, digest in build['elf_sha256'].items():
        assert sha(package / name) == digest, 'Compiled ELF mismatch: ' + name
    for campaign in manifest['portable_campaigns']:
        command = [sys.executable, '-B', str(module / 'scripts/summarize_acceptance.py'),
                   str(module / campaign), '--manifest', str(root / 'artifacts/module14_v2_assets/manifest.json'),
                   '--output', str(module / 'reports/board_v31_20261019' / ('offline_' + Path(campaign).parent.name + '.json'))]
        # Put derived validation output outside the sealed delivery inventory.
        import tempfile
        with tempfile.TemporaryDirectory(dir=root.parent) as temp:
            command[-1] = str(Path(temp) / 'summary.json')
            result = subprocess.run(command, cwd=module, capture_output=True, text=True)
            assert result.returncode == 0, result.stdout + result.stderr
    print('M14_V31_DELIVERY_VERIFY=PASS files=' + str(len(sums)))


if __name__ == '__main__': main()
