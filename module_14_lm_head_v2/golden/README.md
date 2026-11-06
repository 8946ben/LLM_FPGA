# M14 V2 golden

`v2_trace_manifest.json` records the hashes and expected outputs for the eight
real trace steps. Large BF16 weights and FP32 vectors stay under
`artifacts/module14_v2_assets/`, which is intentionally ignored by Git.

The assets are generated from the original BF16 tensor
`model.embed_tokens.weight` in `model.safetensors`. The legacy FP16 NPY is not
the authoritative V2 weight because converting it back to BF16 cannot recover
the original bits.

The current hidden vectors are RNE BF16 conversions of the legacy FP16 trace.
They validate M14 in isolation. Once M06 V2 is integrated, record another
end-to-end golden set from its actual BF16 final-RMS output.

Regenerate with `scripts/generate_assets.ps1`. Hardware validation must first
verify the weight SHA256 from the manifest, then compare raw FP32 logits,
processed scores, selected token, selected score bits, and output CRC.

As of 2026-10-09, the numeric implementation is
`bf16_rne_h8_interleave16_fp32_adjacent_tree_v2`. The final lane tree now matches
the existing C++/RTL adjacent-pair order; no numerical tolerance was introduced.
The old golden is retained under `reports/numeric_20261009/legacy_golden/`.
Use `scripts/regenerate_golden.py` for this audited migration without exporting
or rewriting the original weight, hidden or history assets. See `NUMERIC_CONTRACT.md`.
