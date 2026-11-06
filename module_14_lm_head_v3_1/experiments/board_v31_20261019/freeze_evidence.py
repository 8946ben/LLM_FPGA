"""Bind accepted measurements, their original raw runs and exact source files."""
from pathlib import Path
import hashlib, json, shutil

m=Path(__file__).resolve().parents[2]
root=m.parent
out=m/'reports/board200_20261019'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    comparison=json.loads((out/'comparison.json').read_text(encoding='utf-8'))
    assert comparison['state']=='PASS'
    evidence=set()
    for name in ('baseline_campaign','candidate_campaign'):
        path=Path(comparison[name])
        campaign=json.loads(path.read_text(encoding='utf-8-sig'))
        assert campaign['state']=='PASS'
        evidence.update(p for p in path.parent.rglob('*') if p.is_file())
        for record in campaign['records']:
            evidence.update(p for p in Path(record['source_run']).rglob('*') if p.is_file())
    for name in ('baseline_upload','candidate_upload'):
        evidence.update(p for p in Path(comparison[name]).rglob('*') if p.is_file())
    launch=m/'build/board200_20261019/launch'
    build=m/'build/board200_20261019'
    logs=out/'build_logs'
    logs.mkdir(exist_ok=True)
    for p in launch.iterdir():
        if p.is_file() and p.suffix in ('.log','.jou','.json'): shutil.copy2(p,logs/p.name)
    for name in ('export.log','export_revision_recovery.log','software_build.log','platform.log'):
        p=build/name
        if p.exists(): shutil.copy2(p,logs/name)
    for name in ('m14_v2_test.map','m14_tcp_loader.map'):
        shutil.copy2(build/'software'/name,logs/name)
    rtl=m/'board/build/m14_board200_20261019/m14_board200_20261019.runs/impl_1'
    shutil.copy2(rtl/'m14_200_system_wrapper_methodology_drc_routed.rpt',out/'hardware/methodology.rpt')
    host=build/'host_validation/result.json'
    shutil.copy2(host,out/'host_regression.json')
    sources={p for p in Path(__file__).parent.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    for name in ('board_profile.py','parse_mailbox.py','program_board_tcp.ps1','run_step.ps1',
                 'run_negative.ps1','run_failure_regression.ps1','run_acceptance.ps1'):
        sources.add(m/'standalone'/name)
    sources.update({m/'scripts/summarize_acceptance.py',m/'standalone/src/main.c',m/'standalone/src/lscript.ld',root/'ref/xemacpsif_physpeed.c'})
    def write_manifest(path,files,base):
        entries=sorted((p.resolve() for p in files),key=lambda p:p.relative_to(base).as_posix())
        path.write_text(''.join(sha(p)+'  '+p.relative_to(base).as_posix()+'\n' for p in entries),encoding='utf-8')
    write_manifest(out/'EVIDENCE_SHA256SUMS',evidence,root)
    write_manifest(out/'SOURCE_SHA256SUMS',sources,root)
    write_manifest(out/'SHA256SUMS',[p for p in out.rglob('*') if p.is_file() and p!=out/'SHA256SUMS'],out)
    checked=0
    for manifest,base in ((out/'EVIDENCE_SHA256SUMS',root),(out/'SOURCE_SHA256SUMS',root),(out/'SHA256SUMS',out)):
        for line in manifest.read_text(encoding='utf-8').splitlines():
            digest,name=line.split('  ',1)
            assert sha(base/name)==digest,name
            checked+=1
    print('M14_BOARD200_EVIDENCE_FREEZE=PASS files='+str(checked))

if __name__=='__main__': main()
