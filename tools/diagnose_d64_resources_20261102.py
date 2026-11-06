"""Read-only, bounded STHL snapshot; emits JSON to stdout, never starts EDA."""
from pathlib import Path
import datetime, hashlib, json, os, subprocess

ROOT = Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1')
R = ROOT/'module_14_lm_head_v4/reports/full_bank_cosim_20261026_r1'
V = ROOT/'.cache/p64_full_bank_cosim_20261026_r1/sim/verilog'

def info(p, tail=0):
    if not p.exists(): return {'exists': False}
    s=p.stat(); out={'exists': True, 'bytes': s.st_size, 'mtime_ns': s.st_mtime_ns}
    if tail:
        with p.open('rb') as f:
            f.seek(max(0,s.st_size-tail)); out['tail']=f.read(tail).decode(errors='replace')
    return out

out={'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
     'host':os.uname().nodename,'uid':os.getuid(),'workflow':json.loads((R/'FULL_WORKFLOW.json').read_text()),
     'stop_request':info(R/'STOP_REQUESTED',1024),'active_lock':info(R/'ACTIVE.lock',1024),
     'meminfo':Path('/proc/meminfo').read_text(), 'files':{},'processes':[]}
for p in [R/'launcher.log',R/'xsim.log',V/'full_bank.tcl',V/'run_xsim.sh']:
    out['files'][str(p.relative_to(ROOT))]=info(p,12000)
for p in Path('/proc').iterdir():
    if not p.name.isdigit():continue
    try:
        cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
        if str(ROOT) in cmd or ('xsim' in cmd and cmd.strip()):
            out['processes'].append({'pid':int(p.name),'cmd':cmd[:3000],'stat':(p/'stat').read_text()})
    except OSError: pass
large=[]
for p in V.rglob('*'):
    if p.is_file():
        s=p.stat()
        if s.st_size>=1048576:large.append({'path':str(p.relative_to(V)),'bytes':s.st_size})
out['largest_cache_files']=sorted(large,key=lambda x:x['bytes'],reverse=True)[:30]
for name in ['run_full.py']:
    p=ROOT/'module_14_lm_head_v4/experiments/full_bank_cosim_20261026'/name
    out[name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
out['journal_user']=subprocess.run(['journalctl','--user','--since','2026-10-27 06:00:00','--until','2026-10-27 06:20:00','--no-pager','-n','30'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,universal_newlines=True,timeout=20).stdout
print(json.dumps(out,ensure_ascii=False,indent=2))
