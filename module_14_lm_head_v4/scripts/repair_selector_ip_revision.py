"""Only local generated packaging metadata; original and digest preserved."""
from pathlib import Path
import hashlib,json,re,time
M=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=(M/'build/selector_csynth_r2/hls/solution1/impl/ip/run_ippack.tcl').resolve()
    assert p.is_relative_to((M/'build').resolve())
    record=M/'reports/SELECTOR_LOCAL_IP_REVISION_REPAIR.json'
    if record.exists():
        d=json.loads(record.read_text());assert sha(p)==d['patched_sha256'];print('SELECTOR_IP_REVISION=ALREADY_APPLIED');return
    source=p.read_text(encoding='utf-8');m=re.search(r'^set Revision\s+"([0-9]+)"\r?$',source,re.M)
    assert m and int(m[1])>2147483647
    revision=int(time.time());assert 0<revision<=2147483647
    patched=source[:m.start()]+f'set Revision "{revision}"'+source[m.end():]
    original=p.with_suffix('.original.tcl');assert not original.exists();original.write_bytes(p.read_bytes());before=sha(p)
    p.write_text(patched,encoding='utf-8')
    record.write_text(json.dumps(dict(state='APPLIED',scope='Local generated private selector IP metadata only; no EDA install/system time/source changes',original_revision=m[1],replacement_revision=revision,original_sha256=before,patched_sha256=sha(p)),indent=2)+'\n',encoding='utf-8')
    print('SELECTOR_IP_REVISION=APPLIED')
if __name__=='__main__':main()
