"""Unpack exact owned entry without overwrites, launch finite qualification."""
from pathlib import Path
import hashlib,json,subprocess,tarfile
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
archive=ROOT/'d64_resource_entry_20261102.tar.gz'
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='3d4578b651c2128bd610e0975e2b72788cdd00cc8875d47a6d594abae71e03f4'
R=ROOT/'module_14_lm_head_v4/reports/d64_resource_recovery_20261102_r1'
assert not (R/'WORKFLOW.json').exists() and not (R/'launcher.log').exists()
with tarfile.open(archive) as tar:
    for member in tar.getmembers():
        p=(ROOT/member.name).resolve()
        assert ROOT in p.parents and member.isfile()
        data=tar.extractfile(member).read()
        if p.exists():assert p.read_bytes()==data,str(p)
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
entry=ROOT/'module_14_lm_head_v4/experiments/d64_resource_recovery_20261102/run_qualification.py'
with (R/'launcher.log').open('w') as out:
    p=subprocess.Popen(['/home/zhangben/anaconda3/bin/python',str(entry)],cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
print(json.dumps({'finite_qualification_parent_pid':p.pid,'workflow':str(R/'WORKFLOW.json'),'automatic_next_stage':False}))
