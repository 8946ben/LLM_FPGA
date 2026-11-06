"""Bind simulated DUT to the frozen IP, explicitly excluding translate_off instrumentation."""
from pathlib import Path
import hashlib,json,re,difflib
M=Path(__file__).resolve().parents[1]
def sha(data):return hashlib.sha256(data).hexdigest()
def synth_text(data):
    text=data.decode('utf-8')
    # Only explicit vendor synthesis translate_off/on spans may be removed.
    assert text.count('// synthesis translate_off')==text.count('// synthesis translate_on')
    text=re.sub(r'// synthesis translate_off.*?// synthesis translate_on','',text,flags=re.S)
    return re.sub(r'\s+','',text).encode('utf-8')
def main():
    s=M/'build/selector_full_cosim_r2/hls/solution1/syn/verilog'
    q=M/'ip_repo/lm_head_v4_selector/hdl/verilog'
    rows={};normalized=[]
    for p in s.glob('*.v'):
        a=p.read_bytes();b=(q/p.name).read_bytes()
        equal=a==b
        if not equal:
            assert p.name=='lm_head_v4_selector.v','Unexpected changed child RTL'
            assert synth_text(a)==synth_text(b),'Synthesizable top differs'
            delta=''.join(difflib.unified_diff(a.decode().splitlines(True),b.decode().splitlines(True),fromfile='CoSim_synthesis',tofile='frozen_IP'))
            (M/'reports/SELECTOR_RTL_IP_TOP_DIFF.txt').write_text(delta,encoding='utf-8')
            normalized.append(p.name)
        rows[p.name]=dict(sim_sha256=sha(a),ip_sha256=sha(b),byte_identical=equal,
                         synthesizable_text_sha256=sha(synth_text(a)))
    assert len(rows)==96 and normalized==['lm_head_v4_selector.v']
    result=dict(state='PASS_SYNTHESIZABLE_RTL_EQUIVALENCE',scope='CoSim DUT versus frozen IP used by Vivado',
      byte_identical_files=95,translate_off_only_files=normalized,
      difference='Top IP adds only simulation deadlock-detector include inside synthesis translate_off, empty translate_off spans and whitespace',
      files=rows,hardware_access='NONE')
    (M/'reports/SELECTOR_RTL_IP_EQUIVALENCE.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('RTL_IP_EQUIVALENCE=PASS 95byte-identical +1top translate_off-only; no source/IP modification')
if __name__=='__main__':main()
