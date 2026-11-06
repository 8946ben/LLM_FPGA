"""Private Exp10 catalog and exact exported register map, never board access."""
from pathlib import Path
import hashlib,json,re,shutil,xml.etree.ElementTree as ET
M=Path(__file__).resolve().parents[1];X=M/'experiments/fusion_exp10_20261023';R=M/'reports/fusion_exp10_20261023_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(s):
    s=re.sub(r'//\s*(?:synopsys\s+)?(?:synthesis\s+)?translate_off.*?//\s*(?:synopsys\s+)?(?:synthesis\s+)?translate_on','',s,flags=re.S)
    return re.sub(r'\s+','',s)
def main():
    assert json.loads((R/'RTL_QUALIFICATION.json').read_text())['state'].startswith('PASS_')
    sol=M.parent/'.cache/e10/hls/solution1';source=sol/'impl/ip';target=X/'ip_repo/lm_head_v4_selector';assert not target.exists()
    ns={'s':'http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009'};root=ET.parse(source/'component.xml');vlnv=[root.findtext('s:'+k,namespaces=ns) for k in ['vendor','library','name','version']];assert vlnv==['exp10.local','hls','lm_head_v4_selector','4.10']
    ports={p.findtext('s:name',namespaces=ns):p for p in root.findall('s:model/s:ports/s:port',ns)}
    for n in ['m_axi_plmem_ARADDR','m_axi_plmem_AWADDR','m_axi_histmem_ARADDR','m_axi_histmem_AWADDR']:assert ports[n].findtext('.//s:left',namespaces=ns)=='63'
    equivalence={}
    for p in (sol/'syn/verilog').glob('*.v'):
        dst=source/'hdl/verilog'/p.name;assert dst.exists(),p.name;a=p.read_text();b=dst.read_text();assert a==b or canonical(a)==canonical(b),p.name;equivalence[p.name]=dict(synth_sha256=sha(p),export_sha256=sha(dst),byte_identical=a==b)
    headers=list((source/'drivers').glob('*/src/xlm_head_v4_selector_hw.h'));assert len(headers)==1;header=headers[0].read_text();expected={'PL_DDR':0x10,'HISTORY_BITMAP':0x1c,'ARENA_BYTES':0x28,'DESCRIPTOR_OFFSET':0x34,'COMMAND':0x40,'STATUS':0x48,'STAGE':0x58,'CHILD_STATUS':0x68,'ROUTE_COUNT':0x78,'CANDIDATE_COUNT':0x88,'DENSE_FALLBACK':0x98,'SELECTED_TOKEN_OUT':0xa8,'SCORE':0xb8,'OUTPUT_CRC':0xc8}
    for n,offset in expected.items():
        found=re.search(r'^#define\s+XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_'+n+r'_DATA\s+(0x[0-9a-fA-F]+)',header,re.M);assert found and int(found[1],0)==offset,n
    shutil.copytree(source,target,ignore=shutil.ignore_patterns('.Xil','*.log','*.jou'));files={p.relative_to(target).as_posix():sha(p) for p in target.rglob('*') if p.is_file()}
    for n,h in files.items():assert sha(source/n)==h,n
    frozen=json.loads((X/'MANIFEST.json').read_text())
    for n,h in frozen['source_sha256'].items():assert sha(X/n)==h,n
    result=dict(state='PRIVATE_EXP10_IP_FROZEN_EXACT_REGISTER_AND_SYNTHESIZABLE_RTL_AUDITED',vlnv=':'.join(vlnv),files=files,source_sha256=frozen['source_sha256'],rtl_equivalence=equivalence,register_offsets=expected,driver_directory=headers[0].parent.parent.name,layout_sha256=sha(X/'interface/PL_DDR_LAYOUT_V4.json'),signature='0x4D345A0A',quality='QUALITY_FAIL_NO_RELEASE_NO_RETUNE',board='NOT_RUN')
    (R/'PRIVATE_IP_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['state'],len(files),result['driver_directory'])
if __name__=='__main__':main()
