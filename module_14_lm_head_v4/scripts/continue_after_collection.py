"""Local sequential P2 workflow, not an automation or remote task.

Stops on STOP_REQUESTED. Consumes only completed, hash-checked collection
manifests. CPU selector work may run while the GPU collects untouched holdout.
"""
from pathlib import Path
from datetime import datetime,timezone
import json,os,subprocess,sys,time
M=Path(__file__).resolve().parents[1];DATA=M/'data/hidden_v1';R=M/'reports';OUT=R/'selector_p2_20261021'
def wait_for(split):
    p=DATA/split/'MANIFEST.json'
    while not p.exists():
        if (DATA/'STOP_REQUESTED').exists():return False
        time.sleep(20)
    if (DATA/'STOP_REQUESTED').exists():return False
    return json.loads(p.read_text(encoding='utf-8'))['state']=='PASS'
def command(log,*args):
    env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='4',OMP_NUM_THREADS='4',MKL_NUM_THREADS='4',PYTHONIOENCODING='utf-8')
    with (R/log).open('w',encoding='utf-8') as f:
        r=subprocess.run([sys.executable,'-u',str(M/'scripts/evaluate_selectors.py'),*args],stdout=f,stderr=subprocess.STDOUT,env=env)
    if r.returncode:raise RuntimeError('Selector phase failed: '+log)
def main():
    if not wait_for('train') or not wait_for('calibration'):print('P2_WORKFLOW=PAUSED',flush=True);return
    if not (OUT/'CALIBRATION.json').exists():
        print('P2_CALIBRATION_BEGIN',flush=True);command('selector_calibration.log')
    else:print('P2_CALIBRATION_REUSE_COMPLETED',flush=True)
    result=json.loads((OUT/'CALIBRATION.json').read_text(encoding='utf-8'))
    print('P2_CALIBRATION_END '+result['quality_state'],flush=True)
    if result['chosen_calibration_configuration']:
        if not wait_for('holdout'):print('P2_WORKFLOW=PAUSED_BEFORE_HOLDOUT',flush=True);return
        if not (OUT/'HOLDOUT.json').exists():command('selector_holdout.log','--holdout-only')
        else:print('P2_HOLDOUT_REUSE_COMPLETED',flush=True)
    print('P2_WORKFLOW=COMPLETE',flush=True)
if __name__=='__main__':main()
