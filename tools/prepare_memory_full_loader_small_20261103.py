"""Eight-MiB init-only control in exact full project/reference-model context."""
from pathlib import Path
import json,hashlib,tarfile,shutil
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';BASE='memory_full_startup_20261103_r1';NAME='memory_full_loader_small_20261103_r1'
E=M/'experiments'/NAME;R=M/'reports'/NAME;B=M/'experiments'/BASE
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 E.mkdir(exist_ok=True);R.mkdir(exist_ok=True);assert not (R/'PLAN.json').exists()
 for n in ['mem_model.sv','axi_state.sv','lm_head_v4_partial_proto_subsys_test_sequence_lib.sv','memory_probe_pkg.sv','memory_prefix.sv']:shutil.copy2(B/n,E/n)
 changes=json.loads((B/'CHANGES.json').read_text());ref=(B/'reference_model.sv').read_text()
 def replace(old,new):
  nonlocal ref
  assert ref.count(old)==1,old[:100];ref=ref.replace(old,new);changes['reference_model']['edits'].append([old,new])
 replace('mem_blk_pages_weights.whole_page_size=545685760;','mem_blk_pages_weights.whole_page_size=8388864;')
 replace('lmh_memory_probe_pkg::sample("before_weights_load",545685504);','lmh_memory_probe_pkg::sample("before_weights_load",8388608);')
 replace('mem_blk_pages_weights.tvinload_pagechk_atinit(fpath, 34105344*((128+7)/8), 0);','mem_blk_pages_weights.tvinload_pagechk_atinit(fpath, 524288*((128+7)/8), 0);')
 replace('lmh_memory_probe_pkg::sample("after_weights_load",545685504);','lmh_memory_probe_pkg::sample("after_weights_load",8388608);')
 begin=ref.index('begin : bank_load_preflight');end=ref.index('\nend',ref.index('lmh_memory_probe_pkg::sample("after_1522_sentinels",1522);',begin))+len('\nend')
 block=r'''begin : small_full_context
 integer err;logic[7:0] got;longint unsigned checksum;
 checksum=0;
 if(mem_blk_pages_weights.pages[0].banks.size()!=8 || mem_blk_pages_weights.pages[0].banks[0].mem.size()!=65536 || $bits(mem_blk_pages_weights.pages[0].banks[0].mem[0])!=128) `uvm_fatal("small","bank shape")
 $display("SMALL_BANK_SHAPE banks=8 slots=65536 word_bits=128 flag_bits=%0d",$bits(mem_blk_pages_weights.pages[0].banks[0].IsWr[0]));
 for(int i=0;i<8388608;i++)begin
  err=mem_blk_pages_weights.pages[0].read_one_elem(got,i);
  if(err || got!==((i*17+3)&255)) `uvm_fatal("small","byte mismatch")
  checksum+=got;
 end
 if(checksum!=64'd1069547520) `uvm_fatal("small","checksum")
 lmh_memory_probe_pkg::sample("small_after_full_read",8388608);
 for(int i=0;i<1000000;i++)begin
  err=mem_blk_pages_weights.pages[0].write_one_elem(i&255,0);
  if(err) `uvm_fatal("small","overwrite rejected")
 end
 err=mem_blk_pages_weights.pages[0].read_one_elem(got,0);
 if(err || got!==8'h3f) `uvm_fatal("small","overwrite mismatch")
 lmh_memory_probe_pkg::sample("small_after_repeated_write",1000000);
 $display("SMALL_FULL_CONTEXT_LOADER_PASS bytes=8388608 repeated_writes=1000000 checksum=%0d",checksum);
 $finish;
end'''
 replace(ref[begin:end],block);(E/'reference_model.sv').write_text(ref)
 (E/'CHANGES.json').write_text(json.dumps(changes,indent=2)+'\n')
 runner=(ROOT/'tools/run_memory_full_startup_20261103.py').read_text().replace(BASE,NAME)
 old="  (NEW/'tv').mkdir();(NEW/'tv/cdatafile').symlink_to(OLD.parent/'tv/cdatafile',target_is_directory=True);(NEW/'tv/rtldatafile').mkdir()"
 new='''  (NEW/'tv').mkdir();(NEW/'tv/cdatafile').mkdir();(NEW/'tv/rtldatafile').mkdir()
  private=NEW/'tv/cdatafile';names=['c.lm_head_v4_partial_proto.autotvin_'+n+'.dat' for n in ['weights','canonical_weight','tiled_weight']]
  for p in (OLD.parent/'tv/cdatafile').iterdir():
   if p.name not in names:(private/p.name).symlink_to(p)
  pattern=bytes((i*17+3)&255 for i in range(256));block=''.join('0x'+pattern[i:i+16][::-1].hex()+'\\n' for i in range(0,256,16))
  with (private/names[0]).open('w') as f:
   f.write('[[[runtime]]]\\n[[transaction]] 0\\n')
   for i in range(8388608//256):f.write(block)
   f.write('[[/transaction]]\\n[[[/runtime]]]\\n')
  for n,value in [('canonical_weight',4194304),('tiled_weight',0)]:
   (private/('c.lm_head_v4_partial_proto.autotvin_'+n+'.dat')).write_text('[[[runtime]]]\\n[[transaction]] 0\\n0x%016x\\n[[/transaction]]\\n[[[/runtime]]]\\n'%value)'''
 assert runner.count(old)==1;runner=runner.replace(old,new)
 runner=runner.replace("assert sha(tv)==fullplan['full_tv_sha256']","assert sha(tv)==plan['input_tv_sha256']")
 runner=runner.replace("  assert any(x=='BANK_FULL_INPUT_SENTINEL_PASS checked=1522' for x in lines)\n  assert sum(x.startswith('MEMORY_PREFIX_PASS cycles=20000 ') for x in lines)==1", "  assert lines.count('SMALL_FULL_CONTEXT_LOADER_PASS bytes=8388608 repeated_writes=1000000 checksum=1069547520')==1")
 runner=runner.replace("for name in ['memory_phases.csv','weights_readback.csv','stage_profile.csv']","for name in ['memory_phases.csv']")
 runner=runner.replace('GROUP_RSS_OVER_64GIB','GROUP_RSS_OVER_LIMIT')
 compile(runner,'run_startup.py','exec');(E/'run_startup.py').write_text(runner)
 pattern=bytes((i*17+3)&255 for i in range(256));block=''.join('0x'+pattern[i:i+16][::-1].hex()+'\n' for i in range(0,256,16)).encode()
 h=hashlib.sha256(b'[[[runtime]]]\n[[transaction]] 0\n')
 for i in range(8388608//256):h.update(block)
 h.update(b'[[/transaction]]\n[[[/runtime]]]\n')
 base=json.loads((M/'reports'/BASE/'PLAN.json').read_text())
 plan={'state':'FROZEN_FULL_PROJECT_SMALL_LOADER_CONTEXT','source_sha256':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in E.iterdir() if p.is_file()},
 'baseline_sources':base['baseline_sources'],'input_tv_sha256':h.hexdigest(),'bytes':8388608,'repeated_writes':1000000,
 'guards':{'initial_available_gib':96,'running_available_gib':32,'group_rss_gib':8,'elaborate_seconds':300,'simulate_seconds':300},
 'scope':'Actual full-project/reference-model path; private eight-MiB pattern replaces weights; stops before any DUT clock progress; not valid compute weights',
 'full_m14':'NOT_RUN','board':'NOT_RUN','automatic_next_stage':False}
 (R/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
 with tarfile.open(R/'entry.tar.gz','w:gz') as a:
  for p in list(E.iterdir())+[R/'PLAN.json']:a.add(p,arcname=str(p.relative_to(ROOT)))
 template=(ROOT/'tools/bootstrap_memory_full_startup_20261103.py').read_text().replace(BASE,NAME)
 template=template.replace('d6571c68518e8381f2c6e55c4da819088a8a8cfc0e4e2abb5451fb93f7d8acc9',sha(R/'entry.tar.gz'))
 (ROOT/'tools/bootstrap_memory_full_loader_small_20261103.py').write_text(template)
 print(json.dumps({'archive':str(R/'entry.tar.gz'),'sha256':sha(R/'entry.tar.gz')}))
if __name__=='__main__':main()
