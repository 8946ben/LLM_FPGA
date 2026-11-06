from pathlib import Path
import hashlib,json,subprocess,tarfile
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
assert ROOT.is_dir()
archive=ROOT/'selector_entry.tar.gz'
with tarfile.open(archive) as tar:
    for m in tar.getmembers():
        dest=(ROOT/m.name).resolve()
        assert ROOT in dest.parents and m.isfile(),m.name
        if dest.exists():assert dest.read_bytes()==tar.extractfile(m).read(),m.name
    tar.extractall(ROOT)
source=ROOT/'prepare_partial_rtl_20261024.py';dest=ROOT/'tools'/source.name
dest.parent.mkdir(exist_ok=True)
if dest.exists():assert dest.read_bytes()==source.read_bytes()
else:dest.write_bytes(source.read_bytes())
R=ROOT/'module_14_lm_head_v4/reports/partial_rtl_20261024_r1'
assert not (R/'SELECTOR_WORKFLOW.json').exists() and not (R/'ACTIVE.lock').exists()
log=(R/'launcher.log').open('w')
p=subprocess.Popen(['/home/zhangben/anaconda3/bin/python',str(ROOT/'module_14_lm_head_v4/experiments/partial_rtl_20261024/run_selector.py')],cwd=str(ROOT),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
print(json.dumps(dict(parent_pid=p.pid,archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),automatic_next_stage=False)))
