"""Copy frozen 100 MHz images, pair the subnet-only loader variant, hash inputs."""
from pathlib import Path
import hashlib, json, shutil

m=Path(__file__).resolve().parents[2]
out=m/'reports/board200_20261019/baseline_100_package'
assert not out.exists(), 'Preserve baseline package'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
frozen=m/'reports/board_package_20261009'
old_loader=m/'reports/tcp_loader_package_20261010'
files={}
for package,names in ((frozen,('m14_v2_system_wrapper.bit','m14_v2_single.xsa','m14_v2_test.elf')),
                      (old_loader,('psu_init.tcl',))):
    hashes={line.split()[1]:line.split()[0] for line in (package/'ARTIFACTS.sha256').read_text().splitlines()}
    for name in names:
        assert sha(package/name)==hashes[name]
        files[name]=package/name
files['m14_tcp_loader.elf']=m/'build/board200_20261019/baseline_loader/m14_tcp_loader.elf'
assert all(p.is_file() for p in files.values())
out.mkdir(parents=True)
for name,source in files.items(): shutil.copy2(source,out/name)
profile=dict(format='M14_BOARD_RUN_PROFILE_V1',build_config='0x10008011',ip_clock_hz=100_000_000,
    clock_basis='nominal PL user clock',hardware_xsa_sha256=sha(out/'m14_v2_single.xsa'),
    psu_init_sha256=sha(out/'psu_init.tcl'),board_ip='192.168.0.190',
    note='Accepted 100 MHz bit/XSA/test ELF unchanged; repaired loader changes subnet only.')
(out/'RUN_PROFILE.json').write_text(json.dumps(profile,indent=2)+'\n')
(out/'ARTIFACTS.sha256').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in sorted(out.iterdir()) if p.is_file()))
print('M14_BASELINE_PACKAGE='+str(out))
