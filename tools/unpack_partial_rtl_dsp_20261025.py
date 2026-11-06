from pathlib import Path
import hashlib,tarfile
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'module_14_lm_head_v4/reports/partial_rtl_20261024_r1/full_r3/diagnostics/20261025_dsp_r1'
p=ROOT/'module_14_lm_head_v4/reports/partial_rtl_20261024_r1/full_rtl_dsp_diagnostic_20261025_r1.tar.gz'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='7177a77241eb279559147be8a33a94e1deb3b34c3c38ff15a233cd16cda256a7'
with tarfile.open(p) as tar:
    for m in tar.getmembers():
        q=(ROOT/m.name).resolve();assert R in q.parents and m.isfile()
        if q.exists():assert q.read_bytes()==tar.extractfile(m).read(),m.name
    tar.extractall(ROOT,filter='data')
print('DSP_DIAGNOSTIC_SHA_PATH_CONTENT_PASS')
