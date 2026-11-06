"""Bind native results to the unchanged baseline and the exact candidate code."""
from pathlib import Path
import difflib
import hashlib
import json

HERE = Path(__file__).resolve().parent
MODULE = HERE.parents[2]
REPORT = MODULE / "reports/frequency_200_20261016/reduce_layers"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reducer(text):
    return text[text.index("float reduce_partials("):text.index("// One FIFO word carries")]


def main():
    manifest = json.loads((HERE / "source_manifest.json").read_text(encoding="utf-8"))
    for relative, expected in manifest["files"].items():
        assert sha(MODULE / relative) == expected, "Changed source: " + relative
    baseline = (MODULE / "src/lm_head_v2.cpp").read_text(encoding="utf-8")
    candidate = (HERE / "src/lm_head_v2.cpp").read_text(encoding="utf-8")
    assert baseline.replace(reducer(baseline), "<REDUCER>") == \
        candidate.replace(reducer(candidate), "<REDUCER>"), "Changes outside reducer"
    extracted = (HERE / "tests/reducers.inc").read_text(encoding="utf-8")
    assert "namespace baseline {\n" + reducer(baseline) + "}\n" in extracted
    assert "namespace candidate {\n" + reducer(candidate) + "}\n" in extracted
    assert (MODULE / "include/lm_head_v2.hpp").read_text(encoding="utf-8") == \
        (HERE / "include/lm_head_v2.hpp").read_text(encoding="utf-8")
    fixture = HERE / 'tests/kernel_full_hidden.cpp'
    if fixture.exists():
        text = fixture.read_text(encoding='utf-8')
        start = text.index('#if defined(LMH_V2_TEST_FULL_HIDDEN)')
        end = text.index('#elif defined(LMH_V2_TEST_SMALL)', start)
        restored = text[:start] + '#ifdef LMH_V2_TEST_SMALL' + text[end+len('#elif defined(LMH_V2_TEST_SMALL)'):]
        assert restored == candidate, 'Full-hidden test changed arithmetic/source outside interface depths'
        identity = json.loads((HERE / 'tests/full_hidden_copy_identity.json').read_text(encoding='utf-8'))
        assert sha(fixture) == identity['test_copy_sha256']
        assert sha(HERE / 'src/lm_head_v2.cpp') == identity['source_sha256']
        retry = HERE / 'tests/rtl/lm_head_v2.cpp'
        if retry.exists(): assert retry.read_bytes() == fixture.read_bytes()
    REPORT.mkdir(parents=True, exist_ok=True)
    diff = "".join(difflib.unified_diff(baseline.splitlines(True), candidate.splitlines(True),
                                     fromfile="accepted_100MHz/src/lm_head_v2.cpp",
                                     tofile="reduce_layers/src/lm_head_v2.cpp"))
    (REPORT / "source.diff").write_text(diff, encoding="utf-8")
    sources = [p for p in HERE.rglob("*") if p.is_file() and p.suffix in
               (".cpp", ".hpp", ".inc", ".ps1", ".tcl", ".py")]
    sources += [MODULE / "src/lm_head_v2.cpp", MODULE / "include/lm_head_v2.hpp"]
    identity = {"status": "PASS", "only_reducer_changed": True,
                "production_unchanged": True,
                "files": {str(p.relative_to(MODULE)).replace("\\", "/"): sha(p)
                          for p in sorted(sources)}}
    (REPORT / "tested_sources.json").write_text(json.dumps(identity, indent=2) + "\n", encoding="utf-8")
    print("CANDIDATE_SOURCE_IDENTITY_PASS files=" + str(len(sources)))


if __name__ == "__main__":
    main()
