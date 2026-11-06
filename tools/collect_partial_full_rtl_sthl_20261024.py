from pathlib import Path
import datetime,hashlib,json,tarfile
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1');R=ROOT/'module_14_lm_head_v4/reports/partial_rtl_20261024_r1';F=R/'full_r3';SOL=ROOT/'.cache/p64_rtl_full_r3/hls/solution1'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def main():
    state=json.loads((F/'FULL_WORKFLOW.json').read_text());assert state['state']!='EXECUTING','Still running: do not collect as completed'
    groups=[]
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():continue
        try:
            s=(proc/'stat').read_text();rest=s[s.rindex(')')+2:].split()
            if rest[0]!='Z' and int(rest[2])==state['child_pgid']:groups.append(proc.name)
        except (OSError,ValueError):pass
    assert not groups and not (F/'ACTIVE.lock').exists()
    plan=json.loads((F/'PLAN.json').read_text())
    for n,h in plan['source_sha256'].items():
        if n==plan['only_path_rebind']['path']:h=plan['only_path_rebind']['remote_sha256']
        assert sha(ROOT/n)==h,n
    evidence=F/'tool_artifacts';evidence.mkdir(exist_ok=True);inventory=[]
    for p in (SOL/'sim').rglob('*'):
        if not p.is_file():continue
        size=p.stat().st_size;rel=p.relative_to(SOL)
        record=dict(path=str(rel),bytes=size)
        # Keep large binary weight TV on server, retain identity and small returned workspaces.
        keep=(size<16*1024*1024 and (p.suffix in ['.rpt','.xml','.json','.csv','.log','.tcl'] or 'workspace' in p.name or 'status' in p.name or 'result' in p.name))
        if keep:
            q=evidence/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());record['sha256']=sha(p);record['collected']=str(q.relative_to(F))
        inventory.append(record)
    (F/'TOOL_ARTIFACT_INVENTORY.json').write_text(json.dumps(inventory,indent=2)+'\n')
    after=dict(state='PASS_FULL_JOB_STOPPED_SOURCE_SHA_UNCHANGED',time=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_files=len(plan['source_sha256']),owned_process_group_members=groups,active_locks=0,workflow_state=state['state'],automatic_next_stage=False)
    (F/'PROCESS_AFTER.json').write_text(json.dumps(after,indent=2)+'\n')
    archive=ROOT/'full_rtl_results.tar.gz'
    with tarfile.open(archive,'w:gz') as tar:
        for folder in [R/'full_r1',R/'full_r2',R/'full_r3']:
            for p in folder.rglob('*'):
                if p.is_file() and p.suffix!='.gz':tar.add(p,arcname=str(p.relative_to(ROOT)))
    print(json.dumps(dict(state=after['state'],workflow=state['state'],archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive))))
if __name__=='__main__':main()
