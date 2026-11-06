"""Create an isolated candidate; never edits the accepted production sources."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
MODULE = HERE.parents[1]
CANDIDATE = HERE / "reduce_layers"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    if CANDIDATE.exists():
        raise SystemExit("Candidate exists; preserve it and choose a new candidate name.")
    original = (MODULE / "src/lm_head_v2.cpp").read_text(encoding="utf-8")
    start = original.index("float reduce_partials(")
    end = original.index("// One FIFO word carries", start)
    old = original[start:end]
    new = old.replace(
        "#pragma HLS INLINE off\n",
        "#pragma HLS INLINE off\n"
        "    // Each level has a distinct destination: no in-place indexed writeback.\n"
        "    // Preserve the original slot pairing and every FP32 rounding boundary.\n"
        "    float level8[LMH_V2_H_LANES][8];\n"
        "    float level4[LMH_V2_H_LANES][4];\n"
        "    float level2[LMH_V2_H_LANES][2];\n"
        "#pragma HLS ARRAY_PARTITION variable=level8 complete dim=0\n"
        "#pragma HLS ARRAY_PARTITION variable=level4 complete dim=0\n"
        "#pragma HLS ARRAY_PARTITION variable=level2 complete dim=0\n", 1)
    replacements = {
        "partial[lane][index] =\n                partial[lane][index] + partial[lane][index + 8];":
        "level8[lane][index] =\n                partial[lane][index] + partial[lane][index + 8];",
        "partial[lane][index] =\n                partial[lane][index] + partial[lane][index + 4];":
        "level4[lane][index] =\n                level8[lane][index] + level8[lane][index + 4];",
        "partial[lane][index] =\n                partial[lane][index] + partial[lane][index + 2];":
        "level2[lane][index] =\n                level4[lane][index] + level4[lane][index + 2];",
        "partial[lane][0] = partial[lane][0] + partial[lane][1];":
        "partial[lane][0] = level2[lane][0] + level2[lane][1];",
    }
    for before, after in replacements.items():
        assert new.count(before) == 1, before
        new = new.replace(before, after)
    final_start = new.index("reduce_2_to_1:")
    final_end = new.index("    const float sum01", final_start)
    new = new[:final_start] + (
        "    float lane_sum[LMH_V2_H_LANES];\n"
        "#pragma HLS ARRAY_PARTITION variable=lane_sum complete dim=1\n"
        "reduce_2_to_1:\n"
        "    for (int lane = 0; lane < LMH_V2_H_LANES; ++lane) {\n"
        "#pragma HLS UNROLL\n"
        "        lane_sum[lane] = level2[lane][0] + level2[lane][1];\n"
        "    }\n\n") + new[final_end:]
    new = new.replace("float partial[LMH_V2_H_LANES][LMH_V2_ACC_INTERLEAVE])",
                      "const float partial[LMH_V2_H_LANES][LMH_V2_ACC_INTERLEAVE])", 1)
    candidate_source = original[:start] + new + original[end:]
    (CANDIDATE / "src").mkdir(parents=True)
    (CANDIDATE / "include").mkdir()
    (CANDIDATE / "tests").mkdir()
    (CANDIDATE / "src/lm_head_v2.cpp").write_text(candidate_source, encoding="utf-8")
    header = (MODULE / "include/lm_head_v2.hpp").read_text(encoding="utf-8")
    (CANDIDATE / "include/lm_head_v2.hpp").write_text(header, encoding="utf-8")
    # For native/RTL regression, cover all 112 hidden words and all 16 slots,
    # while retaining a small vocabulary. Existing TEST_SMALL covers only 4 words.
    test_header = header.replace(
        "#ifdef LMH_V2_TEST_SMALL",
        "#if defined(LMH_V2_TEST_FULL_HIDDEN)\n"
        "#define LMH_V2_MAX_HIDDEN_SIZE 896\n"
        "#define LMH_V2_MAX_VOCAB_SIZE 64\n"
        "#elif defined(LMH_V2_TEST_SMALL)", 1)
    (CANDIDATE / "tests/lm_head_v2.hpp").write_text(test_header, encoding="utf-8")
    reducer_harness = (
        "// Extracted verbatim from the two actual kernel sources.\n"
        "static const unsigned int LMH_V2_H_LANES = 8;\n"
        "static const unsigned int LMH_V2_ACC_INTERLEAVE = 16;\n"
        "namespace baseline {\n" + old + "}\n"
        "namespace candidate {\n" + new + "}\n")
    (CANDIDATE / "tests/reducers.inc").write_text(reducer_harness, encoding="utf-8")
    paths = [MODULE / "src/lm_head_v2.cpp", MODULE / "include/lm_head_v2.hpp",
             CANDIDATE / "src/lm_head_v2.cpp", CANDIDATE / "include/lm_head_v2.hpp",
             CANDIDATE / "tests/lm_head_v2.hpp", CANDIDATE / "tests/reducers.inc"]
    manifest = {"candidate": "reduce_layers", "changes": "separate interleave reduction layer arrays",
                "production_modified": False, "board_usable": False,
                "build_identity": "unchanged 100 MHz identity; diagnostic only",
                "files": {str(p.relative_to(MODULE)).replace("\\", "/"): sha(p.read_bytes())
                          for p in paths}}
    (CANDIDATE / "source_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
