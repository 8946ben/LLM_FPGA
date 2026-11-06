"""Full-project eight-MiB candidate with scalar control and packed accesses."""
from pathlib import Path
import json,hashlib,tarfile,shutil
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4';BASE='memory_full_loader_small_20261103_r1';NAME='memory_burst_small_20261103_r3'
B=M/'experiments'/BASE;E=M/'experiments'/NAME;R=M/'reports'/NAME;C=M/'experiments/memory_burst_model_20261103_r3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 E.mkdir(exist_ok=True);R.mkdir(exist_ok=True);assert not (R/'PLAN.json').exists()
 for n in ['axi_state.sv','lm_head_v4_partial_proto_subsys_test_sequence_lib.sv','memory_probe_pkg.sv','memory_prefix.sv']:shutil.copy2(B/n,E/n)
 shutil.copy2(C/'mem_model.sv',E/'mem_model.sv');changes=json.loads((B/'CHANGES.json').read_text())
 changes['mem_model']['edits']+=json.loads((C/'MODEL_CHANGES.json').read_text())['edits']
 ref=(B/'reference_model.sv').read_text()
 def edit(a,b):
  nonlocal ref
  assert ref.count(a)==1,a[:100];ref=ref.replace(a,b);changes['reference_model']['edits'].append([a,b])
 edit(' integer err;logic[7:0] got;longint unsigned checksum;',' integer err;logic[7:0] got;logic[7:0] values[$];logic[127:0] packed_word;longint unsigned checksum;')
 old=''' for(int i=0;i<8388608;i++)begin
  err=mem_blk_pages_weights.pages[0].read_one_elem(got,i);
  if(err || got!==((i*17+3)&255)) `uvm_fatal("small","byte mismatch")
  checksum+=got;
 end'''
 new=''' for(int i=0;i<8388608;i+=16)begin
  err=mem_blk_pages_weights.pages[0].read_elems(values,i,16);
  if(err || values.size()!=16) `uvm_fatal("small","bulk read status")
  for(int j=0;j<16;j++)begin
   if(values[j]!==(((i+j)*17+3)&255)) `uvm_fatal("small","byte mismatch")
   checksum+=values[j];
  end
 end'''
 edit(old,new)
 old=' $display("SMALL_FULL_CONTEXT_LOADER_PASS bytes=8388608 repeated_writes=1000000 checksum=%0d",checksum);'
 new=''' for(int i=0;i<62500;i++)begin
  for(int j=0;j<16;j++)packed_word[j*8+:8]=(i*16+j)&255;
  err=mem_blk_pages_weights.pages[0].write_packed16(packed_word,0);
  if(err) `uvm_fatal("small","bulk overwrite status")
 end
 err=mem_blk_pages_weights.pages[0].read_packed16(packed_word,0);
 if(err) `uvm_fatal("small","bulk overwrite readback status")
 for(int j=0;j<16;j++)if(packed_word[j*8+:8]!==((999984+j)&255)) `uvm_fatal("small","bulk overwrite bits")
 lmh_memory_probe_pkg::sample("small_after_bulk_write",1000000);
 $display("BURST_FULL_CONTEXT_PASS bytes=8388608 scalar_writes=1000000 bulk_elements_written=1000000 checksum=%0d",checksum);'''
 edit(old,new);(E/'reference_model.sv').write_text(ref);(E/'CHANGES.json').write_text(json.dumps(changes,indent=2)+'\n')
 shutil.copy2(M/'reports'/BASE/'INDEPENDENT_REVIEW.json',E/'predecessor_review.json')
 runner=(B/'run_startup.py').read_text().replace(BASE,NAME)
 runner=runner.replace("  assert lines.count('SMALL_FULL_CONTEXT_LOADER_PASS bytes=8388608 repeated_writes=1000000 checksum=1069547520')==1", "  assert lines.count('BURST_FULL_CONTEXT_PASS bytes=8388608 scalar_writes=1000000 bulk_elements_written=1000000 checksum=1069547520')==1")
 runner=runner.replace("plan=json.loads((R/'PLAN.json').read_text());guard=plan['guards']", "plan=json.loads((R/'PLAN.json').read_text());guard=plan['guards']\n assert json.loads((E/'predecessor_review.json').read_text())['state']=='PASS_INDEPENDENT_FULL_PROJECT_SMALL_LOADER_ACCESS_DIAGNOSIS'")
 runner=runner.replace('TOOL_PASS_FINITE_PREFIX_AWAITING_INDEPENDENT_REVIEW','TOOL_PASS_BURST_SMALL_AWAITING_INDEPENDENT_REVIEW')
 compile(runner,'run_startup.py','exec');(E/'run_startup.py').write_text(runner)
 p=json.loads((M/'reports'/BASE/'PLAN.json').read_text());p.update(state='FROZEN_BURST_FULL_PROJECT_SMALL_COMPARISON',source_sha256={str(x.relative_to(ROOT)).replace('\\','/'):sha(x) for x in E.iterdir() if x.is_file()},scope='Actual full-project context;8MiB all-byte bulk API read;million scalar writes control then62500 packed writes;time0 stop;not M14 compute qualification')
 (R/'PLAN.json').write_text(json.dumps(p,indent=2)+'\n')
 with tarfile.open(R/'entry.tar.gz','w:gz') as t:
  for x in list(E.iterdir())+[R/'PLAN.json']:t.add(x,arcname=str(x.relative_to(ROOT)))
 oldhash=sha(M/'reports'/BASE/'entry.tar.gz')
 bootstrap=(ROOT/'tools/bootstrap_memory_full_loader_small_20261103.py').read_text().replace(BASE,NAME).replace(oldhash,sha(R/'entry.tar.gz'))
 (ROOT/'tools/bootstrap_memory_burst_small_20261103.py').write_text(bootstrap)
 print(json.dumps({'archive':str(R/'entry.tar.gz'),'sha256':sha(R/'entry.tar.gz')}))
if __name__=='__main__':main()
