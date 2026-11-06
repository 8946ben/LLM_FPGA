from pathlib import Path
import hashlib,tarfile
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'module_14_lm_head_v4/reports/partial_rtl_20261024_r1/full_r3/observations/20261025_r3'
p=ROOT/'module_14_lm_head_v4/reports/partial_rtl_20261024_r1/full_rtl_observation_20261025_r3.tar.gz'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='778aea07c56abb5ff622352627b63691061dc8a760d9496b7f473f8cca0d7820'
with tarfile.open(p) as tar:
    for m in tar.getmembers():
        q=(ROOT/m.name).resolve();assert R in q.parents and m.isfile()
        if q.exists():assert q.read_bytes()==tar.extractfile(m).read(),m.name
    tar.extractall(ROOT,filter='data')
print('THIRD_OBSERVATION_SHA_PATH_CONTENT_PASS')
