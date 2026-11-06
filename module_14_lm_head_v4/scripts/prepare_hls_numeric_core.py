"""Extract unchanged accepted arithmetic functions into the isolated v4 top."""
from pathlib import Path
import hashlib,json
M=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    source=M.parent/'deliverables/20261020_M14_V3_1_r1/M14_V3_1_20261020_r1/module_14_lm_head_v3_1/src/lm_head_v2.cpp'
    assert sha(source)=='926911392a1664c05072ac3df2c9c494e55b9d94e72776c67ee5e642d5a5ef91'
    text=source.read_text(encoding='utf-8');body=text.split('namespace {',1)[1].split('void policy_and_argmax(',1)[0]
    content='#ifndef LMH4_ACCEPTED_NUMERIC_CORE_HPP\n#define LMH4_ACCEPTED_NUMERIC_CORE_HPP\n#include "lm_head_v4_candidate.hpp"\n#include "hls_stream.h"\nnamespace lmh4_detail {\n'+body+'\n}\n#endif\n'
    target=M/'src/accepted_numeric_core.hpp';target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():assert target.read_text(encoding='utf-8')==content
    else:target.write_text(content,encoding='utf-8')
    record=dict(state='PASS',baseline_source_sha256=sha(source),extracted_core_sha256=sha(target),
        scope='Exact original text from namespace start through reduce_rows; only includes/namespace/header guard wrapped. No FP operation or pragma changed.')
    (M/'reports/HLS_NUMERIC_CORE_PROVENANCE.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print('HLS_NUMERIC_CORE_EXTRACTION=PASS')
if __name__=='__main__':main()
