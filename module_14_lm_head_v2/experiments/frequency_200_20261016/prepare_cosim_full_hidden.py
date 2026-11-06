"""Only adapt simulation AXI depths to the full-hidden/small-vocab fixture."""
from pathlib import Path
import hashlib, json
here = Path(__file__).resolve().parent / 'reduce_layers'
source = here / 'src/lm_head_v2.cpp'
target = here / 'tests/kernel_full_hidden.cpp'
if target.exists(): raise SystemExit('Preserve existing full-hidden simulation copy')
original = source.read_text(encoding='utf-8')
before = '#ifdef LMH_V2_TEST_SMALL\n#pragma HLS INTERFACE m_axi'
branch = '''#if defined(LMH_V2_TEST_FULL_HIDDEN)
#pragma HLS INTERFACE m_axi port=hidden offset=slave bundle=hidden depth=112 max_read_burst_length=64 num_read_outstanding=4
#pragma HLS INTERFACE m_axi port=shared_vocab_weight offset=slave bundle=weight depth=7168 max_read_burst_length=16 num_read_outstanding=16 latency=64
#pragma HLS INTERFACE m_axi port=history_bitmap offset=slave bundle=history depth=1 max_read_burst_length=16 num_read_outstanding=4
#pragma HLS INTERFACE m_axi port=optional_logits offset=slave bundle=logits depth=16 max_write_burst_length=64 num_write_outstanding=8
#elif defined(LMH_V2_TEST_SMALL)
#pragma HLS INTERFACE m_axi'''
assert original.count(before) == 1
modified = original.replace(before, branch, 1)
assert modified.replace(branch, before, 1) == original
target.write_text(modified,encoding='utf-8')
(here / 'tests/full_hidden_copy_identity.json').write_text(json.dumps({
    'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
    'test_copy_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
    'only_change':'conditional HLS simulation interface depths; all arithmetic unchanged',
    'depths':{'hidden':112,'weight':7168,'history':1,'logits':16},
    'reason':'full-hidden fixture uses vocab=64; production depth overread crashed C-TB copy_in'
},indent=2)+'\n',encoding='utf-8')
print(target)
