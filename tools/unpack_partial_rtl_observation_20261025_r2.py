from pathlib import Path
import hashlib,tarfile
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'module_14_lm_head_v4/reports/partial_rtl_20261024_r1/full_r3/observations/20261025_r2'
p=ROOT/'module_14_lm_head_v4/reports/partial_rtl_20261024_r1/full_rtl_observation_20261025_r2.tar.gz'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='8921a1b82646f81dd2ba85160a4d72052599b2290fb6002ba1528dfde67c5898'
with tarfile.open(p) as tar:
    for m in tar.getmembers():
        q=(ROOT/m.name).resolve();assert R in q.parents and m.isfile()
        if q.exists():assert q.read_bytes()==tar.extractfile(m).read(),m.name
    tar.extractall(ROOT,filter='data')
print('SECOND_OBSERVATION_SHA_PATH_CONTENT_PASS')
