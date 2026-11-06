"""Independent structural/fixture review only; this is not an HDL compiler."""
from pathlib import Path
import csv,datetime,hashlib,json,re
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4'
E=M/'experiments/d64_state_tb_20261104_r1';R=M/'reports/d64_state_tb_20261104_r1'
F=M/'reports/d64_state_fixtures_20261104_r2';FE=M/'experiments/d64_state_fixtures_20261104_r2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=json.loads((R/'PREPARATION.json').read_text());manifest=json.loads((F/'MANIFEST.json').read_text())
    assert p['state']=='PREPARED_FULL_DUT_STATE_TESTBENCH_NOT_COMPILED'
    for name,digest in p['sources'].items():assert sha(ROOT/name)==digest,name
    assert p['fixture_manifest_sha256']==sha(F/'MANIFEST.json') and p['fixture_control_sha256']==sha(FE/'control_sequences.json')
    tb=(E/'d64_state_tb.sv').read_text()
    top=ROOT/next(n for n in p['sources'] if n.endswith('/lm_head_v4_partial_proto.v'))
    port_list=re.search(r'module lm_head_v4_partial_proto\s*\((.*?)\);',top.read_text(),re.S).group(1)
    expected=set(re.findall(r'\b\w+\b',port_list))
    instance=re.search(r'lm_head_v4_partial_proto dut\((.*?)\);',tb,re.S).group(1)
    connections=re.findall(r'\.(\w+)\((\w+)\)',instance)
    assert len(connections)==110 and {a for a,b in connections}==expected and all(a==b for a,b in connections)
    assert len(set(a for a,b in connections))==110
    # A deliberately limited lexical check, not a claim of legal SV elaboration.
    for lineno,line in enumerate(tb.splitlines(),1):
        line=re.sub(r'//.*','',line)
        assert len(re.findall(r'(?<!\\)"',line))%2==0,('unterminated line string',lineno)
    stripped=re.sub(r'"(?:\\.|[^"\\])*"','""',re.sub(r'//[^\n]*','',tb))
    words=re.findall(r'\b\w+\b',stripped)
    for opening,closing in [('begin','end'),('task','endtask'),('fork','join'),('module','endmodule')]:
        assert words.count(opening)==words.count(closing),(opening,closing)
    assert re.findall(r'\bap_rst_n\s*=\s*([01])\s*;',tb)==['0','1']
    assert tb.count('tvinload_hex128_single(weight_tv,545685504,0)')==1
    assert 'mem_weights.storage=weight_loader.pages[0]' in tb
    assert '.READ_ONLY(1)) mem_weights' in tb and '.N(80591),.STORAGE_N(80592)' in tb
    assert tb.count('load_meta(input_path);dump_memory(label,"before");')==1
    assert 'dump_memory(label,"after");' in tb and 'STATE_PRODUCTION_RAW_WRITE' in tb
    assert 'expected_status==0?64\'d1220608:64\'d0' in tb
    assert 'STATE_REAL_CALL_NOT_OBSERVED' in tb and 'STATE_END_GUARD_CHANGED' in tb
    assert 'STATE_EARLY_ERROR_SIDE_EFFECT' in tb and 'STATE_BAD_PARAMETER_READ_META' in tb
    assert 'STATE_ERROR_READ_CANONICAL' in tb and 'STATE_DONE_NOT_CLEARED_OR_NOT_IDLE' in tb
    schedule=(E/'state_schedule.svh').read_text().splitlines();assert len(schedule)==12
    for s,line in zip(manifest['scenarios'],schedule,strict=True):
        assert line.startswith('run_case(') and line.endswith(');')
        fields=next(csv.reader([line[9:-2]]));assert len(fields)==12
        assert [int(fields[i]) for i in [0,3,4,5,8]]==[s['case_index'],s['debug'],s['capacity'],s['expected']['expected_status'],s['expected']['k']]
        assert fields[1]==s['label'] and fields[2]==s['input_path']
        for index,name in [(6,'token'),(7,'score_bits'),(9,'crc')]:
            assert int(fields[index].split("'h")[1],16)==s['expected'][name]
        injection=next((x for x in s['mutations'] if x['region']=='weights'),None)
        assert int(fields[10])==(injection['offset_bytes'] if injection else -1)
        assert int(fields[11].split("'h")[1],16)==(int.from_bytes(bytes.fromhex(injection['expected_original_hex']),'little') if injection else 0)
    sentinel=(E/'state_weight_sentinels.svh').read_text();rows=re.findall(r'read_one_elem\(byte_value,(\d+)\);if\(rc\|\|byte_value!==8\x27h([0-9a-f]{2})\)',sentinel)
    assert len(rows)==1522
    source=M/'experiments/sim_memory_bank_20261026/weights_preflight.svh'
    assert [int(a) for a,v in rows]==list(map(int,re.findall(r'byte mismatch at (\d+)',source.read_text())))
    with (M/'reports/layout_topk_20261024_r1/assets/tiled_W_B1024.bin').open('rb') as a,(ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin').open('rb') as b:
        for address,value in rows:
            address=int(address);f,offset=(a,address) if address<273416192 else (b,address-273416192)
            f.seek(offset);assert f.read(1)[0]==int(value,16)
    assert not (R/'WORKFLOW.json').exists() and not (R/'ACTIVE.lock').exists()
    result=dict(state='PASS_INDEPENDENT_STRUCTURAL_PREPARATION_ONLY',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        port_connections=110,scenarios=12,sentinel_literals=1522,one_weight_initialization=True,no_inter_call_reset_in_draft=True,
        preparation_sha256=sha(R/'PREPARATION.json'),testbench_sha256=sha(E/'d64_state_tb.sv'),
        not_proven=['SV syntax/elaboration','Actual full-DUT calls','Actual state/mode/error preservation','Normal-response timing','Actual native model qualification'],
        eda='NOT_RUN',board='NOT_RUN',automatic_next_stage=False)
    (R/'INDEPENDENT_PREPARATION_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
