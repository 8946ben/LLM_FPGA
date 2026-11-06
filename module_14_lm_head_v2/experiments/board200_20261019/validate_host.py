"""Regress timing conversion against a real old mailbox, plus fail-closed profiles."""
from pathlib import Path
import copy, hashlib, json, struct, subprocess, sys

module = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(module/'standalone'))
from board_profile import load_profile, check_loader_pair

out = module/'build/board200_20261019/host_validation'
out.mkdir(parents=True, exist_ok=True)
old = json.loads((module/'reports/board_runs/20261010_104006_168_acceptance/campaign.json').read_text(encoding='utf-8-sig'))
record = next(r for r in old['records'] if r['campaign_phase'] == 'performance')
data = bytearray((Path(record['source_run'])/'mailbox_output.bin').read_bytes())
assert struct.unpack_from('<I',data,224)[0] == 0x10008011
package = out/'package'
package.mkdir(exist_ok=True)
profile = package/'RUN_PROFILE.json'
profile.write_text(json.dumps(dict(build_config='0x20c08011', ip_clock_hz=200_000_000, clock_basis='nominal PL user clock')))
(package/'ARTIFACTS.sha256').write_text(hashlib.sha256(profile.read_bytes()).hexdigest()+'  RUN_PROFILE.json\n')
assert load_profile(package)['ip_clock_hz'] == 200_000_000
checks=[]
def parse(name, build, package_arg, expected_exit):
    d = bytearray(data)
    struct.pack_into('<I',d,224,build)
    dump = out/(name+'.bin')
    dump.write_bytes(d)
    decoded=out/(name+'.json')
    cmd=[sys.executable,str(module/'standalone/parse_mailbox.py'),str(dump),'--json-output',str(decoded)]
    if package_arg: cmd+=['--package-dir',str(package_arg)]
    result=subprocess.run(cmd,capture_output=True,text=True)
    assert result.returncode == expected_exit,(name,result.stdout,result.stderr)
    checks.append(name)
    return json.loads(decoded.read_text())['records'][0]
a=parse('old_100',0x10008011,None,0)
b=parse('new_200',0x20c08011,package,0)
assert a['ip_seconds'] == 2*b['ip_seconds']
assert 'ip_seconds_100mhz' not in b
parse('reject_new_hardware_with_legacy_profile',0x20c08011,None,1)
parse('reject_old_hardware_with_200_profile',0x10008011,package,1)
synthetic=copy.deepcopy(old)
synthetic['package_dir']=str(package)
for r in synthetic['records']:
    r['build_config']=0x20c08011
    r['ip_clock_hz']=200_000_000
campaign=out/'synthetic_200_campaign.json'
campaign.write_text(json.dumps(synthetic))
summary_path=out/'synthetic_200_summary.json'
result=subprocess.run([sys.executable,str(module/'scripts/summarize_acceptance.py'),str(campaign),
    '--manifest',str(module.parent/'artifacts/module14_v2_assets/manifest.json'),
    '--output',str(summary_path)],capture_output=True,text=True)
assert result.returncode == 0,(result.stdout,result.stderr)
assert json.loads(summary_path.read_text())['performance']['ip_ms_median'] == b['ip_seconds']*1000
checks.append('campaign_200mhz_conversion_and_validation')
profile.write_text(profile.read_text()+' ')
try: load_profile(package)
except ValueError: checks.append('reject_tampered_profile')
else: raise AssertionError('Tampered profile accepted')
hardware=out/'pair_hardware'; loader=out/'pair_loader'
hardware.mkdir(exist_ok=True); loader.mkdir(exist_ok=True)
xsa=hardware/'m14_v2_single.xsa'; init=loader/'psu_init.tcl'
xsa.write_bytes(b'synthetic XSA binding test'); init.write_bytes(b'synthetic PS init binding test')
pair=dict(build_config='0x20c08011',ip_clock_hz=200_000_000,clock_basis='nominal PL user clock',
    hardware_xsa_sha256=hashlib.sha256(xsa.read_bytes()).hexdigest(),
    psu_init_sha256=hashlib.sha256(init.read_bytes()).hexdigest(),board_ip='192.168.0.190')
def freeze(p,document):
    f=p/'RUN_PROFILE.json'; f.write_text(json.dumps(document))
    (p/'ARTIFACTS.sha256').write_text(hashlib.sha256(f.read_bytes()).hexdigest()+'  RUN_PROFILE.json\n')
freeze(hardware,pair); freeze(loader,pair)
assert check_loader_pair(hardware,loader,'192.168.0.190')
checks.append('matching_hardware_loader_pair')
for name,action in (
    ('reject_wrong_loader_ip',lambda:check_loader_pair(hardware,loader,'192.168.8.190')),
    ('reject_mixed_legacy_loader',lambda:check_loader_pair(hardware,module/'reports/tcp_loader_package_20261010','192.168.0.190'))):
    try: action()
    except ValueError: checks.append(name)
    else: raise AssertionError(name)
init.write_bytes(b'wrong 100 MHz init')
try: check_loader_pair(hardware,loader,'192.168.0.190')
except ValueError: checks.append('reject_wrong_ps_init')
else: raise AssertionError('Wrong PS init accepted')
summary=dict(state='PASS',checks=checks,old_ip_ms=a['ip_seconds']*1000,new_ip_ms=b['ip_seconds']*1000,
             note='Synthetic 200 MHz identity on an old real mailbox; host conversion regression only, not a 200 MHz board result.')
(out/'result.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
