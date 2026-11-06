"""One isolated full-DUT initialization + 20000-cycle prefix, never a full call."""
from pathlib import Path
import hashlib,json,tarfile
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4'
NAME='memory_full_startup_20261103_r1';E=M/'experiments'/NAME;R=M/'reports'/NAME
S=M/'reports/memory_growth_diagnosis_20261103_r1/sources'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 E.mkdir(exist_ok=True);R.mkdir(exist_ok=True);assert not (R/'PLAN.json').exists()
 package=r'''`timescale 1ns/1ps
package lmh_memory_probe_pkg;
integer master_ar_seen=0;
function automatic void sample(input string label,input longint amount=0);
 integer pf,rc,rss,vm,anon,file_rss,shared,fd;string line;
 rss=-1;vm=0;anon=0;file_rss=0;shared=0;pf=$fopen("/proc/self/status","r");
 if(!pf)$fatal(1,"memory probe proc open");
 while(!$feof(pf))begin
  rc=$fgets(line,pf);
  if($sscanf(line,"VmRSS: %d kB",rss)==1)continue;
  if($sscanf(line,"VmSize: %d kB",vm)==1)continue;
  if($sscanf(line,"RssAnon: %d kB",anon)==1)continue;
  if($sscanf(line,"RssFile: %d kB",file_rss)==1)continue;
  if($sscanf(line,"RssShmem: %d kB",shared)==1)continue;
 end
 $fclose(pf);if(rss<0)$fatal(1,"memory probe RSS missing");
 fd=$fopen("memory_phases.csv","a");if(!fd)$fatal(1,"memory sample open");
 $fwrite(fd,"%s,%0.0f,%0d,%0d,%0d,%0d,%0d,%0d\n",label,$realtime/1ps,amount,rss,vm,anon,file_rss,shared);$fclose(fd);
 $display("MEMORY_PHASE label=%s time_ps=%0.0f amount=%0d rss_kib=%0d vm_kib=%0d anon_kib=%0d file_kib=%0d shared_kib=%0d",label,$realtime/1ps,amount,rss,vm,anon,file_rss,shared);
endfunction
endpackage
'''
 (E/'memory_probe_pkg.sv').write_text(package)
 # Instrument copied reference model around original, unchanged initialization calls.
 refpath=Path('lm_head_v4_partial_proto_subsystem/lm_head_v4_partial_proto_reference_model.sv')
 ref=(S/refpath).read_text();edits=[]
 def add(old,new):
  nonlocal ref
  assert ref.count(old)==1,old[:100];ref=ref.replace(old,new);edits.append([old,new])
 add('        trans_num_idx= 0;','        lmh_memory_probe_pkg::sample("reference_constructed",0);\n        trans_num_idx= 0;')
 add('    virtual task run_phase(uvm_phase phase);\n        string fpath[$];','    virtual task run_phase(uvm_phase phase);\n        string fpath[$];\n        lmh_memory_probe_pkg::sample("reference_run_enter",0);')
 add('        fpath.push_back(`TV_IN_meta);','        lmh_memory_probe_pkg::sample("control_regions_ready",0);\n        fpath.push_back(`TV_IN_meta);')
 add('        mem_blk_pages_meta.tvinload_pagechk_atinit(fpath, 80591*((128+7)/8), 0);','        lmh_memory_probe_pkg::sample("before_meta_load",1289456);\n        mem_blk_pages_meta.tvinload_pagechk_atinit(fpath, 80591*((128+7)/8), 0);\n        lmh_memory_probe_pkg::sample("after_meta_load",1289456);')
 add('        mem_blk_pages_weights.tvinload_pagechk_atinit(fpath, 34105344*((128+7)/8), 0);','        lmh_memory_probe_pkg::sample("before_weights_load",545685504);\n        mem_blk_pages_weights.tvinload_pagechk_atinit(fpath, 34105344*((128+7)/8), 0);\n        lmh_memory_probe_pkg::sample("after_weights_load",545685504);')
 add('$display("BANK_FULL_INPUT_SENTINEL_PASS checked=1522");','$display("BANK_FULL_INPUT_SENTINEL_PASS checked=1522");\nlmh_memory_probe_pkg::sample("after_1522_sentinels",1522);')
 (E/'reference_model.sv').write_text(ref)
 # Instrument streaming loop every 16MiB, leaving byte/data semantics unchanged.
 model=(S/'file_agent/mem_model.sv').read_text();model_edits=[]
 def mod(old,new):
  nonlocal model
  assert model.count(old)==1,old[:100];model=model.replace(old,new);model_edits.append([old,new])
 mod('        fd=$fopen(path,"r");','        lmh_memory_probe_pkg::sample("stream_before_open",nbytes);\n        fd=$fopen(path,"r");')
 mod('        for(i=0;i<nbytes/16;i=i+1)begin','        lmh_memory_probe_pkg::sample("stream_page_created",nbytes);\n        for(i=0;i<nbytes/16;i=i+1)begin\n            if(i>0 && i%1048576==0)lmh_memory_probe_pkg::sample("stream_progress",i*16);')
 mod('        $fclose(fd);\n        $display("STREAM_LOAD_PASS','        $fclose(fd);\n        lmh_memory_probe_pkg::sample("stream_after_load",nbytes);\n        $display("STREAM_LOAD_PASS')
 (E/'mem_model.sv').write_text(model)
 # Isolated integration of already tested MASTER guard. SLAVE code is untouched.
 state=(S/'axivip/axi_state.sv').read_text()
 old='        axi_transfer trclone;\n        tr.ainfo_rx = 1;'
 new='''        axi_transfer trclone;
        if(cfg.drv_type==MASTER)begin
            if(rq_from_model_num!=0) `uvm_fatal("master_guard","unexpected retained slave responses")
            tr.ainfo_rx=1;tr.expected_read_latency=cfg.clatency.get_rd_lat();
            arq[tr.id].push_back(tr);lmh_memory_probe_pkg::master_ar_seen++;return;
        end
        tr.ainfo_rx = 1;'''
 assert state.count(old)==1;state=state.replace(old,new);(E/'axi_state.sv').write_text(state)
 seqname='lm_head_v4_partial_proto_subsys_test_sequence_lib.sv'
 seq=(S/'svtb'/seqname).read_text();pollold='                                        repeat(20) @(posedge misc_if.clock);'
 pollnew='                                        repeat(2000) @(posedge misc_if.clock);'
 assert seq.count(pollold)==1;seq=seq.replace(pollold,pollnew);(E/seqname).write_text(seq)
 observer=r'''`timescale 1ns/1ps
module lmh_memory_prefix(input wire clk,rst_n,start,done,idle,
 input wire carvalid,carready,crvalid,crready,warvalid,warready,m_arvalid,m_arready);
 bit begun=0;integer clocks=0,control_ar=0,control_r=0,weight_ar=0,meta_ar=0;
 initial lmh_memory_probe_pkg::sample("top_initial",0);
 always @(posedge clk)begin
  if(rst_n)begin
   if(carvalid && carready)control_ar++;
   if(crvalid && crready)control_r++;
   if(warvalid && warready)weight_ar++;
   if(m_arvalid && m_arready)meta_ar++;
   if(!begun && start===1)begin begun=1;clocks=0;lmh_memory_probe_pkg::sample("dut_start",0);end
   else if(begun)begin
    clocks++;
    if(done===1 || idle===1)$fatal(1,"unexpected complete/idle within bounded prefix");
    if(clocks%5000==0)lmh_memory_probe_pkg::sample("running_prefix",clocks);
    if(clocks==20000)begin
     $display("MEMORY_PREFIX_PASS cycles=%0d control_ar=%0d control_r=%0d master_guard_ar=%0d weight_ar=%0d meta_ar=%0d",clocks,control_ar,control_r,lmh_memory_probe_pkg::master_ar_seen,weight_ar,meta_ar);
     $finish;
    end
   end
  end
 end
 initial begin #1000000;$fatal(1,"prefix simulation watchdog");end
endmodule
bind lm_head_v4_partial_proto lmh_memory_prefix memory_prefix_observer(
 .clk(ap_clk),.rst_n(ap_rst_n),.start(ap_start),.done(ap_done),.idle(ap_idle),
 .carvalid(s_axi_control_ARVALID),.carready(s_axi_control_ARREADY),.crvalid(s_axi_control_RVALID),.crready(s_axi_control_RREADY),
 .warvalid(m_axi_weights_ARVALID),.warready(m_axi_weights_ARREADY),.m_arvalid(m_axi_meta_ARVALID),.m_arready(m_axi_meta_ARREADY));
'''
 (E/'memory_prefix.sv').write_text(observer)
 changes={'reference_model':{'original':str(refpath),'original_sha256':sha(S/refpath),'edits':edits},
 'mem_model':{'original':'file_agent/mem_model.sv','original_sha256':sha(S/'file_agent/mem_model.sv'),'edits':model_edits},
 'axi_state':{'original':'axivip/axi_state.sv','original_sha256':sha(S/'axivip/axi_state.sv'),'edits':[[old,new]]},
 'test_sequence':{'original':'svtb/'+seqname,'original_sha256':sha(S/'svtb'/seqname),'edits':[[pollold,pollnew]]}}
 # Reversible edits prove only the declared instrumentation/guard/cadence changed.
 for key,entry in changes.items():
  modified={'reference_model':ref,'mem_model':model,'axi_state':state,'test_sequence':seq}[key]
  for before,after in reversed(entry['edits']):assert modified.count(after)==1;modified=modified.replace(after,before)
  assert modified==(S/entry['original']).read_text()
 (E/'CHANGES.json').write_text(json.dumps(changes,indent=2)+'\n')
 # Runner is a separate source reviewed before upload.
 runner=ROOT/'tools/run_memory_full_startup_20261103.py';assert runner.exists();(E/'run_startup.py').write_bytes(runner.read_bytes())
 plan={'state':'FROZEN_FULL_DUT_STARTUP_AND_FINITE_PREFIX','source_sha256':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in E.iterdir() if p.is_file()},
 'baseline_sources':{str((S/entry['original']).relative_to(S)).replace('\\','/'):entry['original_sha256'] for entry in changes.values()},
 'prefix_cycles':20000,'weights_bytes':545685504,'sentinel_count':1522,
 'guards':{'initial_available_gib':96,'running_available_gib':32,'group_rss_gib':64,'elaborate_seconds':300,'simulate_seconds':1800},
 'full_m14':'NOT_RUN','c_postcheck':'NOT_RUN','board':'NOT_RUN','automatic_next_stage':False,
 'scope':'One actual full-DUT initialization then bounded prefix; original compute RTL/FP32/FIFO and latency classes unchanged; guard/cadence changes random stream identity'}
 (R/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
 with tarfile.open(R/'entry.tar.gz','w:gz') as a:
  for p in list(E.iterdir())+[R/'PLAN.json']:a.add(p,arcname=str(p.relative_to(ROOT)))
 bootstrap=f'''from pathlib import Path
import hashlib,json,subprocess,tarfile
ROOT=Path('/home/zhangben/gpuFpgaLLM_experiments/lm_head_v4_partial_20261024_r1');a=ROOT/'{NAME}.tar.gz'
assert hashlib.sha256(a.read_bytes()).hexdigest()=='{sha(R/'entry.tar.gz')}'
r=ROOT/'module_14_lm_head_v4/reports/{NAME}';assert not (r/'WORKFLOW.json').exists()
assert not list((ROOT/'module_14_lm_head_v4/reports').glob('memory_*/ACTIVE.lock'))
assert not (ROOT/'module_14_lm_head_v4/reports/full_bank_cosim_20261102_r2/ACTIVE.lock').exists()
with tarfile.open(a) as t:
 for m in t.getmembers():
  p=(ROOT/m.name).resolve();assert ROOT in p.parents and m.isfile();data=t.extractfile(m).read()
  if p.exists():assert p.read_bytes()==data
  else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
entry=ROOT/'module_14_lm_head_v4/experiments/{NAME}/run_startup.py'
with (r/'launcher.log').open('w') as f:p=subprocess.Popen(['/home/zhangben/anaconda3/bin/python',str(entry)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
print(json.dumps({{'pid_snapshot':p.pid,'workflow':str(r/'WORKFLOW.json'),'full_m14':'NOT_RUN'}}))
'''
 (ROOT/'tools/bootstrap_memory_full_startup_20261103.py').write_text(bootstrap)
 print(json.dumps({'archive':str(R/'entry.tar.gz'),'sha256':sha(R/'entry.tar.gz')}))
if __name__=='__main__':main()
