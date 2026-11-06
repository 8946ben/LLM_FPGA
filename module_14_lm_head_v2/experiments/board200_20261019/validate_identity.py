"""Verify that the board candidate changes hardware identity only."""
from pathlib import Path
import hashlib, json, re

m=Path(__file__).resolve().parents[2]
here=Path(__file__).resolve().parent
old=m/'experiments/frequency_200_20261016/reduce_layers'
assert (here/'src/lm_head_v2.cpp').read_bytes() == (old/'src/lm_head_v2.cpp').read_bytes()
h=(here/'include/lm_head_v2.hpp').read_text()
h=h.replace('0x20c08011u','0x10008011u').replace(
    'clock code=3 (200 MHz), module_revision=2. See doc/0924 clock table.',
    'clock=100 MHz, module_revision=1.')
assert h == (old/'include/lm_head_v2.hpp').read_text()
assert (here/'drivers/lm_head_v2_driver.h').read_text().replace('0x20c08011u','0x10008011u') == (m/'drivers/lm_head_v2_driver.h').read_text()
loader=(here/'loader/main.c').read_text().replace('192,168,0,190','192,168,8,190').replace('IP4_ADDR(&gw,0,0,0,0)','IP4_ADDR(&gw,192,168,8,1)').replace('ip=192.168.0.190','ip=192.168.8.190')
assert loader == (m/'standalone/tcp_loader/main.c').read_text()
manifest=json.loads((here/'source_manifest.json').read_text(encoding='utf-8'))
for name,expected in manifest['source_sha256'].items():
    assert hashlib.sha256((here/name).read_bytes()).hexdigest() == expected,name
oldrtl=m/'build/frequency_200_20261016/reduce_layers/csynth/solution1/syn/verilog'
newrtl=m/'build/board200_20261019/hls/solution1/syn/verilog'
oldfiles={p.name:p for p in oldrtl.glob('*.v')}
newfiles={p.name:p for p in newrtl.glob('*.v')}
assert oldfiles.keys() == newfiles.keys()
changed=[]
def normalize(text):
    return re.sub(r'^//.*$', '', text, flags=re.M).replace("32'd549486609", "32'd268468241")
for name in oldfiles:
    a=oldfiles[name].read_text(); b=newfiles[name].read_text()
    if a != b: changed.append(name)
    assert normalize(a) == normalize(b), 'Unexpected RTL change: '+name
out=m/'reports/board200_20261019'
out.mkdir(parents=True,exist_ok=True)
result=dict(state='PASS',rtl_modules=len(newfiles),changed_rtl=changed,
    comparison='Ignoring generated // comments, all RTL matches diagnostic candidate after normalizing only build_config constant.',
    source_arithmetic_byte_identical=True,loader_change='IP/subnet and direct-link gateway only; tcp_output retry retained')
(out/'identity_validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
