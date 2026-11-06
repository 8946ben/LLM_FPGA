from pathlib import Path
import subprocess,tarfile,json
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
with tarfile.open(ROOT/'selector_r3_entry.tar.gz') as tar:
    for m in tar.getmembers():
        p=(ROOT/m.name).resolve();assert ROOT in p.parents and m.isfile()
        if p.exists():assert p.read_bytes()==tar.extractfile(m).read()
    tar.extractall(ROOT)
R=ROOT/'module_14_lm_head_v4/reports/partial_rtl_20261024_r1/r3'
assert not (R/'SELECTOR_WORKFLOW.json').exists()
p=subprocess.Popen(['/home/zhangben/anaconda3/bin/python',str(ROOT/'module_14_lm_head_v4/experiments/partial_rtl_20261024/r3/run_selector.py')],cwd=str(ROOT),stdout=(R/'launcher.log').open('w'),stderr=subprocess.STDOUT,start_new_session=True)
print(json.dumps(dict(parent_pid=p.pid,automatic_next_stage=False)))
