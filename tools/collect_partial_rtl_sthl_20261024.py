from pathlib import Path
import argparse,datetime,hashlib,json,os,tarfile
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1');R=ROOT/'module_14_lm_head_v4/reports/partial_rtl_20261024_r1'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def collect_selector():
    workflow=json.loads((R/'r4/SELECTOR_WORKFLOW.json').read_text());assert workflow['state']=='SELECTOR_RTL_COMPLETE_AWAITING_REVIEW'
    members=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            s=(p/'stat').read_text();rest=s[s.rindex(')')+2:].split()
            if rest[0]!='Z' and int(rest[2])==workflow['child_pgid']:members.append(dict(pid=p.name,stat=s))
        except (OSError,ValueError):pass
    assert not members
    for folder in [R,R/'r2',R/'r3',R/'r4']:assert not (folder/'ACTIVE.lock').exists()
    plan=json.loads((R/'r4/PLAN.json').read_text());prefix='module_14_lm_head_v4/reports/partial_hw_20261024_r1/r3/remote_hls/syn/verilog/'
    for n,h in plan['source_sha256'].items():
        p=ROOT/'.cache/p64_r3/csynth/hls/solution1/syn/verilog'/n[len(prefix):] if n.startswith(prefix) else ROOT/n
        assert sha(p)==h,n
    after=dict(state='PASS_SELECTOR_STOPPED_SOURCE_SHA_UNCHANGED',time=datetime.datetime.now(datetime.timezone.utc).isoformat(),owned_process_group_members=members,source_files=len(plan['source_sha256']),active_locks=0,automatic_next_stage=False)
    (R/'r4/PROCESS_AFTER.json').write_text(json.dumps(after,indent=2)+'\n')
    out=ROOT/'selector_rtl_results.tar.gz'
    with tarfile.open(out,'w:gz') as tar:
        for p in R.rglob('*'):
            if p.is_file() and p.suffix!='.gz' and 'full_r1' not in p.parts:tar.add(p,arcname=str(p.relative_to(ROOT)))
    print(json.dumps(dict(state=after['state'],archive=str(out),bytes=out.stat().st_size,sha256=sha(out))))
if __name__=='__main__':collect_selector()
