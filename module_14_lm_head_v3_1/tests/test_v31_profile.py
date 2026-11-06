"""Reject internally inconsistent PL DDR profiles even if their hash is valid."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

M = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(M / 'standalone'))
from board_profile import load_profile, check_loader_pair


class ProfileContract(unittest.TestCase):
    def test_missing_deploy_profile_rejected_before_hardware(self):
        root = M / 'build/address_contract'
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as directory:
            with self.assertRaisesRegex(ValueError, 'requires RUN_PROFILE'):
                check_loader_pair(directory, directory, '192.168.0.190')

    def test_fail_closed_map(self):
        profile = dict(format='M14_BOARD_RUN_PROFILE_V2', build_config='0x30c08011',
                       ip_clock_hz=200000000, capabilities='0x382', data_memory='PL_DDR',
                       ps_ddr_data_fallback=False, pl_ddr=dict(capacity_bytes=0x80000000),
                       address_map=dict(a53_window_base='0x400000000',
                                        a53_window_bytes='0x80000000', mig_local_bytes='0x80000000',
                                        hls_system_base='0x400000000', hls_address_kind='shared_system_address'))
        for name, offset in (('weight', 0x100000), ('hidden', 0x104a8000),
                             ('history', 0x104a8700), ('logits', 0x104ad140)):
            profile['address_map'][name + '_local'] = hex(offset)
            profile['address_map'][name + '_a53'] = hex(0x400000000 + offset)
            profile['address_map'][name + '_hls'] = hex(0x400000000 + offset)
        root = M / 'build/address_contract'
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as directory:
            p = Path(directory)

            def write(value):
                f = p / 'RUN_PROFILE.json'
                f.write_text(json.dumps(value), encoding='utf-8')
                (p / 'ARTIFACTS.sha256').write_text(
                    hashlib.sha256(f.read_bytes()).hexdigest() + '  RUN_PROFILE.json\n', encoding='utf-8')

            write(profile)
            self.assertEqual(load_profile(p)['build_config'], 0x30c08011)
            cases = [('ps_ddr_data_fallback', True), ('data_memory', 'PS_DDR'),
                     ('format', 'M14_BOARD_RUN_PROFILE_V1'), ('capabilities', '0x182')]
            for field, value in cases:
                with self.subTest(field=field):
                    bad = copy.deepcopy(profile)
                    bad[field] = value
                    write(bad)
                    with self.assertRaises(ValueError): load_profile(p)
            for field, value in (('hidden_a53', '0x40104a8000'),
                                 ('weight_local', '0x7fffffc0'), ('logits_local', '0x104a8000')):
                with self.subTest(field=field):
                    bad = copy.deepcopy(profile)
                    bad['address_map'][field] = value
                    write(bad)
                    with self.assertRaises(ValueError): load_profile(p)
            write(profile)
            (p / 'RUN_PROFILE.json').write_text('{}', encoding='utf-8')
            with self.assertRaises(ValueError): load_profile(p)


if __name__ == '__main__': unittest.main(verbosity=2)
