"""Static consistency checks that do not replace a Vitis HLS compilation."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def argument_names(argument_text: str) -> list[str]:
    names: list[str] = []
    for argument in argument_text.split(","):
        match = re.search(r"(\w+)\s*$", argument.strip())
        if match is None:
            raise ValueError(f"cannot parse argument: {argument!r}")
        names.append(match.group(1))
    return names


def main() -> int:
    header = (ROOT / "include" / "lm_head_v2.hpp").read_text(encoding="utf-8")
    source = (ROOT / "src" / "lm_head_v2.cpp").read_text(encoding="utf-8")
    pattern = r'extern\s+"C"\s+void\s+lm_head_v2\s*\((.*?)\)\s*[;{]'
    header_matches = re.findall(pattern, header, flags=re.DOTALL)
    source_matches = re.findall(pattern, source, flags=re.DOTALL)
    if len(header_matches) != 1 or len(source_matches) != 1:
        raise AssertionError("lm_head_v2 declaration/definition count mismatch")
    header_names = argument_names(header_matches[0])
    source_names = argument_names(source_matches[0])
    if header_names != source_names:
        raise AssertionError((header_names, source_names))

    axilite_ports = set(
        re.findall(r"#pragma\s+HLS\s+INTERFACE\s+s_axilite\s+port=(\w+)", source)
    )
    expected_ports = set(source_names) | {"return"}
    if axilite_ports != expected_ports:
        raise AssertionError(
            {
                "missing_axilite": sorted(expected_ports - axilite_ports),
                "extra_axilite": sorted(axilite_ports - expected_ports),
            }
        )

    required_fragments = (
        "typedef ap_uint<256> accumulator_slice_t",
        "#pragma HLS DATAFLOW",
        "#pragma HLS PIPELINE II=1",
        "bundle=hidden",
        "bundle=weight",
        "bundle=history",
        "bundle=logits",
        "max_read_burst_length=16",
        "num_read_outstanding=16",
    )
    missing = [fragment for fragment in required_fragments if fragment not in source]
    if missing:
        raise AssertionError({"missing_source_fragments": missing})

    for script_name in (
        "run_csim.tcl",
        "run_csynth.tcl",
        "run_cosim.tcl",
        "run_export_ip.tcl",
    ):
        script = (ROOT / "scripts" / script_name).read_text(encoding="utf-8")
        if "config_interface -m_axi_addr64" not in script:
            raise AssertionError({"missing_m_axi_addr64": script_name})
    print(
        f"SOURCE_CONTRACT=PASS arguments={len(source_names)} "
        f"axilite_ports={len(axilite_ports)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
