from pathlib import Path
import hashlib,tarfile
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'module_14_lm_head_v4/reports/partial_rtl_20261024_r1';p=R/'selector_rtl_results.tar.gz'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='f30e64933d7b98a8d76635a98cba758376ef8848d4a22e2ce4aa60af940adb7c'
with tarfile.open(p) as tar:
    for m in tar.getmembers():
        dest=(ROOT/m.name).resolve();assert R in dest.parents and m.isfile()
        if dest.exists():assert dest.read_bytes()==tar.extractfile(m).read(),m.name
    tar.extractall(ROOT,filter='data')
print('SELECTOR_ARCHIVE_SHA_PATH_CONTENT_PASS')
