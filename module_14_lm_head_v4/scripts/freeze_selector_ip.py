"""Freeze a private generated IP before independent BD and RTL runs."""
from pathlib import Path
import hashlib,json,shutil,xml.etree.ElementTree as ET
M=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    source=M/'build/selector_csynth_r2/hls/solution1/impl/ip';target=M/'ip_repo/lm_head_v4_selector'
    assert (source/'component.xml').exists() and not target.exists()
    ns={'s':'http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009'};x=ET.parse(source/'component.xml')
    vlnv=[x.findtext('s:'+n,namespaces=ns) for n in ('vendor','library','name','version')]
    assert vlnv==['user.org','hls','lm_head_v4_selector','4.0']
    interfaces=[e.findtext('s:name',namespaces=ns) for e in x.findall('s:busInterfaces/s:busInterface',ns)]
    assert {'s_axi_control','m_axi_plmem','m_axi_histmem'}<=set(interfaces)
    ports={p.findtext('s:name',namespaces=ns):p for p in x.findall('s:model/s:ports/s:port',ns)}
    for port in ('m_axi_plmem_ARADDR','m_axi_plmem_AWADDR','m_axi_histmem_ARADDR','m_axi_histmem_AWADDR'):
        assert ports[port].findtext('.//s:left',namespaces=ns)=='63'
    shutil.copytree(source,target,ignore=shutil.ignore_patterns('.Xil','*.log','*.jou'))
    files={p.relative_to(target).as_posix():sha(p) for p in target.rglob('*') if p.is_file()}
    for relative,digest in files.items():assert sha(source/relative)==digest
    inputs=['src/lm_head_v4_selector.cpp','include/lm_head_v4_selector.hpp','src/lm_head_v4_lowrank.cpp','src/lm_head_v4_router.cpp','src/lm_head_v4_topk.cpp','src/lm_head_v4_candidate.cpp','src/accepted_numeric_core.hpp','hls_selector.tcl']
    record=dict(state='PRIVATE_IP_FROZEN',vlnv=':'.join(vlnv),scope='Offline experimental IP only; not released/board accepted',
        path=target.relative_to(M).as_posix(),component_sha256=sha(target/'component.xml'),interfaces=interfaces,address_width=64,
        files=files,source_sha256={f:sha(M/f) for f in inputs},layout_sha256=sha(M/'interface/PL_DDR_LAYOUT_V4.json'),
        board_signature='0x4D345301',signature_scope='Private system GPIO2; not a released M14 public ABI/build_config')
    (M/'reports/SELECTOR_PRIVATE_IP_MANIFEST.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('SELECTOR_PRIVATE_IP=FROZEN files='+str(len(files))+' AXI64x2 verified')
if __name__=='__main__':main()
