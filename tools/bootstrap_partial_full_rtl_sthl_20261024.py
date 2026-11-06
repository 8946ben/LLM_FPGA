from pathlib import Path
import json,subprocess,tarfile
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
with tarfile.open(ROOT/'full_rtl_entry.tar.gz') as tar:
    for m in tar.getmembers():
        p=(ROOT/m.name).resolve();assert ROOT in p.parents and m.isfile()
        if p.exists():assert p.read_bytes()==tar.extractfile(m).read()
    tar.extractall(ROOT)
R=ROOT/'module_14_lm_head_v4/reports/partial_rtl_20261024_r1/full_r1'
assert not (R/'FULL_WORKFLOW.json').exists()
assert json.loads((R.parent/'r4/INDEPENDENT_REVIEW.json').read_text())['state']=='PASS_SELECTOR_RTL_FULL_ARRAYS_AND_AXI_STALLS'
p=subprocess.Popen(['/home/zhangben/anaconda3/bin/python',str(ROOT/'module_14_lm_head_v4/experiments/partial_rtl_20261024/run_full.py')],cwd=str(ROOT),stdout=(R/'launcher.log').open('w'),stderr=subprocess.STDOUT,start_new_session=True)
print(json.dumps(dict(parent_pid=p.pid,automatic_next_stage=False)))
