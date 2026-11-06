"""Gated actual full-project input initialization/all-word readback, time0 stop."""
from pathlib import Path
import json,hashlib,tarfile,shutil
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';BASE='memory_full_startup_20261103_r1';NAME='memory_burst_full_input_20261103_r1'
B=M/'experiments'/BASE;E=M/'experiments'/NAME;R=M/'reports'/NAME;C=M/'experiments/memory_burst_model_20261103_r3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 E.mkdir(exist_ok=True);R.mkdir(exist_ok=True);assert not (R/'PLAN.json').exists()
 for n in ['axi_state.sv','lm_head_v4_partial_proto_subsys_test_sequence_lib.sv','memory_probe_pkg.sv','memory_prefix.sv']:shutil.copy2(B/n,E/n)
 shutil.copy2(C/'mem_model.sv',E/'mem_model.sv');changes=json.loads((B/'CHANGES.json').read_text());changes['mem_model']['edits']+=json.loads((C/'MODEL_CHANGES.json').read_text())['edits']
 gates={'gate_small.json':M/'reports/memory_burst_small_20261103_r3/INDEPENDENT_REVIEW.json','gate_semantics.json':M/'reports/memory_burst_semantics_20261103_r4/INDEPENDENT_REVIEW.json'}
 for n,p in gates.items():
  j=json.loads(p.read_text());assert j['state'].startswith('PASS_INDEPENDENT_') and j['model_sha256']==sha(C/'mem_model.sv');shutil.copy2(p,E/n)
 ref=(B/'reference_model.sv').read_text()
 def edit(a,b):
  nonlocal ref
  assert ref.count(a)==1,a[:100];ref=ref.replace(a,b);changes['reference_model']['edits'].append([a,b])
 concat='{'+','.join('source_word[%d:%d]'%(i+7,i) for i in range(0,128,8))+'}'
 task=r'''    // Compare packed readback against original binary, all16 bytes per word.
    task automatic burst_verify_binary(input string path,input int base,input int count);
        integer fd,rc,i;
        reg[127:0] source_word;
        logic[127:0] actual_word,expected_word;
        fd=$fopen(path,"rb");if(!fd) `uvm_fatal("burst_binary","reference open")
        for(i=0;i<count;i+=16)begin
            rc=$fread(source_word,fd);if(rc!=16) `uvm_fatal("burst_binary","reference short read")
            expected_word=REVERSE_BYTES;
            rc=mem_blk_pages_weights.pages[0].read_packed16(actual_word,base+i);
            if(rc || actual_word!==expected_word)begin
                $display("BURST_BINARY_MISMATCH offset=%0d actual=%h expected=%h rc=%0d",base+i,actual_word,expected_word,rc);
                `uvm_fatal("burst_binary","all-word readback mismatch")
            end
            if((i+16)%16777216==0)lmh_memory_probe_pkg::sample("binary_verify_progress",base+i+16);
        end
        rc=$fgetc(fd);if(rc!=-1) `uvm_fatal("burst_binary","reference trailing bytes")
        $fclose(fd);$display("BURST_FULL_BINARY_PASS base=%0d bytes=%0d words=%0d",base,count,count/16);
    endtask

'''.replace('REVERSE_BYTES',concat)
 edit('    virtual task run_phase(uvm_phase phase);',task+'    virtual task run_phase(uvm_phase phase);')
 prefix='/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1/'
 calls='''lmh_memory_probe_pkg::sample("after_1522_sentinels",1522);
lmh_memory_probe_pkg::sample("before_full_binary_verify",545685504);
burst_verify_binary("TILED_PATH",0,273416192);
burst_verify_binary("CANONICAL_PATH",273416192,272269312);
lmh_memory_probe_pkg::sample("after_full_binary_verify",545685504);
$display("BURST_FULL_INPUT_INIT_PASS bytes=545685504 words=34105344 sentinel=1522 all_bytes=1 time0=1");
$finish;'''.replace('TILED_PATH',prefix+'module_14_lm_head_v4/reports/layout_topk_20261024_r1/assets/tiled_W_B1024.bin').replace('CANONICAL_PATH',prefix+'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin')
 edit('lmh_memory_probe_pkg::sample("after_1522_sentinels",1522);',calls)
 (E/'reference_model.sv').write_text(ref);(E/'CHANGES.json').write_text(json.dumps(changes,indent=2)+'\n')
 runner=(ROOT/'tools/run_memory_full_startup_20261103.py').read_text().replace(BASE,NAME)
 anchor="plan=json.loads((R/'PLAN.json').read_text());guard=plan['guards']"
 verify="""plan=json.loads((R/'PLAN.json').read_text());guard=plan['guards']
 for n,expected in [('gate_small.json','PASS_INDEPENDENT_BURST_FULL_PROJECT_SMALL_COMPARISON'),('gate_semantics.json','PASS_INDEPENDENT_BURST_MODEL_SEMANTICS')]:
  gate=json.loads((E/n).read_text());assert gate['state']==expected and gate['model_sha256']==sha(E/'mem_model.sv')
"""
 assert runner.count(anchor)==1;runner=runner.replace(anchor,verify.rstrip())
 runner=runner.replace("  assert sum(x.startswith('MEMORY_PREFIX_PASS cycles=20000 ') for x in lines)==1", "  assert lines.count('BURST_FULL_INPUT_INIT_PASS bytes=545685504 words=34105344 sentinel=1522 all_bytes=1 time0=1')==1\n  assert lines.count('BURST_FULL_BINARY_PASS base=0 bytes=273416192 words=17088512')==1\n  assert lines.count('BURST_FULL_BINARY_PASS base=273416192 bytes=272269312 words=17016832')==1")
 runner=runner.replace("for name in ['memory_phases.csv','weights_readback.csv','stage_profile.csv']","for name in ['memory_phases.csv','weights_readback.csv']")
 runner=runner.replace('TOOL_PASS_FINITE_PREFIX_AWAITING_INDEPENDENT_REVIEW','TOOL_PASS_BURST_FULL_INPUT_AWAITING_INDEPENDENT_REVIEW').replace('GROUP_RSS_OVER_64GIB','GROUP_RSS_OVER_LIMIT')
 anchor="assert sha(tv)==fullplan['full_tv_sha256']"
 verify="""assert sha(tv)==fullplan['full_tv_sha256']
  for n,h in plan['weight_sha256'].items():assert sha(ROOT/n)==h,n
  state.setdefault('weight_source_sha256_checks',[]).append(dict(utc=stamp(),digests=plan['weight_sha256']));save()"""
 assert runner.count(anchor)==2;runner=runner.replace(anchor,verify)
 compile(runner,'burst_full_input.py','exec');(E/'run_startup.py').write_text(runner)
 p=json.loads((M/'reports'/BASE/'PLAN.json').read_text());p.update(state='FROZEN_GATED_BURST_FULL_INPUT_INIT_ONLY',source_sha256={str(x.relative_to(ROOT)).replace('\\','/'):sha(x) for x in E.iterdir() if x.is_file()},scope='Actual full-project initialization; original545685504B input;1522 sentinels plus all34105344 packed words compared with original binaries;stop at time0;not full M14',guards={'initial_available_gib':96,'running_available_gib':32,'group_rss_gib':16,'elaborate_seconds':300,'simulate_seconds':1800})
 p['weight_sha256']=json.loads((M/'reports/d64_full_input_preflight_20261102_r2/PLAN.json').read_text())['weight_sha256']
 (R/'PLAN.json').write_text(json.dumps(p,indent=2)+'\n')
 with tarfile.open(R/'entry.tar.gz','w:gz') as t:
  for x in list(E.iterdir())+[R/'PLAN.json']:t.add(x,arcname=str(x.relative_to(ROOT)))
 template=(ROOT/'tools/bootstrap_memory_full_startup_20261103.py').read_text().replace(BASE,NAME).replace(sha(M/'reports'/BASE/'entry.tar.gz'),sha(R/'entry.tar.gz'))
 (ROOT/'tools/bootstrap_memory_burst_full_input_20261103.py').write_text(template)
 print(json.dumps({'archive':str(R/'entry.tar.gz'),'sha256':sha(R/'entry.tar.gz'),'model_sha256':sha(E/'mem_model.sv')}))
if __name__=='__main__':main()
