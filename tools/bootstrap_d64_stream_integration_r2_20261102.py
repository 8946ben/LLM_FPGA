"""Unpack exact owned entry without overwrites, launch finite qualification."""
from pathlib import Path
import hashlib,json,subprocess,tarfile
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
archive=ROOT/'d64_integration_entry_20261102_r2.tar.gz'
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='f369b9a6a004d91ab613f5fef5eb02b144691b5f844461ef72bf08020f719fa7'
R=ROOT/'module_14_lm_head_v4/reports/d64_stream_integration_20261102_r2'
assert not (R/'WORKFLOW.json').exists() and not (R/'launcher.log').exists()
with tarfile.open(archive) as tar:
    for member in tar.getmembers():
        p=(ROOT/member.name).resolve()
        assert ROOT in p.parents and member.isfile()
        data=tar.extractfile(member).read()
        if p.exists():assert p.read_bytes()==data,str(p)
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
entry=ROOT/'module_14_lm_head_v4/experiments/d64_stream_integration_20261102_r2/run_qualification.py'
with (R/'launcher.log').open('w') as out:
    p=subprocess.Popen(['/home/zhangben/anaconda3/bin/python',str(entry)],cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
print(json.dumps({'finite_qualification_parent_pid':p.pid,'workflow':str(R/'WORKFLOW.json'),'automatic_next_stage':False}))
