"""Bind already executed selected-layout/mock tests; no target or new tests."""
from pathlib import Path
import hashlib,json,re
M=Path(__file__).resolve().parents[1];X=M/'experiments/fusion_exp10_20261023';R=M/'reports/fusion_exp10_20261023_r1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    host=X/'reports/control_host_20261023_r1';logs={};total=0
    for p,n in [(X/'reports/arena_loader_20261022/host_r2/transport.log',13),(host/'mailbox.log',8),(host/'layout.log',3),(host/'orchestration_r2.log',13)]:
        text=p.read_text(encoding='utf-8-sig');assert f'Ran {n} tests' in text and re.search(r'^OK\s*$',text,re.M) and 'skipped=' not in text;total+=n;logs[p.relative_to(X).as_posix()]=sha(p)
    assert 'SELECTOR_CONTROL_HOST_TEST=PASS cases=25 fake_MMIO_only' in (host/'control.log').read_text();loader=X/'reports/arena_loader_20261022/host_r2/RESULT.json';assert read(loader)['state']=='PASS_HOST_ONLY_NO_BSP_ELF_BOARD'
    for n,h in read(loader)['source_sha256'].items():assert sha(X/n)==h,n
    assert '88 alignment/length combinations' in (loader.parent/'core.log').read_text()
    files={}
    for folder in ['standalone','reference','tests']:
        for p in (X/folder).rglob('*'):
            if p.is_file() and p.suffix in ['.c','.h','.py','.tcl','.ld']:files[p.relative_to(X).as_posix()]=sha(p)
    # A synthetic producer/parser pair could agree on a stale identity; bind all
    # actual language surfaces to the selected private hardware identity too.
    for name in ['standalone/selector_control.c','standalone/arena_loader/arena_layout.h','standalone/selector_ps_mailbox.py','standalone/scripts/private_board_common.tcl']:
        assert '0x4d345a0a' in (X/name).read_text().lower(),name
    assert not any('0x4d345301' in (X/n).read_text().lower() for n in files if n.startswith('standalone/'))
    report=dict(state='PASS_OFFLINE_HOST_LAYOUT_IDENTITY_AND_MOCK_CONTROL',python_tests=total,fake_mmio_cases=25,loader_copy_alignment_length_combinations=88,source_sha256=files,log_sha256=logs,loader_result_sha256=sha(loader),network_access='NONE',board='NOT_RUN',scope='C protocol and fake-MMIO, local320MiB images, Python/Tcl mocks. Not lwIP/GEM DMA, physical DDR, target shutdown or FPGA timing.')
    (R/'HOST_QUALIFICATION.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(report['state'],total)
if __name__=='__main__':main()
