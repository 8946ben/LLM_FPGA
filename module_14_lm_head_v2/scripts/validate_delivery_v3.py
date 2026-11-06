"""Offline lm_head v3 delivery audit. No hardware access or EDA rebuild."""
from pathlib import Path
import argparse, contextlib, hashlib, importlib.util, io, json, os, re, subprocess, sys, tempfile
import xml.etree.ElementTree as ET

M=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(M/'standalone'))
from board_profile import load_profile, check_loader_pair

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def sums(base):
    tracked=set()
    for line in (base/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        digest,name=line.split('  ',1); p=(base/name).resolve()
        assert p.is_relative_to(base.resolve()) and sha(p)==digest,name
        tracked.add(name)
    actual={p.relative_to(base).as_posix() for p in base.rglob('*') if p.is_file()
            and not {'build','__pycache__','.Xil'}.intersection(p.relative_to(base).parts)
            and p!=base/'SHA256SUMS'}
    assert actual==tracked,(actual-tracked,tracked-actual)
    print('SHA256=PASS files='+str(len(tracked)))

def run(args,cwd=M):
    subprocess.run([sys.executable,'-B',*map(str,args)],cwd=cwd,check=True)

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--skip-hashes',action='store_true'); args=parser.parse_args()
    if not args.skip_hashes: sums(M); sums(M.parent)
    manifest=json.loads((M/'module_manifest.json').read_text(encoding='utf-8'))
    assert manifest['release_name']=='lm_head v3' and manifest['abi_version']==2
    assert manifest['build_config']=='0x20c08011' and manifest['target_clock_hz']==200_000_000
    for rel,digest in manifest['tested_source_sha256'].items(): assert sha(M/rel)==digest,rel
    ip=M/'ip_repo/lm_head_v2'; ns={'s':'http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009'}
    xml=ET.parse(ip/'component.xml').getroot()
    assert xml.findtext('s:version',namespaces=ns)=='2.1'
    refs=xml.findall('s:fileSets/s:fileSet/s:file/s:name',ns)
    for n in refs:
        p=(ip/n.text).resolve(); assert p.is_relative_to(ip.resolve()) and p.is_file(),n.text
    regs=[]
    for r in xml.findall('s:memoryMaps/s:memoryMap/s:addressBlock/s:register',ns):
        reset=r.find('s:reset/s:value',ns)
        regs.append(dict(name=r.findtext('s:name',namespaces=ns),offset=int(r.findtext('s:addressOffset',namespaces=ns),0),
            width_bits=int(r.findtext('s:size',namespaces=ns),0),access=r.findtext('s:access',namespaces=ns),reset=int(reset.text,0) if reset is not None else None))
    assert regs==json.loads((M/'interface/interface_contract.json').read_text(encoding='utf-8'))['control_registers']
    assert sha(M/'drivers/generated/xlm_head_v2_hw.h')==sha(M/'reports/hls/xlm_head_v2_hw.h')
    print(f'IP_REFERENCES_AND_REGISTERS=PASS files={len(refs)} registers={len(regs)}')
    for name,expected in (('board_package_lm_head_v3',0x20c08011),('baseline_100_package',0x10008011)):
        p=M/'reports'/name
        for line in (p/'ARTIFACTS.sha256').read_text().splitlines():
            digest,rel=line.split('  ',1); assert sha(p/rel)==digest,rel
        profile=load_profile(p); assert profile['build_config']==expected
        check_loader_pair(p,p,'192.168.0.190')
    assert '0x20c08011' in (M/'include/lm_head_v2.hpp').read_text()
    assert 'create_clock -period 5' in (M/'scripts/run_csynth.tcl').read_text()
    assert 'set_clock_uncertainty 1.350' in (M/'scripts/run_csynth.tcl').read_text()
    assert '-version 2.1' in (M/'scripts/run_export_ip.tcl').read_text()
    assert 'PL0_REF_CTRL__DIVISOR0 {2}' in (M/'board/create_bd.tcl').read_text()
    print('CLOCK_BUILD_AND_PACKAGE_BINDINGS=PASS')
    run(['-m','unittest','discover','-p','test_*.py','-v'],M/'reference')
    run(['reference/validate_source_contract.py'])
    run(['reference/verify_assets.py','--asset-root',M.parent/'artifacts/module14_v2_assets','--manifest',M/'golden/v2_trace_manifest.json'])
    spec=importlib.util.spec_from_file_location('mailbox',M/'standalone/parse_mailbox.py')
    mailbox=importlib.util.module_from_spec(spec); spec.loader.exec_module(mailbox)
    total=0
    temp=M/'build/delivery_checks'; temp.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=temp) as td:
        for campaign_rel in manifest['portable_campaigns']:
            path=M/campaign_rel; campaign=json.loads(path.read_text(encoding='utf-8'))
            pkg=M/campaign['package_dir']
            for record in campaign['records']:
                data=M/record['source_run']/'mailbox_output.bin'; saved=sys.argv; captured=io.StringIO()
                try:
                    sys.argv=['parse_mailbox.py',str(data),'--step',record['step'],'--package-dir',str(pkg)]
                    with contextlib.redirect_stdout(captured): code=mailbox.main()
                finally: sys.argv=saved
                assert code==(1 if record['campaign_phase']=='golden_failure' else 0),record['source_run']
                decoded,_=json.JSONDecoder().raw_decode(captured.getvalue())
                for key,value in decoded.items():
                    if key not in ('source_run','profile_source'): assert record[key]==value,(key,value,record.get(key))
                total+=1
            run(['scripts/summarize_acceptance.py',campaign_rel,'--manifest','golden/v2_trace_manifest.json','--output',Path(td)/(path.parent.name+'.json')])
    print(f'RAW_MAILBOX_CAMPAIGNS=PASS runs={total}')
    print('LM_HEAD_V3_DELIVERY_OFFLINE_VERIFY=PASS (no board access)')

if __name__=='__main__': main()
