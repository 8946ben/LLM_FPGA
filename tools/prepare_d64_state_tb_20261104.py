"""Prepare a persistent full-DUT testbench; no SV compile, upload or EDA launch."""
from pathlib import Path
import datetime,hashlib,json,re
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'module_14_lm_head_v4'
NAME='d64_state_tb_20261104_r1';E=M/'experiments'/NAME;R=M/'reports'/NAME
F=M/'reports/d64_state_fixtures_20261104_r2';FE=M/'experiments/d64_state_fixtures_20261104_r2'
S=M/'reports/memory_growth_diagnosis_20261103_r1/sources'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    manifest=json.loads((F/'MANIFEST.json').read_text());controls=json.loads((FE/'control_sequences.json').read_text())
    audit=json.loads((F/'INDEPENDENT_PREPARATION_REVIEW.json').read_text())
    assert audit['state']=='PASS_INDEPENDENT_PREPARATION_ONLY' and audit['cases']==12
    assert audit['manifest_sha256']==sha(F/'MANIFEST.json') and audit['control_sha256']==sha(FE/'control_sequences.json')
    assert not E.exists() and not R.exists();E.mkdir();R.mkdir()
    top=S/'lm_head_v4_partial_proto.v';text=top.read_text()
    parameters={k:int(v) for k,v in re.findall(r'\bparameter\s+(C_[A-Z0-9_]+)\s*=\s*(\d+)\s*;',text)}
    parameters.update(C_S_AXI_CONTROL_WSTRB_WIDTH=4,C_S_AXI_WSTRB_WIDTH=4,C_M_AXI_META_WSTRB_WIDTH=16,C_M_AXI_WEIGHTS_WSTRB_WIDTH=16,C_M_AXI_WSTRB_WIDTH=4)
    declarations=[];ports=[]
    for direction,width,name in re.findall(r'^(input|output)\s*(\[[^\]]+\])?\s*(\w+)\s*;',text,re.M):
        for token in re.findall(r'\bC_[A-Z0-9_]+\b',width):
            assert token in parameters,token;width=width.replace(token,str(parameters[token]))
        declarations.append('logic '+width+' '+name+';');ports.append((direction,name))
    port_list=re.search(r'module lm_head_v4_partial_proto\s*\((.*?)\);',text,re.S).group(1)
    assert set(re.findall(r'\b\w+\b',port_list))=={name for _,name in ports}
    assert len({name for _,name in ports})==len(ports)
    wiring='lm_head_v4_partial_proto dut(\n'+',\n'.join(' .'+name+'('+name+')' for _,name in ports)+'\n);\n'
    native=[]
    required=['AWVALID','AWREADY','AWADDR','AWID','AWLEN','AWSIZE','AWBURST','WVALID','WREADY','WDATA','WSTRB','WLAST',
              'BVALID','BREADY','BID','BRESP','ARVALID','ARREADY','ARADDR','ARID','ARLEN','ARSIZE','ARBURST','RVALID','RREADY','RDATA','RLAST','RID','RRESP']
    for region,n,storage,readonly in [('meta',80591,80592,0),('weights',34105344,34105344,1)]:
        native.append('d64_native_memory #(.N(%d),.STORAGE_N(%d),.READ_ONLY(%d)) mem_%s(\n .clk(ap_clk),.rst(!ap_rst_n),\n%s\n);\n'%(n,storage,readonly,region,',\n'.join(' .'+field+'(m_axi_'+region+'_'+field+')' for field in required)))
    header='''`timescale 1ns/1ps
// PREPARED_NOT_SIMULATED. Full unchanged compute RTL, persistent DUT and memories.
// No DUT result is supplied by a reference file. Expectations are checked after return.
module d64_state_tb;
'''
    body=r'''
string root,weight_tv,out_dir;
integer cycle=0,frame=-1,ctrl_fd,metrics_fd,ar_count=0,aw_count=0,raw_write_beats=0;
integer starts=0,dones=0,canonical_read_requests=0,current_debug=1;
bit active_case=0,seen_busy=0,seen_done=0,previous_start=0;
longint unsigned ip_start_cycle=0,ip_done_cycle=0;
file_agent_pkg::mem_model_pages#(128,8) weight_loader;
logic[127:0] word_value;
logic[7:0] byte_value;
integer rc,fd,byte_in;
localparam integer META_BYTES=24368,WS_BEATS=79068;
localparam logic[127:0] GUARD=128'hfedcba98765432100123456789abcdef;
initial ap_clk=0;always #2.5 ap_clk=~ap_clk;
always @(posedge ap_clk)if(ap_rst_n)begin
 cycle=cycle+1;
 if(dut.ap_start===1'b1&&!previous_start)begin
  if(!active_case)$fatal(1,"STATE_START_OUTSIDE_CASE");starts++;ip_start_cycle=cycle;
 end
 previous_start=(dut.ap_start===1'b1);
 if(active_case&&dut.ap_idle===1'b0)seen_busy=1;
 if(active_case&&seen_busy&&dut.ap_done===1'b1&&!seen_done)begin
  dones++;seen_done=1;ip_done_cycle=cycle;
 end
 if(m_axi_weights_ARVALID&&m_axi_weights_ARREADY)begin
  if(!active_case)$fatal(1,"STATE_WEIGHT_AR_OUTSIDE_CASE");
  ar_count++;
  if(m_axi_weights_ARADDR>=273416192)canonical_read_requests++;
 end
 if(m_axi_meta_AWVALID&&m_axi_meta_AWREADY)begin
  if(!active_case||m_axi_meta_AWADDR<META_BYTES)$fatal(1,"STATE_META_WRITE_OUTSIDE_WORKSPACE");
  aw_count++;
 end
 if(m_axi_meta_WVALID&&m_axi_meta_WREADY)begin
  if(mem_meta.wa<META_BYTES)$fatal(1,"STATE_METADATA_OVERWRITE");
  if(mem_meta.wa>=META_BYTES+76997*16 && mem_meta.wa<META_BYTES+79052*16 && m_axi_meta_WSTRB!=0)begin
   raw_write_beats++;
   if(current_debug==0)$fatal(1,"STATE_PRODUCTION_RAW_WRITE");
  end
 end
end
task automatic ctrl_read(input logic[7:0] address,output logic[31:0] value);
 integer waited;
 @(negedge ap_clk);s_axi_control_ARADDR=address;s_axi_control_ARVALID=1;
 waited=0;
 do begin @(posedge ap_clk);waited++;if(waited>10000)$fatal(1,"STATE_CONTROL_AR_TIMEOUT");end while(s_axi_control_ARREADY!==1'b1);
 @(negedge ap_clk);s_axi_control_ARVALID=0;s_axi_control_RREADY=1;
 waited=0;
 do begin @(posedge ap_clk);waited++;if(waited>10000)$fatal(1,"STATE_CONTROL_R_TIMEOUT");end while(s_axi_control_RVALID!==1'b1);
 value=s_axi_control_RDATA;
 if(s_axi_control_RRESP!==2'b00||$isunknown(value))$fatal(1,"STATE_CONTROL_READ_INVALID");
 $fwrite(ctrl_fd,"R,%0d,%0d,%02h,%08h
",frame,cycle,address,value);
 @(negedge ap_clk);s_axi_control_RREADY=0;
endtask
task automatic ctrl_write(input logic[7:0] address,input logic[31:0] value);
 integer aw_wait,w_wait,b_wait;
 @(negedge ap_clk);s_axi_control_BREADY=1;
 fork
  begin
   s_axi_control_AWADDR=address;s_axi_control_AWVALID=1;aw_wait=0;
   do begin @(posedge ap_clk);aw_wait++;if(aw_wait>10000)$fatal(1,"STATE_CONTROL_AW_TIMEOUT");end while(s_axi_control_AWREADY!==1'b1);
   @(negedge ap_clk);s_axi_control_AWVALID=0;
  end
  begin
   s_axi_control_WDATA=value;s_axi_control_WSTRB=4'hf;s_axi_control_WVALID=1;w_wait=0;
   do begin @(posedge ap_clk);w_wait++;if(w_wait>10000)$fatal(1,"STATE_CONTROL_W_TIMEOUT");end while(s_axi_control_WREADY!==1'b1);
   @(negedge ap_clk);s_axi_control_WVALID=0;
  end
 join
 b_wait=0;
 do begin @(posedge ap_clk);b_wait++;if(b_wait>10000)$fatal(1,"STATE_CONTROL_B_TIMEOUT");end while(s_axi_control_BVALID!==1'b1);
 if(s_axi_control_BRESP!==2'b00)$fatal(1,"STATE_CONTROL_WRITE_INVALID");
 $fwrite(ctrl_fd,"W,%0d,%0d,%02h,%08h
",frame,cycle,address,value);
 @(negedge ap_clk);s_axi_control_BREADY=0;
endtask
task automatic write_check(input logic[7:0] address,input logic[31:0] value);
 logic[31:0] got;
 ctrl_write(address,value);ctrl_read(address,got);
 if(got!==value)$fatal(1,"STATE_PARAMETER_READBACK address=%h",address);
endtask
task automatic load_meta(input string relative_path);
 integer h,c,e;logic[127:0] v;
 if(!mem_meta.idle||!mem_weights.idle)$fatal(1,"STATE_MUTATE_WHILE_BUS_ACTIVE");
 h=$fopen({root,"/",relative_path},"rb");if(!h)$fatal(1,"STATE_META_OPEN");
 for(integer beat=0;beat<1523;beat++)begin
  for(integer lane=0;lane<16;lane++)begin
   c=$fgetc(h);if(c<0)$fatal(1,"STATE_META_SHORT");v[lane*8+:8]=c;
  end
  e=mem_meta.storage.write_packed16(v,beat*16);if(e)$fatal(1,"STATE_META_LOAD_RANGE");
 end
 if($fgetc(h)!=-1)$fatal(1,"STATE_META_LONG");$fclose(h);
endtask
task automatic dump_memory(input string label,input string suffix);
 integer h,e;logic[127:0] v;
 if(!mem_meta.idle||!mem_weights.idle)$fatal(1,"STATE_DUMP_WHILE_BUS_ACTIVE");
 h=$fopen({out_dir,"/",label,".",suffix,".hex"},"w");if(!h)$fatal(1,"STATE_DUMP_OPEN");
 for(integer beat=0;beat<80592;beat++)begin
  e=mem_meta.storage.read_packed16(v,beat*16);if(e)$fatal(1,"STATE_DUMP_RANGE");
  $fwrite(h,"%032h
",v);
 end
 $fclose(h);
 e=mem_meta.storage.read_packed16(v,80591*16);if(e||v!==GUARD)$fatal(1,"STATE_END_GUARD_CHANGED");
endtask
task automatic mutate_weight(input integer offset,input logic[15:0] expect_value,input logic[15:0] new_value);
 integer e;logic[7:0] lo,hi;
 if(!mem_meta.idle||!mem_weights.idle)$fatal(1,"STATE_WEIGHT_MUTATE_ACTIVE");
 e=mem_weights.storage.read_one_elem(lo,offset);e+=mem_weights.storage.read_one_elem(hi,offset+1);
 if(e||{hi,lo}!==expect_value)$fatal(1,"STATE_WEIGHT_MUTATION_ORIGINAL");
 e=mem_weights.storage.write_one_elem(new_value[7:0],offset);
 e+=mem_weights.storage.write_one_elem(new_value[15:8],offset+1);
 if(e)$fatal(1,"STATE_WEIGHT_MUTATION_RANGE");
endtask
task automatic run_case(input integer index,input string label,input string input_path,
 input integer debug_value,input integer capacity,input integer expected_status,
 input logic[31:0] expected_token,input logic[31:0] expected_score,input integer expected_k,input logic[31:0] expected_crc,
 input integer injection_offset,input logic[15:0] original_weight);
 logic[31:0] value,status,token,score,count,crc,preview_lo,preview_hi;
 integer first_starts,first_dones,first_mrd,first_mwr,first_wrd,first_canonical,first_raw,waited;
 longint unsigned call_begin,call_end;
 frame=index;current_debug=debug_value;seen_busy=0;seen_done=0;
 load_meta(input_path);dump_memory(label,"before");
 if(injection_offset>=0)mutate_weight(injection_offset,original_weight,16'h7fc0);
 ctrl_read(0,value);
 if((value&32'h85)!=4)$fatal(1,"STATE_NOT_IDLE_BEFORE_CASE");
 for(integer field=0;field<6;field++)begin
  ctrl_read(field==5?8'ha8:8'h54+16*field,value);
  ctrl_read(field==5?8'ha8:8'h54+16*field,value);
  if(value!==0)$fatal(1,"STATE_STALE_OUTPUT_VALID");
 end
 write_check(8'h10,0);write_check(8'h14,0);write_check(8'h1c,0);write_check(8'h20,0);
 write_check(8'h28,273416192);write_check(8'h2c,0);write_check(8'h34,META_BYTES);write_check(8'h38,0);
 write_check(8'h40,capacity);write_check(8'h48,debug_value);
 first_starts=starts;first_dones=dones;first_mrd=mem_meta.rdbeats;first_mwr=mem_meta.wrbeats;
 first_wrd=mem_weights.rdbeats;first_canonical=canonical_read_requests;first_raw=raw_write_beats;
 active_case=1;call_begin=cycle;ctrl_write(0,1);waited=0;
 do begin
  ctrl_read(0,value);waited++;
  if(waited>500000)$fatal(1,"STATE_CASE_DONE_TIMEOUT");
  if(!value[1])repeat(64)@(negedge ap_clk);
 end while(value[1]!==1'b1);
 call_end=cycle;
 if(starts!=first_starts+1||dones!=first_dones+1||!seen_busy||!seen_done)$fatal(1,"STATE_REAL_CALL_NOT_OBSERVED");
 for(integer field=0;field<6;field++)begin
  ctrl_read(field==5?8'ha8:8'h54+16*field,value);if(value!==1)$fatal(1,"STATE_MISSING_OUTPUT_VALID");
  ctrl_read(field==5?8'ha8:8'h54+16*field,value);if(value!==0)$fatal(1,"STATE_OUTPUT_VALID_NOT_CLEARED");
 end
 ctrl_read(8'h50,status);ctrl_read(8'h60,token);ctrl_read(8'h70,score);ctrl_read(8'h80,count);
 ctrl_read(8'h90,crc);ctrl_read(8'ha0,preview_lo);ctrl_read(8'ha4,preview_hi);
 if(status!==expected_status||token!==expected_token||score!==expected_score||count!==expected_k||crc!==expected_crc)
  $fatal(1,"STATE_OUTPUT_MISMATCH case=%s status=%h token=%h score=%h K=%h crc=%h",label,status,token,score,count,crc);
 if({preview_hi,preview_lo}!==(expected_status==0?64'd1220608:64'd0))$fatal(1,"STATE_PREVIEW_COUNT_MISMATCH");
 ctrl_read(0,value);if(value[1]!==0||value[0]!==0||value[7]!==0||value[2]!==1)$fatal(1,"STATE_DONE_NOT_CLEARED_OR_NOT_IDLE");
 waited=0;
 while(!mem_meta.idle||!mem_weights.idle)begin
  @(negedge ap_clk);waited++;if(waited>10000)$fatal(1,"STATE_BUS_DRAIN_TIMEOUT");
 end
 @(negedge ap_clk);active_case=0;
 if(expected_status==0&&mem_weights.rdbeats-first_wrd<=1220608)$fatal(1,"STATE_EXACT_WEIGHT_READ_MISSING");
 if(expected_status!=0&&canonical_read_requests!=first_canonical)$fatal(1,"STATE_ERROR_READ_CANONICAL");
 if(index>=5&&index<=9)begin
  if(mem_weights.rdbeats!=first_wrd||mem_meta.wrbeats!=first_mwr)$fatal(1,"STATE_EARLY_ERROR_SIDE_EFFECT");
  if(index<=6&&mem_meta.rdbeats!=first_mrd)$fatal(1,"STATE_BAD_PARAMETER_READ_META");
 end
 if(debug_value==0&&raw_write_beats!=first_raw)$fatal(1,"STATE_PRODUCTION_RAW_BEATS");
 if(injection_offset>=0)mutate_weight(injection_offset,16'h7fc0,original_weight);
 dump_memory(label,"after");
 $fwrite(metrics_fd,"%0d,%s,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d
",index,label,debug_value,status,token,score,count,crc,ip_done_cycle-ip_start_cycle,call_end-call_begin,
 mem_meta.rdbeats-first_mrd,mem_meta.wrbeats-first_mwr,mem_weights.rdbeats-first_wrd,canonical_read_requests-first_canonical,raw_write_beats-first_raw,starts);
 $fflush(metrics_fd);$fflush(ctrl_fd);
 $display("STATE_CASE_RETURNED index=%0d label=%s status=%0d K=%0d ip_cycles=%0d",index,label,status,count,ip_done_cycle-ip_start_cycle);
endtask
initial begin
 ap_rst_n=0;
 s_axi_control_AWVALID=0;s_axi_control_AWADDR=0;s_axi_control_WVALID=0;s_axi_control_WDATA=0;s_axi_control_WSTRB=0;
 s_axi_control_ARVALID=0;s_axi_control_ARADDR=0;s_axi_control_RREADY=0;s_axi_control_BREADY=0;
 m_axi_meta_RUSER=0;m_axi_meta_BUSER=0;m_axi_weights_RUSER=0;m_axi_weights_BUSER=0;
 if(!$value$plusargs("ROOT=%s",root)||!$value$plusargs("WEIGHTS_TV=%s",weight_tv)||!$value$plusargs("OUT=%s",out_dir))$fatal(1,"STATE_PATH_ARGUMENTS_REQUIRED");
 ctrl_fd=$fopen({out_dir,"/control_trace.csv"},"w");metrics_fd=$fopen({out_dir,"/case_metrics.csv"},"w");
 if(!ctrl_fd||!metrics_fd)$fatal(1,"STATE_RESULTS_OPEN");
 $fwrite(metrics_fd,"case,label,debug,status,token,score,K,crc,ip_cycles,control_call_cycles,meta_reads,meta_writes,weight_reads,canonical_requests,raw_write_beats,total_starts
");
 wait(mem_meta.initialized&&mem_weights.initialized);
 weight_loader=new("real_original_full_weight_tv");weight_loader.tvinload_hex128_single(weight_tv,545685504,0);
 if(weight_loader.pages.size()!=1)$fatal(1,"STATE_WEIGHT_PAGE_COUNT");mem_weights.storage=weight_loader.pages[0];
 `include "state_weight_sentinels.svh"
 for(integer beat=0;beat<80591;beat++)begin
  rc=mem_meta.storage.write_packed16(128'ha5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5,beat*16);
  if(rc)$fatal(1,"STATE_INITIAL_META_RANGE");
 end
 rc=mem_meta.storage.write_packed16(GUARD,80591*16);if(rc)$fatal(1,"STATE_INITIAL_GUARD_RANGE");
 repeat(8)@(negedge ap_clk);ap_rst_n=1;repeat(8)@(negedge ap_clk);
 `include "state_schedule.svh"
 if(starts!=12||dones!=12||!mem_meta.idle||!mem_weights.idle)$fatal(1,"STATE_FINAL_COUNTS");
 $fclose(ctrl_fd);$fclose(metrics_fd);$display("D64_STATE_SUITE_RETURNED calls=12 no_inter_call_reset=1");$finish;
end
initial begin #2000000000;$fatal(1,"STATE_SIMULATION_WATCHDOG");end
endmodule
'''
    # Restore explicit escaped newlines in SV format strings (not literal source LF).
    body=body.replace('\n",','\\n",').replace('\n");','\\n");')
    (E/'d64_state_tb.sv').write_text(header+'\n'.join(declarations)+'\n'+wiring+'\n'.join(native)+body)
    schedule=[]
    for s,sequence in zip(manifest['scenarios'],controls['sequences'],strict=True):
        expected=s['expected'];mutation=next((x for x in s['mutations'] if x['region']=='weights'),None)
        off=mutation['offset_bytes'] if mutation else -1
        original=int.from_bytes(bytes.fromhex(mutation['expected_original_hex']),'little') if mutation else 0
        schedule.append('run_case(%d,"%s","%s",%d,%d,%d,32\'h%08x,32\'h%08x,%d,32\'h%08x,%d,16\'h%04x);'%(
            s['case_index'],s['label'],s['input_path'],s['debug'],s['capacity'],expected['expected_status'],expected['token'],expected['score_bits'],expected['k'],expected['crc'],off,original))
    (E/'state_schedule.svh').write_text('\n'.join(schedule)+'\n')
    old_preflight=M/'experiments/sim_memory_bank_20261026/weights_preflight.svh'
    addresses=list(map(int,re.findall(r'byte mismatch at (\d+)',old_preflight.read_text())));assert len(addresses)==1522
    tiled=M/'reports/layout_topk_20261024_r1/assets/tiled_W_B1024.bin';canonical=ROOT/'artifacts/module14_v2_assets/shared_vocab_weight.bf16.bin'
    sentinel=[]
    with tiled.open('rb') as a,canonical.open('rb') as b:
        for addr in addresses:
            stream,offset=(a,addr) if addr<273416192 else (b,addr-273416192);stream.seek(offset);value=stream.read(1)[0]
            sentinel.append("rc=mem_weights.storage.read_one_elem(byte_value,%d);if(rc||byte_value!==8'h%02x)$fatal(1,\"STATE_WEIGHT_SENTINEL addr=%d\");"%(addr,value,addr))
    sentinel.append('$display("STATE_WEIGHT_SENTINEL_PASS checked=1522");')
    (E/'state_weight_sentinels.svh').write_text('\n'.join(sentinel)+'\n')
    plan=dict(state='PREPARED_FULL_DUT_STATE_TESTBENCH_NOT_COMPILED',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        sources={p.relative_to(ROOT).as_posix():sha(p) for p in [top,E/'d64_state_tb.sv',E/'state_schedule.svh',E/'state_weight_sentinels.svh',old_preflight]},
        fixture_manifest_sha256=sha(F/'MANIFEST.json'),fixture_control_sha256=sha(FE/'control_sequences.json'),fixture_review_sha256=sha(F/'INDEPENDENT_PREPARATION_REVIEW.json'),
        port_count=len(ports),scenarios=12,reset_count_in_scheduled_cases=0,weight_initializations=1,
        runtime_condition='Draft single-outstanding registered native model. No inserted random delay; not MIG or physical FPGA performance.',
        pending=['SV compilation and independent structural/control review','Current strong-stress complete numeric/FIFO PASS',
                 'New native AXI model actual gate PASS','Bounded suite runner and all actual compiled-source SHA',
                 'Every actual array/production preservation/error side effect independently audited','Normal-response cycles interpreted only after correctness'],
        requested_outputs=['Control request/readback trace','All12 before/after logical meta/workspace and end-guard images','Actual start/done counts','Per-call IP/control cycles and AXI counts','Unmodified passive stage_observer/bind'],
        normal_timing_claim='NONE; prepared code only',eda='NOT_RUN',board='NOT_RUN',automatic_next_stage=False)
    (R/'PREPARATION.json').write_text(json.dumps(plan,indent=2)+'\n')
    (R/'RESUME.md').write_text('PREPARED_NOT_COMPILED. Persistent full-DUT12-case bench draft only. No runner/EDA started. Current strong-delay full call remains sole EDA job. Require its independent PASS and actual new-model gate PASS, then independently review this bench before manually freezing bounded execution.\n')
    print(json.dumps(dict(state=plan['state'],ports=len(ports),cases=12,eda='NOT_RUN'),indent=2))
if __name__=='__main__':main()
