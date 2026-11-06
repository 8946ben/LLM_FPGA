"""Freeze real HLS/host evidence without using tool exit as a numeric verdict."""
from pathlib import Path
import hashlib,json,re,xml.etree.ElementTree as ET
M=Path(__file__).resolve().parents[1];X=M/'experiments/fusion_exp10_20261023';R=M/'reports/fusion_exp10_20261023_r1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    frozen=read(X/'MANIFEST.json')
    for section,base in [('source_sha256',X),('fixture_sha256',X/'fixture')]:
        for name,h in frozen[section].items():assert sha(base/name)==h,name
    csim=R/'hls_exp10_csim_r1.log';assert 'M14_V4_SELECTOR_CSIM=PASS valid=7 preflight_invalid=24 stage_errors=5 rtl_subset=0' in csim.read_text(encoding='utf-8-sig')
    report=X/'build/exp10_cosim_r1/hls/solution1/syn/report/lm_head_v4_selector_csynth.xml';root=ET.parse(report).getroot();ns=float(root.findtext('.//EstimatedClockPeriod'));assert ns<=5
    host=X/'reports/control_host_20261023_r1';assert 'PASS cases=25 fake_MMIO_only' in (host/'control.log').read_text();assert re.search(r'Ran 8 tests', (host/'mailbox.log').read_text()) and re.search(r'^OK\s*$',(host/'mailbox.log').read_text(),re.M)
    sources={p.relative_to(X).as_posix():sha(p) for p in [X/'standalone/selector_control.c',X/'standalone/selector_control.h',X/'tests/selector_control_test.c',X/'tests/test_selector_ps_mailbox.py',X/'standalone/selector_ps_mailbox.py',X/'standalone/scripts/private_board_common.tcl']}
    h=dict(state='PASS_HOST_FAKE_MMIO_AND_SYNTHETIC_MAILBOX',fake_mmio_cases=25,synthetic_mailbox_tests=8,source_sha256=sources,board='NOT_RUN')
    (host/'RESULT.json').write_text(json.dumps(h,indent=2)+'\n',encoding='utf-8')
    result=dict(state='PASS_HLS_CSIM_AND_SYNTHESIS_ONLY',hls_estimated_ns=ns,period_target_ns=5,uncertainty_ns=1.35,resources={e.tag:int(e.text) for e in root.find('.//AreaEstimates/Resources')},csim=dict(valid=7,preflight_invalid=24,stage_errors=5,real_sequence='chinese→english→chinese→code→math; four full preview/IDs/raw references, math production'),source_manifest_sha256=sha(X/'MANIFEST.json'),csim_log_sha256=sha(csim),synthesis_xml_sha256=sha(report),rtl='PENDING_SEPARATE_EVIDENCE',system_200MHz='PENDING_SEPARATE_EVIDENCE',board='NOT_RUN')
    (R/'HLS_SYNTHESIS_AUDIT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
