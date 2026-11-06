"""Cross-language address contract checks; these never access the FPGA."""
import ast
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1]
EXPERIMENT = MODULE / "experiments/board_v31_20261019"
HEADER = (MODULE / "standalone/src/pl_ddr_layout.h").read_text()
DEFINES = {name: int(value, 0) for name, value in re.findall(
    r"^#define\s+M14_V31_(\w+)\s+(0x[0-9a-fA-F]+|[0-9]+)[uUlL]*\s*$", HEADER, re.M)}


def expected():
    return {name.lower(): DEFINES["PL_DDR_A53_BASE"] + DEFINES[name + "_OFFSET"]
            for name in ("WEIGHT", "HIDDEN", "HISTORY", "LOGITS")}


class AddressContract(unittest.TestCase):
    def test_generated_mailbox_addresses_and_ranges(self):
        # Validate actual serialized bytes passed to A53, rather than only a dict.
        temp_root = MODULE / "build/address_contract"
        temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as tmp:
            output = Path(tmp) / "mailbox.bin"
            result = subprocess.run([sys.executable, str(MODULE / "standalone/prepare_mailbox.py"),
                                     str(output), "--expected-token", "0"], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
            data = output.read_bytes()
        self.assertEqual(len(data), 256)
        base = DEFINES["PL_DDR_A53_BASE"]
        limit = base + DEFINES["PL_DDR_A53_BYTES"]
        # Mailbox ABI defines hidden/weight/history/logits at byte offsets 16..47.
        addresses = dict(zip(("hidden", "weight", "history", "logits"),
                             struct.unpack_from("<4Q", data, 16)))
        self.assertEqual(addresses, expected())
        regions = []
        for name, address in addresses.items():
            end = address + DEFINES[name.upper() + "_BYTES"]
            self.assertGreaterEqual(address, base)
            self.assertLessEqual(end, limit)
            regions.append((address, end))
        regions.sort()
        self.assertTrue(all(a[1] <= b[0] for a, b in zip(regions, regions[1:])))

    def test_jtag_io_addresses(self):
        text = (MODULE / "standalone/scripts/run_step.tcl").read_text()
        for name in ("hidden", "history"):
            value = re.search(r"dow -data \$" + name + r"_file\s+(0x[0-9a-fA-F]+)", text)
            self.assertEqual(int(value[1], 16), expected()[name])
        value = re.search(r"-size w\s+(0x[0-9a-fA-F]+)\s+151936", text)
        self.assertEqual(int(value[1], 16), expected()["logits"])
        probe = (MODULE / "standalone/scripts/probe_retained_state.tcl").read_text()
        last = int(re.search(r"WEIGHT_LAST\s+(0x[0-9a-fA-F]+)", probe)[1], 16)
        self.assertEqual(last, expected()["weight"] + DEFINES["WEIGHT_BYTES"] - 16)

    def test_package_map_and_platform_binding(self):
        tree = ast.parse((EXPERIMENT / "package.py").read_text())
        profile = next(n.value for n in tree.body if isinstance(n, ast.Assign)
                       and any(isinstance(t, ast.Name) and t.id == "profile" for t in n.targets))
        fields = {k.value: v for k, v in zip(profile.keys, profile.values)}
        address_map = ast.literal_eval(fields["address_map"])
        for name, address in expected().items():
            self.assertEqual(int(address_map[name + "_a53"], 16), address)
            self.assertEqual(int(address_map[name + "_hls"], 16), address)
            self.assertEqual(int(address_map[name + "_local"], 16),
                             address - DEFINES["PL_DDR_A53_BASE"])
        self.assertEqual(ast.literal_eval(fields["pl_ddr"])["reset_pin"], "AM5")
        platform = (EXPERIMENT / "platform.tcl").read_text()
        name = re.search(r"platform create -name\s+(\w+)", platform)[1]
        self.assertIn("workspace/" + name + "/hw/psu_init.tcl",
                      (EXPERIMENT / "package.py").read_text())
        self.assertIn("workspace\\" + name + "\\psu_cortexa53_0",
                      (EXPERIMENT / "build_software.ps1").read_text())


if __name__ == "__main__":
    unittest.main(verbosity=2)
