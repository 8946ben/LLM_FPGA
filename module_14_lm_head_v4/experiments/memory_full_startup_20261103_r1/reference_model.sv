//==============================================================
//Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2022.2 (64-bit)
//Tool Version Limit: 2019.12
//Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
//==============================================================

`ifndef LM_HEAD_V4_PARTIAL_PROTO_REFERENCE_MODEL_SV
`define LM_HEAD_V4_PARTIAL_PROTO_REFERENCE_MODEL_SV
typedef class lm_head_v4_partial_proto_reference_model;
class memaccess_axi_state_cbs extends axi_pkg::axi_state_cbs;
    lm_head_v4_partial_proto_reference_model refm;
    string memid;
    //function new(string name="memaccess_axi_state_cbs");
    //    super.new(name);
    //endfunction
    virtual function void memmodel_read_fromar(ref logic[7:0] data[$], input longint addr, input longint len);
        if(memid=="meta") refm.mem_blk_pages_meta.read_elems_pipepage(data, addr, len);
        if(memid=="weights") refm.mem_blk_pages_weights.read_elems_pipepage(data, addr, len);
    endfunction
endclass

class lm_head_v4_partial_proto_reference_model extends uvm_component;
`define TV_IN_meta "../tv/cdatafile/c.lm_head_v4_partial_proto.autotvin_meta.dat"
`define TV_OUT_meta "../tv/rtldatafile/rtl.lm_head_v4_partial_proto.autotvout_meta.dat"
`define TV_IN_OFFSET_meta_offset "../tv/cdatafile/c.lm_head_v4_partial_proto.autotvin_meta_offset.dat"
`define TV_IN_OFFSET_workspace "../tv/cdatafile/c.lm_head_v4_partial_proto.autotvin_workspace.dat"
`define TV_IN_weights "../tv/cdatafile/c.lm_head_v4_partial_proto.autotvin_weights.dat"
`define TV_OUT_weights "../tv/rtldatafile/rtl.lm_head_v4_partial_proto.autotvout_weights.dat"
`define TV_IN_OFFSET_tiled_weight "../tv/cdatafile/c.lm_head_v4_partial_proto.autotvin_tiled_weight.dat"
`define TV_IN_OFFSET_canonical_weight "../tv/cdatafile/c.lm_head_v4_partial_proto.autotvin_canonical_weight.dat"
`define TV_IN_meta_offset "../tv/cdatafile/c.lm_head_v4_partial_proto.autotvin_meta_offset.dat"
`define TV_OUT_meta_offset ""
`define TV_IN_tiled_weight "../tv/cdatafile/c.lm_head_v4_partial_proto.autotvin_tiled_weight.dat"
`define TV_OUT_tiled_weight ""
`define TV_IN_canonical_weight "../tv/cdatafile/c.lm_head_v4_partial_proto.autotvin_canonical_weight.dat"
`define TV_OUT_canonical_weight ""
`define TV_IN_workspace "../tv/cdatafile/c.lm_head_v4_partial_proto.autotvin_workspace.dat"
`define TV_OUT_workspace ""
`define TV_IN_capacity_beats "../tv/cdatafile/c.lm_head_v4_partial_proto.autotvin_capacity_beats.dat"
`define TV_OUT_capacity_beats ""
`define TV_IN_debug "../tv/cdatafile/c.lm_head_v4_partial_proto.autotvin_debug.dat"
`define TV_OUT_debug ""
`define TV_IN_status ""
`define TV_OUT_status "../tv/rtldatafile/rtl.lm_head_v4_partial_proto.autotvout_status.dat"
`define TV_IN_token ""
`define TV_OUT_token "../tv/rtldatafile/rtl.lm_head_v4_partial_proto.autotvout_token.dat"
`define TV_IN_score_bits ""
`define TV_OUT_score_bits "../tv/rtldatafile/rtl.lm_head_v4_partial_proto.autotvout_score_bits.dat"
`define TV_IN_candidate_count ""
`define TV_OUT_candidate_count "../tv/rtldatafile/rtl.lm_head_v4_partial_proto.autotvout_candidate_count.dat"
`define TV_IN_output_crc ""
`define TV_OUT_output_crc "../tv/rtldatafile/rtl.lm_head_v4_partial_proto.autotvout_output_crc.dat"
`define TV_IN_preview_read_beats ""
`define TV_OUT_preview_read_beats "../tv/rtldatafile/rtl.lm_head_v4_partial_proto.autotvout_preview_read_beats.dat"
    bit  read_data_finish_control;
    bit  write_data_finish_control;
    event allaxilite_read_data_finish;
    event allaxilite_write_data_finish;
    event write_start_finish;
    int trans_num_total = 1;
    int trans_num_idx;
    int ap_done_cnt=1;
    event dut2tb_ap_ready;
    event dut2tb_ap_done;
    event ap_ready_for_nexttrans;
    event ap_done_for_nexttrans;
    event finish;
    lm_head_v4_partial_proto_config lm_head_v4_partial_proto_cfg;
    virtual interface misc_interface misc_if;

    mem_model_pages_with_diffofst#(128,8) mem_blk_pages_meta;
    int blk_id_meta = 0;
    memaccess_axi_state_cbs axi_memaccess_cb_meta;

    mem_model_pages_with_diffofst#(128,8) mem_blk_pages_weights;
    int blk_id_weights = 0;
    memaccess_axi_state_cbs axi_memaccess_cb_weights;

    mem_model_pages#(32,8) mem_blk_pages_control_capacity_beats;
    mem_model_pages#(32,8) mem_blk_pages_control_debug;
    mem_model_pages#(32,8) mem_blk_pages_control_status;
    mem_model_pages#(32,8) mem_blk_pages_control_token;
    mem_model_pages#(32,8) mem_blk_pages_control_score_bits;
    mem_model_pages#(32,8) mem_blk_pages_control_candidate_count;
    mem_model_pages#(32,8) mem_blk_pages_control_output_crc;
    mem_model_pages#(64,8) mem_blk_pages_control_preview_read_beats;
    
    `uvm_component_utils_begin(lm_head_v4_partial_proto_reference_model)
        `uvm_field_int (trans_num_idx, UVM_DEFAULT)
    `uvm_component_utils_end

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if(!uvm_config_db#(virtual misc_interface)::get(this, "", "misc_if", misc_if))
            `uvm_fatal(this.get_full_name(), "No misc_if from high level")
        axi_memaccess_cb_meta = new;
        axi_memaccess_cb_meta.refm = this;
        axi_memaccess_cb_meta.memid = "meta";
        axi_memaccess_cb_weights = new;
        axi_memaccess_cb_weights.refm = this;
        axi_memaccess_cb_weights.memid = "weights";
    endfunction

    function new (string name = "", uvm_component parent = null);
        super.new (name, parent);
        lmh_memory_probe_pkg::sample("reference_constructed",0);
        trans_num_idx= 0;
    endfunction

    virtual task run_phase(uvm_phase phase);
        string fpath[$];
        lmh_memory_probe_pkg::sample("reference_run_enter",0);
misc_if.dut2tb_ap_done = 0;

        fpath.push_back(`TV_IN_capacity_beats);
        mem_blk_pages_control_capacity_beats = mem_model_pages#(32,8)::type_id::create("mem_blk_pages_control_capacity_beats");
        mem_blk_pages_control_capacity_beats.tvinload_pagechk_atinit(fpath, 1*((32+7)/8), 0, 64);
        fpath.delete;


        fpath.push_back(`TV_IN_debug);
        mem_blk_pages_control_debug = mem_model_pages#(32,8)::type_id::create("mem_blk_pages_control_debug");
        mem_blk_pages_control_debug.tvinload_pagechk_atinit(fpath, 1*((32+7)/8), 0, 72);
        fpath.delete;


        mem_blk_pages_control_status = mem_model_pages#(32,8)::type_id::create("mem_blk_pages_control_status");
        mem_blk_pages_control_status.init_pages(trans_num_total, 1*((32+7)/8), 80);
        mem_blk_pages_control_status.tvoutdump_atinit(`TV_OUT_status);


        mem_blk_pages_control_token = mem_model_pages#(32,8)::type_id::create("mem_blk_pages_control_token");
        mem_blk_pages_control_token.init_pages(trans_num_total, 1*((32+7)/8), 96);
        mem_blk_pages_control_token.tvoutdump_atinit(`TV_OUT_token);


        mem_blk_pages_control_score_bits = mem_model_pages#(32,8)::type_id::create("mem_blk_pages_control_score_bits");
        mem_blk_pages_control_score_bits.init_pages(trans_num_total, 1*((32+7)/8), 112);
        mem_blk_pages_control_score_bits.tvoutdump_atinit(`TV_OUT_score_bits);


        mem_blk_pages_control_candidate_count = mem_model_pages#(32,8)::type_id::create("mem_blk_pages_control_candidate_count");
        mem_blk_pages_control_candidate_count.init_pages(trans_num_total, 1*((32+7)/8), 128);
        mem_blk_pages_control_candidate_count.tvoutdump_atinit(`TV_OUT_candidate_count);


        mem_blk_pages_control_output_crc = mem_model_pages#(32,8)::type_id::create("mem_blk_pages_control_output_crc");
        mem_blk_pages_control_output_crc.init_pages(trans_num_total, 1*((32+7)/8), 144);
        mem_blk_pages_control_output_crc.tvoutdump_atinit(`TV_OUT_output_crc);


        mem_blk_pages_control_preview_read_beats = mem_model_pages#(64,8)::type_id::create("mem_blk_pages_control_preview_read_beats");
        mem_blk_pages_control_preview_read_beats.init_pages(trans_num_total, 1*((64+7)/8), 160);
        mem_blk_pages_control_preview_read_beats.tvoutdump_atinit(`TV_OUT_preview_read_beats);

        lmh_memory_probe_pkg::sample("control_regions_ready",0);
        fpath.push_back(`TV_IN_meta);
        mem_blk_pages_meta = mem_model_pages_with_diffofst#(128,8)::type_id::create("mem_blk_pages_meta");
        mem_blk_pages_meta.whole_page_size=1289712;
        mem_blk_pages_meta.maxi_bundlevar_fpath["meta_offset"]=`TV_IN_OFFSET_meta_offset;
        mem_blk_pages_meta.maxi_bundlevar_fpath["workspace"]=`TV_IN_OFFSET_workspace;
        lmh_memory_probe_pkg::sample("before_meta_load",1289456);
        mem_blk_pages_meta.tvinload_pagechk_atinit(fpath, 80591*((128+7)/8), 0);
        lmh_memory_probe_pkg::sample("after_meta_load",1289456);
        mem_blk_pages_meta.tvoutdump_atinit(`TV_OUT_meta);
        fpath.delete();

        fpath.push_back(`TV_IN_weights);
        mem_blk_pages_weights = mem_model_pages_with_diffofst#(128,8)::type_id::create("mem_blk_pages_weights");
        mem_blk_pages_weights.whole_page_size=545685760;
        mem_blk_pages_weights.maxi_bundlevar_fpath["tiled_weight"]=`TV_IN_OFFSET_tiled_weight;
        mem_blk_pages_weights.maxi_bundlevar_fpath["canonical_weight"]=`TV_IN_OFFSET_canonical_weight;
        lmh_memory_probe_pkg::sample("before_weights_load",545685504);
        mem_blk_pages_weights.tvinload_pagechk_atinit(fpath, 34105344*((128+7)/8), 0);
        lmh_memory_probe_pkg::sample("after_weights_load",545685504);
begin : bank_load_preflight
logic [7:0] got;
int err, fd;
fd=$fopen("weights_readback.csv","w");
if(fd==0) `uvm_fatal("bank_preflight","readback file")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd0);
$fwrite(fd,"0,%02h,%0d\n",got,err);
if(err || got !== 8'h2a) `uvm_fatal("bank_preflight","byte mismatch at 0")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1);
$fwrite(fd,"1,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 1")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd2);
$fwrite(fd,"2,%02h,%0d\n",got,err);
if(err || got !== 8'h6f) `uvm_fatal("bank_preflight","byte mismatch at 2")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3);
$fwrite(fd,"3,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 3")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd4);
$fwrite(fd,"4,%02h,%0d\n",got,err);
if(err || got !== 8'h16) `uvm_fatal("bank_preflight","byte mismatch at 4")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5);
$fwrite(fd,"5,%02h,%0d\n",got,err);
if(err || got !== 8'hbd) `uvm_fatal("bank_preflight","byte mismatch at 5")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd6);
$fwrite(fd,"6,%02h,%0d\n",got,err);
if(err || got !== 8'h19) `uvm_fatal("bank_preflight","byte mismatch at 6")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7);
$fwrite(fd,"7,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 7")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8);
$fwrite(fd,"8,%02h,%0d\n",got,err);
if(err || got !== 8'h1c) `uvm_fatal("bank_preflight","byte mismatch at 8")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9);
$fwrite(fd,"9,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 9")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd10);
$fwrite(fd,"10,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 10")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11);
$fwrite(fd,"11,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 11")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd12);
$fwrite(fd,"12,%02h,%0d\n",got,err);
if(err || got !== 8'h86) `uvm_fatal("bank_preflight","byte mismatch at 12")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd13);
$fwrite(fd,"13,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 13")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd14);
$fwrite(fd,"14,%02h,%0d\n",got,err);
if(err || got !== 8'h4e) `uvm_fatal("bank_preflight","byte mismatch at 14")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd15);
$fwrite(fd,"15,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 15")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd16);
$fwrite(fd,"16,%02h,%0d\n",got,err);
if(err || got !== 8'hb0) `uvm_fatal("bank_preflight","byte mismatch at 16")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd17);
$fwrite(fd,"17,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 17")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd18);
$fwrite(fd,"18,%02h,%0d\n",got,err);
if(err || got !== 8'hf8) `uvm_fatal("bank_preflight","byte mismatch at 18")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd19);
$fwrite(fd,"19,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 19")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd20);
$fwrite(fd,"20,%02h,%0d\n",got,err);
if(err || got !== 8'h05) `uvm_fatal("bank_preflight","byte mismatch at 20")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd21);
$fwrite(fd,"21,%02h,%0d\n",got,err);
if(err || got !== 8'hbd) `uvm_fatal("bank_preflight","byte mismatch at 21")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd22);
$fwrite(fd,"22,%02h,%0d\n",got,err);
if(err || got !== 8'hb6) `uvm_fatal("bank_preflight","byte mismatch at 22")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd23);
$fwrite(fd,"23,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 23")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd24);
$fwrite(fd,"24,%02h,%0d\n",got,err);
if(err || got !== 8'h6f) `uvm_fatal("bank_preflight","byte mismatch at 24")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd25);
$fwrite(fd,"25,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 25")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd26);
$fwrite(fd,"26,%02h,%0d\n",got,err);
if(err || got !== 8'h83) `uvm_fatal("bank_preflight","byte mismatch at 26")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd27);
$fwrite(fd,"27,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 27")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd28);
$fwrite(fd,"28,%02h,%0d\n",got,err);
if(err || got !== 8'ha5) `uvm_fatal("bank_preflight","byte mismatch at 28")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd29);
$fwrite(fd,"29,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 29")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd30);
$fwrite(fd,"30,%02h,%0d\n",got,err);
if(err || got !== 8'h8d) `uvm_fatal("bank_preflight","byte mismatch at 30")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd31);
$fwrite(fd,"31,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 31")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd32);
$fwrite(fd,"32,%02h,%0d\n",got,err);
if(err || got !== 8'h8f) `uvm_fatal("bank_preflight","byte mismatch at 32")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1048575);
$fwrite(fd,"1048575,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 1048575")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1048576);
$fwrite(fd,"1048576,%02h,%0d\n",got,err);
if(err || got !== 8'h34) `uvm_fatal("bank_preflight","byte mismatch at 1048576")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1834992);
$fwrite(fd,"1834992,%02h,%0d\n",got,err);
if(err || got !== 8'hf6) `uvm_fatal("bank_preflight","byte mismatch at 1834992")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1834993);
$fwrite(fd,"1834993,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 1834993")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1834994);
$fwrite(fd,"1834994,%02h,%0d\n",got,err);
if(err || got !== 8'h27) `uvm_fatal("bank_preflight","byte mismatch at 1834994")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1834995);
$fwrite(fd,"1834995,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 1834995")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1834996);
$fwrite(fd,"1834996,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 1834996")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1834997);
$fwrite(fd,"1834997,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 1834997")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1834998);
$fwrite(fd,"1834998,%02h,%0d\n",got,err);
if(err || got !== 8'h1d) `uvm_fatal("bank_preflight","byte mismatch at 1834998")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1834999);
$fwrite(fd,"1834999,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 1834999")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1835000);
$fwrite(fd,"1835000,%02h,%0d\n",got,err);
if(err || got !== 8'h90) `uvm_fatal("bank_preflight","byte mismatch at 1835000")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1835001);
$fwrite(fd,"1835001,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 1835001")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1835002);
$fwrite(fd,"1835002,%02h,%0d\n",got,err);
if(err || got !== 8'h6d) `uvm_fatal("bank_preflight","byte mismatch at 1835002")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1835003);
$fwrite(fd,"1835003,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 1835003")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1835004);
$fwrite(fd,"1835004,%02h,%0d\n",got,err);
if(err || got !== 8'hc5) `uvm_fatal("bank_preflight","byte mismatch at 1835004")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1835005);
$fwrite(fd,"1835005,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 1835005")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1835006);
$fwrite(fd,"1835006,%02h,%0d\n",got,err);
if(err || got !== 8'hde) `uvm_fatal("bank_preflight","byte mismatch at 1835006")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1835007);
$fwrite(fd,"1835007,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 1835007")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1835008);
$fwrite(fd,"1835008,%02h,%0d\n",got,err);
if(err || got !== 8'h3d) `uvm_fatal("bank_preflight","byte mismatch at 1835008")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1835009);
$fwrite(fd,"1835009,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 1835009")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1835010);
$fwrite(fd,"1835010,%02h,%0d\n",got,err);
if(err || got !== 8'h9d) `uvm_fatal("bank_preflight","byte mismatch at 1835010")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1835011);
$fwrite(fd,"1835011,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 1835011")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1835012);
$fwrite(fd,"1835012,%02h,%0d\n",got,err);
if(err || got !== 8'ha7) `uvm_fatal("bank_preflight","byte mismatch at 1835012")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1835013);
$fwrite(fd,"1835013,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 1835013")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1835014);
$fwrite(fd,"1835014,%02h,%0d\n",got,err);
if(err || got !== 8'h14) `uvm_fatal("bank_preflight","byte mismatch at 1835014")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1835015);
$fwrite(fd,"1835015,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 1835015")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1835016);
$fwrite(fd,"1835016,%02h,%0d\n",got,err);
if(err || got !== 8'h14) `uvm_fatal("bank_preflight","byte mismatch at 1835016")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1835017);
$fwrite(fd,"1835017,%02h,%0d\n",got,err);
if(err || got !== 8'hbd) `uvm_fatal("bank_preflight","byte mismatch at 1835017")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1835018);
$fwrite(fd,"1835018,%02h,%0d\n",got,err);
if(err || got !== 8'h8e) `uvm_fatal("bank_preflight","byte mismatch at 1835018")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1835019);
$fwrite(fd,"1835019,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 1835019")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1835020);
$fwrite(fd,"1835020,%02h,%0d\n",got,err);
if(err || got !== 8'h09) `uvm_fatal("bank_preflight","byte mismatch at 1835020")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1835021);
$fwrite(fd,"1835021,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 1835021")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1835022);
$fwrite(fd,"1835022,%02h,%0d\n",got,err);
if(err || got !== 8'hd3) `uvm_fatal("bank_preflight","byte mismatch at 1835022")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd1835023);
$fwrite(fd,"1835023,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 1835023")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd2097151);
$fwrite(fd,"2097151,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 2097151")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd2097152);
$fwrite(fd,"2097152,%02h,%0d\n",got,err);
if(err || got !== 8'h22) `uvm_fatal("bank_preflight","byte mismatch at 2097152")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3145727);
$fwrite(fd,"3145727,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 3145727")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3145728);
$fwrite(fd,"3145728,%02h,%0d\n",got,err);
if(err || got !== 8'h5c) `uvm_fatal("bank_preflight","byte mismatch at 3145728")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670000);
$fwrite(fd,"3670000,%02h,%0d\n",got,err);
if(err || got !== 8'hd6) `uvm_fatal("bank_preflight","byte mismatch at 3670000")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670001);
$fwrite(fd,"3670001,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 3670001")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670002);
$fwrite(fd,"3670002,%02h,%0d\n",got,err);
if(err || got !== 8'h6c) `uvm_fatal("bank_preflight","byte mismatch at 3670002")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670003);
$fwrite(fd,"3670003,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 3670003")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670004);
$fwrite(fd,"3670004,%02h,%0d\n",got,err);
if(err || got !== 8'h92) `uvm_fatal("bank_preflight","byte mismatch at 3670004")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670005);
$fwrite(fd,"3670005,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 3670005")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670006);
$fwrite(fd,"3670006,%02h,%0d\n",got,err);
if(err || got !== 8'h37) `uvm_fatal("bank_preflight","byte mismatch at 3670006")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670007);
$fwrite(fd,"3670007,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 3670007")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670008);
$fwrite(fd,"3670008,%02h,%0d\n",got,err);
if(err || got !== 8'hbf) `uvm_fatal("bank_preflight","byte mismatch at 3670008")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670009);
$fwrite(fd,"3670009,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 3670009")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670010);
$fwrite(fd,"3670010,%02h,%0d\n",got,err);
if(err || got !== 8'hf0) `uvm_fatal("bank_preflight","byte mismatch at 3670010")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670011);
$fwrite(fd,"3670011,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 3670011")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670012);
$fwrite(fd,"3670012,%02h,%0d\n",got,err);
if(err || got !== 8'h21) `uvm_fatal("bank_preflight","byte mismatch at 3670012")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670013);
$fwrite(fd,"3670013,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 3670013")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670014);
$fwrite(fd,"3670014,%02h,%0d\n",got,err);
if(err || got !== 8'h2a) `uvm_fatal("bank_preflight","byte mismatch at 3670014")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670015);
$fwrite(fd,"3670015,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 3670015")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670016);
$fwrite(fd,"3670016,%02h,%0d\n",got,err);
if(err || got !== 8'h91) `uvm_fatal("bank_preflight","byte mismatch at 3670016")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670017);
$fwrite(fd,"3670017,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 3670017")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670018);
$fwrite(fd,"3670018,%02h,%0d\n",got,err);
if(err || got !== 8'hf4) `uvm_fatal("bank_preflight","byte mismatch at 3670018")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670019);
$fwrite(fd,"3670019,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 3670019")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670020);
$fwrite(fd,"3670020,%02h,%0d\n",got,err);
if(err || got !== 8'ha2) `uvm_fatal("bank_preflight","byte mismatch at 3670020")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670021);
$fwrite(fd,"3670021,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 3670021")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670022);
$fwrite(fd,"3670022,%02h,%0d\n",got,err);
if(err || got !== 8'hd9) `uvm_fatal("bank_preflight","byte mismatch at 3670022")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670023);
$fwrite(fd,"3670023,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 3670023")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670024);
$fwrite(fd,"3670024,%02h,%0d\n",got,err);
if(err || got !== 8'h93) `uvm_fatal("bank_preflight","byte mismatch at 3670024")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670025);
$fwrite(fd,"3670025,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 3670025")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670026);
$fwrite(fd,"3670026,%02h,%0d\n",got,err);
if(err || got !== 8'hb4) `uvm_fatal("bank_preflight","byte mismatch at 3670026")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670027);
$fwrite(fd,"3670027,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 3670027")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670028);
$fwrite(fd,"3670028,%02h,%0d\n",got,err);
if(err || got !== 8'h96) `uvm_fatal("bank_preflight","byte mismatch at 3670028")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670029);
$fwrite(fd,"3670029,%02h,%0d\n",got,err);
if(err || got !== 8'hb9) `uvm_fatal("bank_preflight","byte mismatch at 3670029")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670030);
$fwrite(fd,"3670030,%02h,%0d\n",got,err);
if(err || got !== 8'ha8) `uvm_fatal("bank_preflight","byte mismatch at 3670030")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd3670031);
$fwrite(fd,"3670031,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 3670031")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd4194303);
$fwrite(fd,"4194303,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 4194303")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd4194304);
$fwrite(fd,"4194304,%02h,%0d\n",got,err);
if(err || got !== 8'ha0) `uvm_fatal("bank_preflight","byte mismatch at 4194304")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5242879);
$fwrite(fd,"5242879,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 5242879")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5242880);
$fwrite(fd,"5242880,%02h,%0d\n",got,err);
if(err || got !== 8'hb2) `uvm_fatal("bank_preflight","byte mismatch at 5242880")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505008);
$fwrite(fd,"5505008,%02h,%0d\n",got,err);
if(err || got !== 8'ha7) `uvm_fatal("bank_preflight","byte mismatch at 5505008")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505009);
$fwrite(fd,"5505009,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 5505009")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505010);
$fwrite(fd,"5505010,%02h,%0d\n",got,err);
if(err || got !== 8'h2e) `uvm_fatal("bank_preflight","byte mismatch at 5505010")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505011);
$fwrite(fd,"5505011,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 5505011")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505012);
$fwrite(fd,"5505012,%02h,%0d\n",got,err);
if(err || got !== 8'hdf) `uvm_fatal("bank_preflight","byte mismatch at 5505012")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505013);
$fwrite(fd,"5505013,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 5505013")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505014);
$fwrite(fd,"5505014,%02h,%0d\n",got,err);
if(err || got !== 8'h4b) `uvm_fatal("bank_preflight","byte mismatch at 5505014")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505015);
$fwrite(fd,"5505015,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 5505015")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505016);
$fwrite(fd,"5505016,%02h,%0d\n",got,err);
if(err || got !== 8'hc8) `uvm_fatal("bank_preflight","byte mismatch at 5505016")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505017);
$fwrite(fd,"5505017,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 5505017")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505018);
$fwrite(fd,"5505018,%02h,%0d\n",got,err);
if(err || got !== 8'h44) `uvm_fatal("bank_preflight","byte mismatch at 5505018")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505019);
$fwrite(fd,"5505019,%02h,%0d\n",got,err);
if(err || got !== 8'hb9) `uvm_fatal("bank_preflight","byte mismatch at 5505019")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505020);
$fwrite(fd,"5505020,%02h,%0d\n",got,err);
if(err || got !== 8'h1b) `uvm_fatal("bank_preflight","byte mismatch at 5505020")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505021);
$fwrite(fd,"5505021,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 5505021")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505022);
$fwrite(fd,"5505022,%02h,%0d\n",got,err);
if(err || got !== 8'h34) `uvm_fatal("bank_preflight","byte mismatch at 5505022")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505023);
$fwrite(fd,"5505023,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 5505023")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505024);
$fwrite(fd,"5505024,%02h,%0d\n",got,err);
if(err || got !== 8'h30) `uvm_fatal("bank_preflight","byte mismatch at 5505024")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505025);
$fwrite(fd,"5505025,%02h,%0d\n",got,err);
if(err || got !== 8'h3d) `uvm_fatal("bank_preflight","byte mismatch at 5505025")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505026);
$fwrite(fd,"5505026,%02h,%0d\n",got,err);
if(err || got !== 8'hc2) `uvm_fatal("bank_preflight","byte mismatch at 5505026")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505027);
$fwrite(fd,"5505027,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 5505027")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505028);
$fwrite(fd,"5505028,%02h,%0d\n",got,err);
if(err || got !== 8'h0e) `uvm_fatal("bank_preflight","byte mismatch at 5505028")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505029);
$fwrite(fd,"5505029,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 5505029")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505030);
$fwrite(fd,"5505030,%02h,%0d\n",got,err);
if(err || got !== 8'hc2) `uvm_fatal("bank_preflight","byte mismatch at 5505030")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505031);
$fwrite(fd,"5505031,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 5505031")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505032);
$fwrite(fd,"5505032,%02h,%0d\n",got,err);
if(err || got !== 8'hd7) `uvm_fatal("bank_preflight","byte mismatch at 5505032")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505033);
$fwrite(fd,"5505033,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 5505033")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505034);
$fwrite(fd,"5505034,%02h,%0d\n",got,err);
if(err || got !== 8'hf8) `uvm_fatal("bank_preflight","byte mismatch at 5505034")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505035);
$fwrite(fd,"5505035,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 5505035")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505036);
$fwrite(fd,"5505036,%02h,%0d\n",got,err);
if(err || got !== 8'hbe) `uvm_fatal("bank_preflight","byte mismatch at 5505036")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505037);
$fwrite(fd,"5505037,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 5505037")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505038);
$fwrite(fd,"5505038,%02h,%0d\n",got,err);
if(err || got !== 8'h2f) `uvm_fatal("bank_preflight","byte mismatch at 5505038")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd5505039);
$fwrite(fd,"5505039,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 5505039")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd6291455);
$fwrite(fd,"6291455,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 6291455")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd6291456);
$fwrite(fd,"6291456,%02h,%0d\n",got,err);
if(err || got !== 8'hd1) `uvm_fatal("bank_preflight","byte mismatch at 6291456")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340016);
$fwrite(fd,"7340016,%02h,%0d\n",got,err);
if(err || got !== 8'h2b) `uvm_fatal("bank_preflight","byte mismatch at 7340016")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340017);
$fwrite(fd,"7340017,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 7340017")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340018);
$fwrite(fd,"7340018,%02h,%0d\n",got,err);
if(err || got !== 8'hd9) `uvm_fatal("bank_preflight","byte mismatch at 7340018")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340019);
$fwrite(fd,"7340019,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 7340019")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340020);
$fwrite(fd,"7340020,%02h,%0d\n",got,err);
if(err || got !== 8'h34) `uvm_fatal("bank_preflight","byte mismatch at 7340020")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340021);
$fwrite(fd,"7340021,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 7340021")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340022);
$fwrite(fd,"7340022,%02h,%0d\n",got,err);
if(err || got !== 8'h50) `uvm_fatal("bank_preflight","byte mismatch at 7340022")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340023);
$fwrite(fd,"7340023,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 7340023")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340024);
$fwrite(fd,"7340024,%02h,%0d\n",got,err);
if(err || got !== 8'h02) `uvm_fatal("bank_preflight","byte mismatch at 7340024")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340025);
$fwrite(fd,"7340025,%02h,%0d\n",got,err);
if(err || got !== 8'hbd) `uvm_fatal("bank_preflight","byte mismatch at 7340025")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340026);
$fwrite(fd,"7340026,%02h,%0d\n",got,err);
if(err || got !== 8'h0d) `uvm_fatal("bank_preflight","byte mismatch at 7340026")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340027);
$fwrite(fd,"7340027,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 7340027")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340028);
$fwrite(fd,"7340028,%02h,%0d\n",got,err);
if(err || got !== 8'h02) `uvm_fatal("bank_preflight","byte mismatch at 7340028")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340029);
$fwrite(fd,"7340029,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 7340029")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340030);
$fwrite(fd,"7340030,%02h,%0d\n",got,err);
if(err || got !== 8'h81) `uvm_fatal("bank_preflight","byte mismatch at 7340030")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340031);
$fwrite(fd,"7340031,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 7340031")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340032);
$fwrite(fd,"7340032,%02h,%0d\n",got,err);
if(err || got !== 8'ha5) `uvm_fatal("bank_preflight","byte mismatch at 7340032")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340033);
$fwrite(fd,"7340033,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 7340033")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340034);
$fwrite(fd,"7340034,%02h,%0d\n",got,err);
if(err || got !== 8'h6b) `uvm_fatal("bank_preflight","byte mismatch at 7340034")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340035);
$fwrite(fd,"7340035,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 7340035")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340036);
$fwrite(fd,"7340036,%02h,%0d\n",got,err);
if(err || got !== 8'h2c) `uvm_fatal("bank_preflight","byte mismatch at 7340036")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340037);
$fwrite(fd,"7340037,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 7340037")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340038);
$fwrite(fd,"7340038,%02h,%0d\n",got,err);
if(err || got !== 8'h86) `uvm_fatal("bank_preflight","byte mismatch at 7340038")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340039);
$fwrite(fd,"7340039,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 7340039")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340040);
$fwrite(fd,"7340040,%02h,%0d\n",got,err);
if(err || got !== 8'h99) `uvm_fatal("bank_preflight","byte mismatch at 7340040")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340041);
$fwrite(fd,"7340041,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 7340041")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340042);
$fwrite(fd,"7340042,%02h,%0d\n",got,err);
if(err || got !== 8'hc9) `uvm_fatal("bank_preflight","byte mismatch at 7340042")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340043);
$fwrite(fd,"7340043,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 7340043")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340044);
$fwrite(fd,"7340044,%02h,%0d\n",got,err);
if(err || got !== 8'hb7) `uvm_fatal("bank_preflight","byte mismatch at 7340044")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340045);
$fwrite(fd,"7340045,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 7340045")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340046);
$fwrite(fd,"7340046,%02h,%0d\n",got,err);
if(err || got !== 8'hd8) `uvm_fatal("bank_preflight","byte mismatch at 7340046")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd7340047);
$fwrite(fd,"7340047,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 7340047")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8388607);
$fwrite(fd,"8388607,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 8388607")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8388608);
$fwrite(fd,"8388608,%02h,%0d\n",got,err);
if(err || got !== 8'hd9) `uvm_fatal("bank_preflight","byte mismatch at 8388608")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814560);
$fwrite(fd,"8814560,%02h,%0d\n",got,err);
if(err || got !== 8'h24) `uvm_fatal("bank_preflight","byte mismatch at 8814560")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814561);
$fwrite(fd,"8814561,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 8814561")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814562);
$fwrite(fd,"8814562,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 8814562")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814563);
$fwrite(fd,"8814563,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 8814563")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814564);
$fwrite(fd,"8814564,%02h,%0d\n",got,err);
if(err || got !== 8'hdd) `uvm_fatal("bank_preflight","byte mismatch at 8814564")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814565);
$fwrite(fd,"8814565,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 8814565")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814566);
$fwrite(fd,"8814566,%02h,%0d\n",got,err);
if(err || got !== 8'ha2) `uvm_fatal("bank_preflight","byte mismatch at 8814566")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814567);
$fwrite(fd,"8814567,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 8814567")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814568);
$fwrite(fd,"8814568,%02h,%0d\n",got,err);
if(err || got !== 8'h6d) `uvm_fatal("bank_preflight","byte mismatch at 8814568")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814569);
$fwrite(fd,"8814569,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 8814569")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814570);
$fwrite(fd,"8814570,%02h,%0d\n",got,err);
if(err || got !== 8'hc6) `uvm_fatal("bank_preflight","byte mismatch at 8814570")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814571);
$fwrite(fd,"8814571,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 8814571")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814572);
$fwrite(fd,"8814572,%02h,%0d\n",got,err);
if(err || got !== 8'hb9) `uvm_fatal("bank_preflight","byte mismatch at 8814572")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814573);
$fwrite(fd,"8814573,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 8814573")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814574);
$fwrite(fd,"8814574,%02h,%0d\n",got,err);
if(err || got !== 8'h54) `uvm_fatal("bank_preflight","byte mismatch at 8814574")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814575);
$fwrite(fd,"8814575,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 8814575")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814576);
$fwrite(fd,"8814576,%02h,%0d\n",got,err);
if(err || got !== 8'h69) `uvm_fatal("bank_preflight","byte mismatch at 8814576")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814577);
$fwrite(fd,"8814577,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 8814577")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814578);
$fwrite(fd,"8814578,%02h,%0d\n",got,err);
if(err || got !== 8'hc2) `uvm_fatal("bank_preflight","byte mismatch at 8814578")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814579);
$fwrite(fd,"8814579,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 8814579")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814580);
$fwrite(fd,"8814580,%02h,%0d\n",got,err);
if(err || got !== 8'h0e) `uvm_fatal("bank_preflight","byte mismatch at 8814580")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814581);
$fwrite(fd,"8814581,%02h,%0d\n",got,err);
if(err || got !== 8'h3d) `uvm_fatal("bank_preflight","byte mismatch at 8814581")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814582);
$fwrite(fd,"8814582,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 8814582")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814583);
$fwrite(fd,"8814583,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 8814583")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814584);
$fwrite(fd,"8814584,%02h,%0d\n",got,err);
if(err || got !== 8'ha8) `uvm_fatal("bank_preflight","byte mismatch at 8814584")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814585);
$fwrite(fd,"8814585,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 8814585")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814586);
$fwrite(fd,"8814586,%02h,%0d\n",got,err);
if(err || got !== 8'hae) `uvm_fatal("bank_preflight","byte mismatch at 8814586")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814587);
$fwrite(fd,"8814587,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 8814587")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814588);
$fwrite(fd,"8814588,%02h,%0d\n",got,err);
if(err || got !== 8'hb6) `uvm_fatal("bank_preflight","byte mismatch at 8814588")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814589);
$fwrite(fd,"8814589,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 8814589")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814590);
$fwrite(fd,"8814590,%02h,%0d\n",got,err);
if(err || got !== 8'h58) `uvm_fatal("bank_preflight","byte mismatch at 8814590")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814591);
$fwrite(fd,"8814591,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 8814591")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814592);
$fwrite(fd,"8814592,%02h,%0d\n",got,err);
if(err || got !== 8'h6e) `uvm_fatal("bank_preflight","byte mismatch at 8814592")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814593);
$fwrite(fd,"8814593,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 8814593")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814594);
$fwrite(fd,"8814594,%02h,%0d\n",got,err);
if(err || got !== 8'hdd) `uvm_fatal("bank_preflight","byte mismatch at 8814594")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814595);
$fwrite(fd,"8814595,%02h,%0d\n",got,err);
if(err || got !== 8'hb8) `uvm_fatal("bank_preflight","byte mismatch at 8814595")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814596);
$fwrite(fd,"8814596,%02h,%0d\n",got,err);
if(err || got !== 8'h7e) `uvm_fatal("bank_preflight","byte mismatch at 8814596")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814597);
$fwrite(fd,"8814597,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 8814597")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814598);
$fwrite(fd,"8814598,%02h,%0d\n",got,err);
if(err || got !== 8'h9a) `uvm_fatal("bank_preflight","byte mismatch at 8814598")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814599);
$fwrite(fd,"8814599,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 8814599")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814600);
$fwrite(fd,"8814600,%02h,%0d\n",got,err);
if(err || got !== 8'h15) `uvm_fatal("bank_preflight","byte mismatch at 8814600")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814601);
$fwrite(fd,"8814601,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 8814601")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814602);
$fwrite(fd,"8814602,%02h,%0d\n",got,err);
if(err || got !== 8'h27) `uvm_fatal("bank_preflight","byte mismatch at 8814602")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814603);
$fwrite(fd,"8814603,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 8814603")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814604);
$fwrite(fd,"8814604,%02h,%0d\n",got,err);
if(err || got !== 8'h0b) `uvm_fatal("bank_preflight","byte mismatch at 8814604")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814605);
$fwrite(fd,"8814605,%02h,%0d\n",got,err);
if(err || got !== 8'h3d) `uvm_fatal("bank_preflight","byte mismatch at 8814605")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814606);
$fwrite(fd,"8814606,%02h,%0d\n",got,err);
if(err || got !== 8'h01) `uvm_fatal("bank_preflight","byte mismatch at 8814606")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814607);
$fwrite(fd,"8814607,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 8814607")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814608);
$fwrite(fd,"8814608,%02h,%0d\n",got,err);
if(err || got !== 8'h9d) `uvm_fatal("bank_preflight","byte mismatch at 8814608")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814609);
$fwrite(fd,"8814609,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 8814609")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814610);
$fwrite(fd,"8814610,%02h,%0d\n",got,err);
if(err || got !== 8'h86) `uvm_fatal("bank_preflight","byte mismatch at 8814610")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814611);
$fwrite(fd,"8814611,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 8814611")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814612);
$fwrite(fd,"8814612,%02h,%0d\n",got,err);
if(err || got !== 8'h45) `uvm_fatal("bank_preflight","byte mismatch at 8814612")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814613);
$fwrite(fd,"8814613,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 8814613")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814614);
$fwrite(fd,"8814614,%02h,%0d\n",got,err);
if(err || got !== 8'h65) `uvm_fatal("bank_preflight","byte mismatch at 8814614")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814615);
$fwrite(fd,"8814615,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 8814615")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814616);
$fwrite(fd,"8814616,%02h,%0d\n",got,err);
if(err || got !== 8'h18) `uvm_fatal("bank_preflight","byte mismatch at 8814616")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814617);
$fwrite(fd,"8814617,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 8814617")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814618);
$fwrite(fd,"8814618,%02h,%0d\n",got,err);
if(err || got !== 8'hfe) `uvm_fatal("bank_preflight","byte mismatch at 8814618")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814619);
$fwrite(fd,"8814619,%02h,%0d\n",got,err);
if(err || got !== 8'h39) `uvm_fatal("bank_preflight","byte mismatch at 8814619")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814620);
$fwrite(fd,"8814620,%02h,%0d\n",got,err);
if(err || got !== 8'h96) `uvm_fatal("bank_preflight","byte mismatch at 8814620")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814621);
$fwrite(fd,"8814621,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 8814621")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814622);
$fwrite(fd,"8814622,%02h,%0d\n",got,err);
if(err || got !== 8'h7f) `uvm_fatal("bank_preflight","byte mismatch at 8814622")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814623);
$fwrite(fd,"8814623,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 8814623")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd8814624);
$fwrite(fd,"8814624,%02h,%0d\n",got,err);
if(err || got !== 8'hbd) `uvm_fatal("bank_preflight","byte mismatch at 8814624")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175008);
$fwrite(fd,"9175008,%02h,%0d\n",got,err);
if(err || got !== 8'h69) `uvm_fatal("bank_preflight","byte mismatch at 9175008")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175009);
$fwrite(fd,"9175009,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 9175009")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175010);
$fwrite(fd,"9175010,%02h,%0d\n",got,err);
if(err || got !== 8'h6c) `uvm_fatal("bank_preflight","byte mismatch at 9175010")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175011);
$fwrite(fd,"9175011,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 9175011")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175012);
$fwrite(fd,"9175012,%02h,%0d\n",got,err);
if(err || got !== 8'h38) `uvm_fatal("bank_preflight","byte mismatch at 9175012")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175013);
$fwrite(fd,"9175013,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 9175013")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175014);
$fwrite(fd,"9175014,%02h,%0d\n",got,err);
if(err || got !== 8'h2c) `uvm_fatal("bank_preflight","byte mismatch at 9175014")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175015);
$fwrite(fd,"9175015,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 9175015")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175016);
$fwrite(fd,"9175016,%02h,%0d\n",got,err);
if(err || got !== 8'h29) `uvm_fatal("bank_preflight","byte mismatch at 9175016")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175017);
$fwrite(fd,"9175017,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 9175017")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175018);
$fwrite(fd,"9175018,%02h,%0d\n",got,err);
if(err || got !== 8'h94) `uvm_fatal("bank_preflight","byte mismatch at 9175018")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175019);
$fwrite(fd,"9175019,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 9175019")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175020);
$fwrite(fd,"9175020,%02h,%0d\n",got,err);
if(err || got !== 8'h4a) `uvm_fatal("bank_preflight","byte mismatch at 9175020")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175021);
$fwrite(fd,"9175021,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 9175021")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175022);
$fwrite(fd,"9175022,%02h,%0d\n",got,err);
if(err || got !== 8'hdd) `uvm_fatal("bank_preflight","byte mismatch at 9175022")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175023);
$fwrite(fd,"9175023,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 9175023")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175024);
$fwrite(fd,"9175024,%02h,%0d\n",got,err);
if(err || got !== 8'hb4) `uvm_fatal("bank_preflight","byte mismatch at 9175024")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175025);
$fwrite(fd,"9175025,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 9175025")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175026);
$fwrite(fd,"9175026,%02h,%0d\n",got,err);
if(err || got !== 8'h1b) `uvm_fatal("bank_preflight","byte mismatch at 9175026")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175027);
$fwrite(fd,"9175027,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 9175027")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175028);
$fwrite(fd,"9175028,%02h,%0d\n",got,err);
if(err || got !== 8'ha2) `uvm_fatal("bank_preflight","byte mismatch at 9175028")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175029);
$fwrite(fd,"9175029,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 9175029")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175030);
$fwrite(fd,"9175030,%02h,%0d\n",got,err);
if(err || got !== 8'hb9) `uvm_fatal("bank_preflight","byte mismatch at 9175030")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175031);
$fwrite(fd,"9175031,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 9175031")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175032);
$fwrite(fd,"9175032,%02h,%0d\n",got,err);
if(err || got !== 8'h8b) `uvm_fatal("bank_preflight","byte mismatch at 9175032")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175033);
$fwrite(fd,"9175033,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 9175033")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175034);
$fwrite(fd,"9175034,%02h,%0d\n",got,err);
if(err || got !== 8'h2c) `uvm_fatal("bank_preflight","byte mismatch at 9175034")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175035);
$fwrite(fd,"9175035,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 9175035")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175036);
$fwrite(fd,"9175036,%02h,%0d\n",got,err);
if(err || got !== 8'h6e) `uvm_fatal("bank_preflight","byte mismatch at 9175036")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175037);
$fwrite(fd,"9175037,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 9175037")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175038);
$fwrite(fd,"9175038,%02h,%0d\n",got,err);
if(err || got !== 8'h8e) `uvm_fatal("bank_preflight","byte mismatch at 9175038")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175039);
$fwrite(fd,"9175039,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 9175039")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175040);
$fwrite(fd,"9175040,%02h,%0d\n",got,err);
if(err || got !== 8'h77) `uvm_fatal("bank_preflight","byte mismatch at 9175040")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175041);
$fwrite(fd,"9175041,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 9175041")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175042);
$fwrite(fd,"9175042,%02h,%0d\n",got,err);
if(err || got !== 8'h8c) `uvm_fatal("bank_preflight","byte mismatch at 9175042")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175043);
$fwrite(fd,"9175043,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 9175043")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175044);
$fwrite(fd,"9175044,%02h,%0d\n",got,err);
if(err || got !== 8'hf1) `uvm_fatal("bank_preflight","byte mismatch at 9175044")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175045);
$fwrite(fd,"9175045,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 9175045")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175046);
$fwrite(fd,"9175046,%02h,%0d\n",got,err);
if(err || got !== 8'hc3) `uvm_fatal("bank_preflight","byte mismatch at 9175046")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175047);
$fwrite(fd,"9175047,%02h,%0d\n",got,err);
if(err || got !== 8'h39) `uvm_fatal("bank_preflight","byte mismatch at 9175047")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175048);
$fwrite(fd,"9175048,%02h,%0d\n",got,err);
if(err || got !== 8'he2) `uvm_fatal("bank_preflight","byte mismatch at 9175048")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175049);
$fwrite(fd,"9175049,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 9175049")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175050);
$fwrite(fd,"9175050,%02h,%0d\n",got,err);
if(err || got !== 8'h78) `uvm_fatal("bank_preflight","byte mismatch at 9175050")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175051);
$fwrite(fd,"9175051,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 9175051")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175052);
$fwrite(fd,"9175052,%02h,%0d\n",got,err);
if(err || got !== 8'hf9) `uvm_fatal("bank_preflight","byte mismatch at 9175052")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175053);
$fwrite(fd,"9175053,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 9175053")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175054);
$fwrite(fd,"9175054,%02h,%0d\n",got,err);
if(err || got !== 8'h37) `uvm_fatal("bank_preflight","byte mismatch at 9175054")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175055);
$fwrite(fd,"9175055,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 9175055")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175056);
$fwrite(fd,"9175056,%02h,%0d\n",got,err);
if(err || got !== 8'h89) `uvm_fatal("bank_preflight","byte mismatch at 9175056")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175057);
$fwrite(fd,"9175057,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 9175057")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175058);
$fwrite(fd,"9175058,%02h,%0d\n",got,err);
if(err || got !== 8'hd4) `uvm_fatal("bank_preflight","byte mismatch at 9175058")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175059);
$fwrite(fd,"9175059,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 9175059")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175060);
$fwrite(fd,"9175060,%02h,%0d\n",got,err);
if(err || got !== 8'h04) `uvm_fatal("bank_preflight","byte mismatch at 9175060")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175061);
$fwrite(fd,"9175061,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 9175061")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175062);
$fwrite(fd,"9175062,%02h,%0d\n",got,err);
if(err || got !== 8'hb7) `uvm_fatal("bank_preflight","byte mismatch at 9175062")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175063);
$fwrite(fd,"9175063,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 9175063")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175064);
$fwrite(fd,"9175064,%02h,%0d\n",got,err);
if(err || got !== 8'hcc) `uvm_fatal("bank_preflight","byte mismatch at 9175064")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175065);
$fwrite(fd,"9175065,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 9175065")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175066);
$fwrite(fd,"9175066,%02h,%0d\n",got,err);
if(err || got !== 8'h42) `uvm_fatal("bank_preflight","byte mismatch at 9175066")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175067);
$fwrite(fd,"9175067,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 9175067")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175068);
$fwrite(fd,"9175068,%02h,%0d\n",got,err);
if(err || got !== 8'h9e) `uvm_fatal("bank_preflight","byte mismatch at 9175068")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175069);
$fwrite(fd,"9175069,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 9175069")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175070);
$fwrite(fd,"9175070,%02h,%0d\n",got,err);
if(err || got !== 8'hae) `uvm_fatal("bank_preflight","byte mismatch at 9175070")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175071);
$fwrite(fd,"9175071,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 9175071")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9175072);
$fwrite(fd,"9175072,%02h,%0d\n",got,err);
if(err || got !== 8'h96) `uvm_fatal("bank_preflight","byte mismatch at 9175072")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9437183);
$fwrite(fd,"9437183,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 9437183")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd9437184);
$fwrite(fd,"9437184,%02h,%0d\n",got,err);
if(err || got !== 8'h8c) `uvm_fatal("bank_preflight","byte mismatch at 9437184")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd10485759);
$fwrite(fd,"10485759,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 10485759")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd10485760);
$fwrite(fd,"10485760,%02h,%0d\n",got,err);
if(err || got !== 8'h13) `uvm_fatal("bank_preflight","byte mismatch at 10485760")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010032);
$fwrite(fd,"11010032,%02h,%0d\n",got,err);
if(err || got !== 8'h39) `uvm_fatal("bank_preflight","byte mismatch at 11010032")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010033);
$fwrite(fd,"11010033,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 11010033")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010034);
$fwrite(fd,"11010034,%02h,%0d\n",got,err);
if(err || got !== 8'h18) `uvm_fatal("bank_preflight","byte mismatch at 11010034")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010035);
$fwrite(fd,"11010035,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 11010035")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010036);
$fwrite(fd,"11010036,%02h,%0d\n",got,err);
if(err || got !== 8'hc4) `uvm_fatal("bank_preflight","byte mismatch at 11010036")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010037);
$fwrite(fd,"11010037,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 11010037")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010038);
$fwrite(fd,"11010038,%02h,%0d\n",got,err);
if(err || got !== 8'ha9) `uvm_fatal("bank_preflight","byte mismatch at 11010038")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010039);
$fwrite(fd,"11010039,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 11010039")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010040);
$fwrite(fd,"11010040,%02h,%0d\n",got,err);
if(err || got !== 8'hb4) `uvm_fatal("bank_preflight","byte mismatch at 11010040")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010041);
$fwrite(fd,"11010041,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 11010041")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010042);
$fwrite(fd,"11010042,%02h,%0d\n",got,err);
if(err || got !== 8'he9) `uvm_fatal("bank_preflight","byte mismatch at 11010042")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010043);
$fwrite(fd,"11010043,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 11010043")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010044);
$fwrite(fd,"11010044,%02h,%0d\n",got,err);
if(err || got !== 8'h96) `uvm_fatal("bank_preflight","byte mismatch at 11010044")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010045);
$fwrite(fd,"11010045,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 11010045")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010046);
$fwrite(fd,"11010046,%02h,%0d\n",got,err);
if(err || got !== 8'h6c) `uvm_fatal("bank_preflight","byte mismatch at 11010046")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010047);
$fwrite(fd,"11010047,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 11010047")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010048);
$fwrite(fd,"11010048,%02h,%0d\n",got,err);
if(err || got !== 8'he3) `uvm_fatal("bank_preflight","byte mismatch at 11010048")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010049);
$fwrite(fd,"11010049,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 11010049")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010050);
$fwrite(fd,"11010050,%02h,%0d\n",got,err);
if(err || got !== 8'h28) `uvm_fatal("bank_preflight","byte mismatch at 11010050")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010051);
$fwrite(fd,"11010051,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 11010051")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010052);
$fwrite(fd,"11010052,%02h,%0d\n",got,err);
if(err || got !== 8'h96) `uvm_fatal("bank_preflight","byte mismatch at 11010052")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010053);
$fwrite(fd,"11010053,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 11010053")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010054);
$fwrite(fd,"11010054,%02h,%0d\n",got,err);
if(err || got !== 8'h15) `uvm_fatal("bank_preflight","byte mismatch at 11010054")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010055);
$fwrite(fd,"11010055,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 11010055")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010056);
$fwrite(fd,"11010056,%02h,%0d\n",got,err);
if(err || got !== 8'hb7) `uvm_fatal("bank_preflight","byte mismatch at 11010056")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010057);
$fwrite(fd,"11010057,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 11010057")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010058);
$fwrite(fd,"11010058,%02h,%0d\n",got,err);
if(err || got !== 8'h8d) `uvm_fatal("bank_preflight","byte mismatch at 11010058")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010059);
$fwrite(fd,"11010059,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 11010059")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010060);
$fwrite(fd,"11010060,%02h,%0d\n",got,err);
if(err || got !== 8'had) `uvm_fatal("bank_preflight","byte mismatch at 11010060")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010061);
$fwrite(fd,"11010061,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 11010061")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010062);
$fwrite(fd,"11010062,%02h,%0d\n",got,err);
if(err || got !== 8'ha1) `uvm_fatal("bank_preflight","byte mismatch at 11010062")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11010063);
$fwrite(fd,"11010063,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 11010063")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11534335);
$fwrite(fd,"11534335,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 11534335")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd11534336);
$fwrite(fd,"11534336,%02h,%0d\n",got,err);
if(err || got !== 8'h38) `uvm_fatal("bank_preflight","byte mismatch at 11534336")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd12582911);
$fwrite(fd,"12582911,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 12582911")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd12582912);
$fwrite(fd,"12582912,%02h,%0d\n",got,err);
if(err || got !== 8'h88) `uvm_fatal("bank_preflight","byte mismatch at 12582912")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd13631487);
$fwrite(fd,"13631487,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 13631487")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd13631488);
$fwrite(fd,"13631488,%02h,%0d\n",got,err);
if(err || got !== 8'h0a) `uvm_fatal("bank_preflight","byte mismatch at 13631488")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd14680063);
$fwrite(fd,"14680063,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 14680063")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd14680064);
$fwrite(fd,"14680064,%02h,%0d\n",got,err);
if(err || got !== 8'h5e) `uvm_fatal("bank_preflight","byte mismatch at 14680064")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd15728639);
$fwrite(fd,"15728639,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 15728639")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd15728640);
$fwrite(fd,"15728640,%02h,%0d\n",got,err);
if(err || got !== 8'h1b) `uvm_fatal("bank_preflight","byte mismatch at 15728640")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd16777215);
$fwrite(fd,"16777215,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 16777215")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd16777216);
$fwrite(fd,"16777216,%02h,%0d\n",got,err);
if(err || got !== 8'heb) `uvm_fatal("bank_preflight","byte mismatch at 16777216")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd17825791);
$fwrite(fd,"17825791,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 17825791")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd17825792);
$fwrite(fd,"17825792,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 17825792")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd18874367);
$fwrite(fd,"18874367,%02h,%0d\n",got,err);
if(err || got !== 8'h3d) `uvm_fatal("bank_preflight","byte mismatch at 18874367")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd18874368);
$fwrite(fd,"18874368,%02h,%0d\n",got,err);
if(err || got !== 8'hbe) `uvm_fatal("bank_preflight","byte mismatch at 18874368")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd19922943);
$fwrite(fd,"19922943,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 19922943")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd19922944);
$fwrite(fd,"19922944,%02h,%0d\n",got,err);
if(err || got !== 8'h98) `uvm_fatal("bank_preflight","byte mismatch at 19922944")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd20971519);
$fwrite(fd,"20971519,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 20971519")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd20971520);
$fwrite(fd,"20971520,%02h,%0d\n",got,err);
if(err || got !== 8'h10) `uvm_fatal("bank_preflight","byte mismatch at 20971520")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd22020095);
$fwrite(fd,"22020095,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 22020095")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd22020096);
$fwrite(fd,"22020096,%02h,%0d\n",got,err);
if(err || got !== 8'h5a) `uvm_fatal("bank_preflight","byte mismatch at 22020096")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd23068671);
$fwrite(fd,"23068671,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 23068671")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd23068672);
$fwrite(fd,"23068672,%02h,%0d\n",got,err);
if(err || got !== 8'h86) `uvm_fatal("bank_preflight","byte mismatch at 23068672")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd24117247);
$fwrite(fd,"24117247,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 24117247")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd24117248);
$fwrite(fd,"24117248,%02h,%0d\n",got,err);
if(err || got !== 8'hc1) `uvm_fatal("bank_preflight","byte mismatch at 24117248")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd25165823);
$fwrite(fd,"25165823,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 25165823")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd25165824);
$fwrite(fd,"25165824,%02h,%0d\n",got,err);
if(err || got !== 8'he5) `uvm_fatal("bank_preflight","byte mismatch at 25165824")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd26214399);
$fwrite(fd,"26214399,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 26214399")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd26214400);
$fwrite(fd,"26214400,%02h,%0d\n",got,err);
if(err || got !== 8'hfb) `uvm_fatal("bank_preflight","byte mismatch at 26214400")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd27262975);
$fwrite(fd,"27262975,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 27262975")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd27262976);
$fwrite(fd,"27262976,%02h,%0d\n",got,err);
if(err || got !== 8'h09) `uvm_fatal("bank_preflight","byte mismatch at 27262976")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd28311551);
$fwrite(fd,"28311551,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 28311551")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd28311552);
$fwrite(fd,"28311552,%02h,%0d\n",got,err);
if(err || got !== 8'h64) `uvm_fatal("bank_preflight","byte mismatch at 28311552")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd29360127);
$fwrite(fd,"29360127,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 29360127")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd29360128);
$fwrite(fd,"29360128,%02h,%0d\n",got,err);
if(err || got !== 8'h3d) `uvm_fatal("bank_preflight","byte mismatch at 29360128")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd30408703);
$fwrite(fd,"30408703,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 30408703")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd30408704);
$fwrite(fd,"30408704,%02h,%0d\n",got,err);
if(err || got !== 8'hab) `uvm_fatal("bank_preflight","byte mismatch at 30408704")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd31457279);
$fwrite(fd,"31457279,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 31457279")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd31457280);
$fwrite(fd,"31457280,%02h,%0d\n",got,err);
if(err || got !== 8'h21) `uvm_fatal("bank_preflight","byte mismatch at 31457280")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd32505855);
$fwrite(fd,"32505855,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 32505855")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd32505856);
$fwrite(fd,"32505856,%02h,%0d\n",got,err);
if(err || got !== 8'he1) `uvm_fatal("bank_preflight","byte mismatch at 32505856")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd33554431);
$fwrite(fd,"33554431,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 33554431")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd33554432);
$fwrite(fd,"33554432,%02h,%0d\n",got,err);
if(err || got !== 8'hc2) `uvm_fatal("bank_preflight","byte mismatch at 33554432")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd34603007);
$fwrite(fd,"34603007,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 34603007")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd34603008);
$fwrite(fd,"34603008,%02h,%0d\n",got,err);
if(err || got !== 8'hdd) `uvm_fatal("bank_preflight","byte mismatch at 34603008")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd35651583);
$fwrite(fd,"35651583,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 35651583")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd35651584);
$fwrite(fd,"35651584,%02h,%0d\n",got,err);
if(err || got !== 8'hc9) `uvm_fatal("bank_preflight","byte mismatch at 35651584")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd36700159);
$fwrite(fd,"36700159,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 36700159")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd36700160);
$fwrite(fd,"36700160,%02h,%0d\n",got,err);
if(err || got !== 8'hf7) `uvm_fatal("bank_preflight","byte mismatch at 36700160")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd37748735);
$fwrite(fd,"37748735,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 37748735")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd37748736);
$fwrite(fd,"37748736,%02h,%0d\n",got,err);
if(err || got !== 8'h18) `uvm_fatal("bank_preflight","byte mismatch at 37748736")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd38797311);
$fwrite(fd,"38797311,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 38797311")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd38797312);
$fwrite(fd,"38797312,%02h,%0d\n",got,err);
if(err || got !== 8'h43) `uvm_fatal("bank_preflight","byte mismatch at 38797312")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd39845887);
$fwrite(fd,"39845887,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 39845887")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd39845888);
$fwrite(fd,"39845888,%02h,%0d\n",got,err);
if(err || got !== 8'h9f) `uvm_fatal("bank_preflight","byte mismatch at 39845888")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd40894463);
$fwrite(fd,"40894463,%02h,%0d\n",got,err);
if(err || got !== 8'hb9) `uvm_fatal("bank_preflight","byte mismatch at 40894463")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd40894464);
$fwrite(fd,"40894464,%02h,%0d\n",got,err);
if(err || got !== 8'hb9) `uvm_fatal("bank_preflight","byte mismatch at 40894464")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd41943039);
$fwrite(fd,"41943039,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 41943039")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd41943040);
$fwrite(fd,"41943040,%02h,%0d\n",got,err);
if(err || got !== 8'h8e) `uvm_fatal("bank_preflight","byte mismatch at 41943040")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd42991615);
$fwrite(fd,"42991615,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 42991615")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd42991616);
$fwrite(fd,"42991616,%02h,%0d\n",got,err);
if(err || got !== 8'h65) `uvm_fatal("bank_preflight","byte mismatch at 42991616")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd44040191);
$fwrite(fd,"44040191,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 44040191")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd44040192);
$fwrite(fd,"44040192,%02h,%0d\n",got,err);
if(err || got !== 8'hbe) `uvm_fatal("bank_preflight","byte mismatch at 44040192")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd45088767);
$fwrite(fd,"45088767,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 45088767")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd45088768);
$fwrite(fd,"45088768,%02h,%0d\n",got,err);
if(err || got !== 8'hb6) `uvm_fatal("bank_preflight","byte mismatch at 45088768")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd46137343);
$fwrite(fd,"46137343,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 46137343")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd46137344);
$fwrite(fd,"46137344,%02h,%0d\n",got,err);
if(err || got !== 8'h98) `uvm_fatal("bank_preflight","byte mismatch at 46137344")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd47185919);
$fwrite(fd,"47185919,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 47185919")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd47185920);
$fwrite(fd,"47185920,%02h,%0d\n",got,err);
if(err || got !== 8'h6f) `uvm_fatal("bank_preflight","byte mismatch at 47185920")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd48234495);
$fwrite(fd,"48234495,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 48234495")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd48234496);
$fwrite(fd,"48234496,%02h,%0d\n",got,err);
if(err || got !== 8'h93) `uvm_fatal("bank_preflight","byte mismatch at 48234496")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd49283071);
$fwrite(fd,"49283071,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 49283071")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd49283072);
$fwrite(fd,"49283072,%02h,%0d\n",got,err);
if(err || got !== 8'he9) `uvm_fatal("bank_preflight","byte mismatch at 49283072")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd50331647);
$fwrite(fd,"50331647,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 50331647")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd50331648);
$fwrite(fd,"50331648,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 50331648")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd51380223);
$fwrite(fd,"51380223,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 51380223")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd51380224);
$fwrite(fd,"51380224,%02h,%0d\n",got,err);
if(err || got !== 8'h93) `uvm_fatal("bank_preflight","byte mismatch at 51380224")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd52428799);
$fwrite(fd,"52428799,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 52428799")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd52428800);
$fwrite(fd,"52428800,%02h,%0d\n",got,err);
if(err || got !== 8'hd1) `uvm_fatal("bank_preflight","byte mismatch at 52428800")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd53477375);
$fwrite(fd,"53477375,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 53477375")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd53477376);
$fwrite(fd,"53477376,%02h,%0d\n",got,err);
if(err || got !== 8'h86) `uvm_fatal("bank_preflight","byte mismatch at 53477376")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd54525951);
$fwrite(fd,"54525951,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 54525951")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd54525952);
$fwrite(fd,"54525952,%02h,%0d\n",got,err);
if(err || got !== 8'h62) `uvm_fatal("bank_preflight","byte mismatch at 54525952")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd55574527);
$fwrite(fd,"55574527,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 55574527")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd55574528);
$fwrite(fd,"55574528,%02h,%0d\n",got,err);
if(err || got !== 8'h9d) `uvm_fatal("bank_preflight","byte mismatch at 55574528")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd56623103);
$fwrite(fd,"56623103,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 56623103")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd56623104);
$fwrite(fd,"56623104,%02h,%0d\n",got,err);
if(err || got !== 8'h0e) `uvm_fatal("bank_preflight","byte mismatch at 56623104")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd57671679);
$fwrite(fd,"57671679,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 57671679")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd57671680);
$fwrite(fd,"57671680,%02h,%0d\n",got,err);
if(err || got !== 8'hee) `uvm_fatal("bank_preflight","byte mismatch at 57671680")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd58720255);
$fwrite(fd,"58720255,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 58720255")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd58720256);
$fwrite(fd,"58720256,%02h,%0d\n",got,err);
if(err || got !== 8'hab) `uvm_fatal("bank_preflight","byte mismatch at 58720256")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd59768831);
$fwrite(fd,"59768831,%02h,%0d\n",got,err);
if(err || got !== 8'hbd) `uvm_fatal("bank_preflight","byte mismatch at 59768831")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd59768832);
$fwrite(fd,"59768832,%02h,%0d\n",got,err);
if(err || got !== 8'h91) `uvm_fatal("bank_preflight","byte mismatch at 59768832")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd60817407);
$fwrite(fd,"60817407,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 60817407")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd60817408);
$fwrite(fd,"60817408,%02h,%0d\n",got,err);
if(err || got !== 8'h28) `uvm_fatal("bank_preflight","byte mismatch at 60817408")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd61865983);
$fwrite(fd,"61865983,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 61865983")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd61865984);
$fwrite(fd,"61865984,%02h,%0d\n",got,err);
if(err || got !== 8'hd0) `uvm_fatal("bank_preflight","byte mismatch at 61865984")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd62914559);
$fwrite(fd,"62914559,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 62914559")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd62914560);
$fwrite(fd,"62914560,%02h,%0d\n",got,err);
if(err || got !== 8'h9c) `uvm_fatal("bank_preflight","byte mismatch at 62914560")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd63963135);
$fwrite(fd,"63963135,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 63963135")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd63963136);
$fwrite(fd,"63963136,%02h,%0d\n",got,err);
if(err || got !== 8'h3f) `uvm_fatal("bank_preflight","byte mismatch at 63963136")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd65011711);
$fwrite(fd,"65011711,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 65011711")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd65011712);
$fwrite(fd,"65011712,%02h,%0d\n",got,err);
if(err || got !== 8'h75) `uvm_fatal("bank_preflight","byte mismatch at 65011712")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd66060287);
$fwrite(fd,"66060287,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 66060287")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd66060288);
$fwrite(fd,"66060288,%02h,%0d\n",got,err);
if(err || got !== 8'h25) `uvm_fatal("bank_preflight","byte mismatch at 66060288")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd67108863);
$fwrite(fd,"67108863,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 67108863")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd67108864);
$fwrite(fd,"67108864,%02h,%0d\n",got,err);
if(err || got !== 8'hf2) `uvm_fatal("bank_preflight","byte mismatch at 67108864")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd68157439);
$fwrite(fd,"68157439,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 68157439")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd68157440);
$fwrite(fd,"68157440,%02h,%0d\n",got,err);
if(err || got !== 8'h51) `uvm_fatal("bank_preflight","byte mismatch at 68157440")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd69206015);
$fwrite(fd,"69206015,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 69206015")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd69206016);
$fwrite(fd,"69206016,%02h,%0d\n",got,err);
if(err || got !== 8'hff) `uvm_fatal("bank_preflight","byte mismatch at 69206016")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd70254591);
$fwrite(fd,"70254591,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 70254591")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd70254592);
$fwrite(fd,"70254592,%02h,%0d\n",got,err);
if(err || got !== 8'h6a) `uvm_fatal("bank_preflight","byte mismatch at 70254592")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd71303167);
$fwrite(fd,"71303167,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 71303167")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd71303168);
$fwrite(fd,"71303168,%02h,%0d\n",got,err);
if(err || got !== 8'h2f) `uvm_fatal("bank_preflight","byte mismatch at 71303168")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd72351743);
$fwrite(fd,"72351743,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 72351743")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd72351744);
$fwrite(fd,"72351744,%02h,%0d\n",got,err);
if(err || got !== 8'h24) `uvm_fatal("bank_preflight","byte mismatch at 72351744")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd73400319);
$fwrite(fd,"73400319,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 73400319")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd73400320);
$fwrite(fd,"73400320,%02h,%0d\n",got,err);
if(err || got !== 8'h02) `uvm_fatal("bank_preflight","byte mismatch at 73400320")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd74448895);
$fwrite(fd,"74448895,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 74448895")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd74448896);
$fwrite(fd,"74448896,%02h,%0d\n",got,err);
if(err || got !== 8'hf0) `uvm_fatal("bank_preflight","byte mismatch at 74448896")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd75497471);
$fwrite(fd,"75497471,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 75497471")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd75497472);
$fwrite(fd,"75497472,%02h,%0d\n",got,err);
if(err || got !== 8'h91) `uvm_fatal("bank_preflight","byte mismatch at 75497472")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd76546047);
$fwrite(fd,"76546047,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 76546047")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd76546048);
$fwrite(fd,"76546048,%02h,%0d\n",got,err);
if(err || got !== 8'hf3) `uvm_fatal("bank_preflight","byte mismatch at 76546048")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd77594623);
$fwrite(fd,"77594623,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 77594623")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd77594624);
$fwrite(fd,"77594624,%02h,%0d\n",got,err);
if(err || got !== 8'h5c) `uvm_fatal("bank_preflight","byte mismatch at 77594624")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd78643199);
$fwrite(fd,"78643199,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 78643199")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd78643200);
$fwrite(fd,"78643200,%02h,%0d\n",got,err);
if(err || got !== 8'h25) `uvm_fatal("bank_preflight","byte mismatch at 78643200")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd79691775);
$fwrite(fd,"79691775,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 79691775")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd79691776);
$fwrite(fd,"79691776,%02h,%0d\n",got,err);
if(err || got !== 8'hd4) `uvm_fatal("bank_preflight","byte mismatch at 79691776")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd80740351);
$fwrite(fd,"80740351,%02h,%0d\n",got,err);
if(err || got !== 8'hb9) `uvm_fatal("bank_preflight","byte mismatch at 80740351")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd80740352);
$fwrite(fd,"80740352,%02h,%0d\n",got,err);
if(err || got !== 8'hb3) `uvm_fatal("bank_preflight","byte mismatch at 80740352")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd81788927);
$fwrite(fd,"81788927,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 81788927")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd81788928);
$fwrite(fd,"81788928,%02h,%0d\n",got,err);
if(err || got !== 8'h81) `uvm_fatal("bank_preflight","byte mismatch at 81788928")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd82837503);
$fwrite(fd,"82837503,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 82837503")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd82837504);
$fwrite(fd,"82837504,%02h,%0d\n",got,err);
if(err || got !== 8'h87) `uvm_fatal("bank_preflight","byte mismatch at 82837504")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd83886079);
$fwrite(fd,"83886079,%02h,%0d\n",got,err);
if(err || got !== 8'hb9) `uvm_fatal("bank_preflight","byte mismatch at 83886079")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd83886080);
$fwrite(fd,"83886080,%02h,%0d\n",got,err);
if(err || got !== 8'h2f) `uvm_fatal("bank_preflight","byte mismatch at 83886080")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd84934655);
$fwrite(fd,"84934655,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 84934655")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd84934656);
$fwrite(fd,"84934656,%02h,%0d\n",got,err);
if(err || got !== 8'h1a) `uvm_fatal("bank_preflight","byte mismatch at 84934656")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd85983231);
$fwrite(fd,"85983231,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 85983231")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd85983232);
$fwrite(fd,"85983232,%02h,%0d\n",got,err);
if(err || got !== 8'h93) `uvm_fatal("bank_preflight","byte mismatch at 85983232")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd87031807);
$fwrite(fd,"87031807,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 87031807")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd87031808);
$fwrite(fd,"87031808,%02h,%0d\n",got,err);
if(err || got !== 8'he2) `uvm_fatal("bank_preflight","byte mismatch at 87031808")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd88080383);
$fwrite(fd,"88080383,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 88080383")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd88080384);
$fwrite(fd,"88080384,%02h,%0d\n",got,err);
if(err || got !== 8'hb6) `uvm_fatal("bank_preflight","byte mismatch at 88080384")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd89128959);
$fwrite(fd,"89128959,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 89128959")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd89128960);
$fwrite(fd,"89128960,%02h,%0d\n",got,err);
if(err || got !== 8'hfb) `uvm_fatal("bank_preflight","byte mismatch at 89128960")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd90177535);
$fwrite(fd,"90177535,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 90177535")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd90177536);
$fwrite(fd,"90177536,%02h,%0d\n",got,err);
if(err || got !== 8'hec) `uvm_fatal("bank_preflight","byte mismatch at 90177536")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd91226111);
$fwrite(fd,"91226111,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 91226111")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd91226112);
$fwrite(fd,"91226112,%02h,%0d\n",got,err);
if(err || got !== 8'h2d) `uvm_fatal("bank_preflight","byte mismatch at 91226112")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd92274687);
$fwrite(fd,"92274687,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 92274687")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd92274688);
$fwrite(fd,"92274688,%02h,%0d\n",got,err);
if(err || got !== 8'h38) `uvm_fatal("bank_preflight","byte mismatch at 92274688")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd93323263);
$fwrite(fd,"93323263,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 93323263")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd93323264);
$fwrite(fd,"93323264,%02h,%0d\n",got,err);
if(err || got !== 8'h3e) `uvm_fatal("bank_preflight","byte mismatch at 93323264")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd94371839);
$fwrite(fd,"94371839,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 94371839")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd94371840);
$fwrite(fd,"94371840,%02h,%0d\n",got,err);
if(err || got !== 8'he2) `uvm_fatal("bank_preflight","byte mismatch at 94371840")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd95420415);
$fwrite(fd,"95420415,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 95420415")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd95420416);
$fwrite(fd,"95420416,%02h,%0d\n",got,err);
if(err || got !== 8'hd1) `uvm_fatal("bank_preflight","byte mismatch at 95420416")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd96468991);
$fwrite(fd,"96468991,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 96468991")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd96468992);
$fwrite(fd,"96468992,%02h,%0d\n",got,err);
if(err || got !== 8'h84) `uvm_fatal("bank_preflight","byte mismatch at 96468992")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd97517567);
$fwrite(fd,"97517567,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 97517567")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd97517568);
$fwrite(fd,"97517568,%02h,%0d\n",got,err);
if(err || got !== 8'he0) `uvm_fatal("bank_preflight","byte mismatch at 97517568")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd98566143);
$fwrite(fd,"98566143,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 98566143")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd98566144);
$fwrite(fd,"98566144,%02h,%0d\n",got,err);
if(err || got !== 8'h10) `uvm_fatal("bank_preflight","byte mismatch at 98566144")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd99614719);
$fwrite(fd,"99614719,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 99614719")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd99614720);
$fwrite(fd,"99614720,%02h,%0d\n",got,err);
if(err || got !== 8'hc3) `uvm_fatal("bank_preflight","byte mismatch at 99614720")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd100663295);
$fwrite(fd,"100663295,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 100663295")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd100663296);
$fwrite(fd,"100663296,%02h,%0d\n",got,err);
if(err || got !== 8'h74) `uvm_fatal("bank_preflight","byte mismatch at 100663296")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd101711871);
$fwrite(fd,"101711871,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 101711871")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd101711872);
$fwrite(fd,"101711872,%02h,%0d\n",got,err);
if(err || got !== 8'h88) `uvm_fatal("bank_preflight","byte mismatch at 101711872")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd102760447);
$fwrite(fd,"102760447,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 102760447")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd102760448);
$fwrite(fd,"102760448,%02h,%0d\n",got,err);
if(err || got !== 8'hb0) `uvm_fatal("bank_preflight","byte mismatch at 102760448")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd103809023);
$fwrite(fd,"103809023,%02h,%0d\n",got,err);
if(err || got !== 8'hbd) `uvm_fatal("bank_preflight","byte mismatch at 103809023")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd103809024);
$fwrite(fd,"103809024,%02h,%0d\n",got,err);
if(err || got !== 8'h28) `uvm_fatal("bank_preflight","byte mismatch at 103809024")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd104857599);
$fwrite(fd,"104857599,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 104857599")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd104857600);
$fwrite(fd,"104857600,%02h,%0d\n",got,err);
if(err || got !== 8'h50) `uvm_fatal("bank_preflight","byte mismatch at 104857600")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd105906175);
$fwrite(fd,"105906175,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 105906175")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd105906176);
$fwrite(fd,"105906176,%02h,%0d\n",got,err);
if(err || got !== 8'h9a) `uvm_fatal("bank_preflight","byte mismatch at 105906176")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd106954751);
$fwrite(fd,"106954751,%02h,%0d\n",got,err);
if(err || got !== 8'hb8) `uvm_fatal("bank_preflight","byte mismatch at 106954751")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd106954752);
$fwrite(fd,"106954752,%02h,%0d\n",got,err);
if(err || got !== 8'h32) `uvm_fatal("bank_preflight","byte mismatch at 106954752")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd108003327);
$fwrite(fd,"108003327,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 108003327")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd108003328);
$fwrite(fd,"108003328,%02h,%0d\n",got,err);
if(err || got !== 8'h01) `uvm_fatal("bank_preflight","byte mismatch at 108003328")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd109051903);
$fwrite(fd,"109051903,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 109051903")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd109051904);
$fwrite(fd,"109051904,%02h,%0d\n",got,err);
if(err || got !== 8'hfd) `uvm_fatal("bank_preflight","byte mismatch at 109051904")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd110100479);
$fwrite(fd,"110100479,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 110100479")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd110100480);
$fwrite(fd,"110100480,%02h,%0d\n",got,err);
if(err || got !== 8'ha6) `uvm_fatal("bank_preflight","byte mismatch at 110100480")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd111149055);
$fwrite(fd,"111149055,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 111149055")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd111149056);
$fwrite(fd,"111149056,%02h,%0d\n",got,err);
if(err || got !== 8'he1) `uvm_fatal("bank_preflight","byte mismatch at 111149056")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd112197631);
$fwrite(fd,"112197631,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 112197631")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd112197632);
$fwrite(fd,"112197632,%02h,%0d\n",got,err);
if(err || got !== 8'h6c) `uvm_fatal("bank_preflight","byte mismatch at 112197632")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd113246207);
$fwrite(fd,"113246207,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 113246207")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd113246208);
$fwrite(fd,"113246208,%02h,%0d\n",got,err);
if(err || got !== 8'hb7) `uvm_fatal("bank_preflight","byte mismatch at 113246208")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd114294783);
$fwrite(fd,"114294783,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 114294783")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd114294784);
$fwrite(fd,"114294784,%02h,%0d\n",got,err);
if(err || got !== 8'hd0) `uvm_fatal("bank_preflight","byte mismatch at 114294784")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd115343359);
$fwrite(fd,"115343359,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 115343359")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd115343360);
$fwrite(fd,"115343360,%02h,%0d\n",got,err);
if(err || got !== 8'hc5) `uvm_fatal("bank_preflight","byte mismatch at 115343360")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd116391935);
$fwrite(fd,"116391935,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 116391935")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd116391936);
$fwrite(fd,"116391936,%02h,%0d\n",got,err);
if(err || got !== 8'hfd) `uvm_fatal("bank_preflight","byte mismatch at 116391936")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd117440511);
$fwrite(fd,"117440511,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 117440511")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd117440512);
$fwrite(fd,"117440512,%02h,%0d\n",got,err);
if(err || got !== 8'h81) `uvm_fatal("bank_preflight","byte mismatch at 117440512")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd118489087);
$fwrite(fd,"118489087,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 118489087")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd118489088);
$fwrite(fd,"118489088,%02h,%0d\n",got,err);
if(err || got !== 8'hc3) `uvm_fatal("bank_preflight","byte mismatch at 118489088")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd119537663);
$fwrite(fd,"119537663,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 119537663")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd119537664);
$fwrite(fd,"119537664,%02h,%0d\n",got,err);
if(err || got !== 8'ha0) `uvm_fatal("bank_preflight","byte mismatch at 119537664")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd120586239);
$fwrite(fd,"120586239,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 120586239")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd120586240);
$fwrite(fd,"120586240,%02h,%0d\n",got,err);
if(err || got !== 8'h54) `uvm_fatal("bank_preflight","byte mismatch at 120586240")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd121634815);
$fwrite(fd,"121634815,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 121634815")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd121634816);
$fwrite(fd,"121634816,%02h,%0d\n",got,err);
if(err || got !== 8'hb0) `uvm_fatal("bank_preflight","byte mismatch at 121634816")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd122683391);
$fwrite(fd,"122683391,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 122683391")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd122683392);
$fwrite(fd,"122683392,%02h,%0d\n",got,err);
if(err || got !== 8'h1d) `uvm_fatal("bank_preflight","byte mismatch at 122683392")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd123731967);
$fwrite(fd,"123731967,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 123731967")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd123731968);
$fwrite(fd,"123731968,%02h,%0d\n",got,err);
if(err || got !== 8'h7a) `uvm_fatal("bank_preflight","byte mismatch at 123731968")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd124780543);
$fwrite(fd,"124780543,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 124780543")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd124780544);
$fwrite(fd,"124780544,%02h,%0d\n",got,err);
if(err || got !== 8'h65) `uvm_fatal("bank_preflight","byte mismatch at 124780544")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd125829119);
$fwrite(fd,"125829119,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 125829119")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd125829120);
$fwrite(fd,"125829120,%02h,%0d\n",got,err);
if(err || got !== 8'h85) `uvm_fatal("bank_preflight","byte mismatch at 125829120")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd126877695);
$fwrite(fd,"126877695,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 126877695")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd126877696);
$fwrite(fd,"126877696,%02h,%0d\n",got,err);
if(err || got !== 8'hd1) `uvm_fatal("bank_preflight","byte mismatch at 126877696")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd127926271);
$fwrite(fd,"127926271,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 127926271")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd127926272);
$fwrite(fd,"127926272,%02h,%0d\n",got,err);
if(err || got !== 8'h68) `uvm_fatal("bank_preflight","byte mismatch at 127926272")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd128974847);
$fwrite(fd,"128974847,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 128974847")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd128974848);
$fwrite(fd,"128974848,%02h,%0d\n",got,err);
if(err || got !== 8'hef) `uvm_fatal("bank_preflight","byte mismatch at 128974848")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd130023423);
$fwrite(fd,"130023423,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 130023423")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd130023424);
$fwrite(fd,"130023424,%02h,%0d\n",got,err);
if(err || got !== 8'hd1) `uvm_fatal("bank_preflight","byte mismatch at 130023424")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd131071999);
$fwrite(fd,"131071999,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 131071999")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd131072000);
$fwrite(fd,"131072000,%02h,%0d\n",got,err);
if(err || got !== 8'hc1) `uvm_fatal("bank_preflight","byte mismatch at 131072000")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd132120575);
$fwrite(fd,"132120575,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 132120575")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd132120576);
$fwrite(fd,"132120576,%02h,%0d\n",got,err);
if(err || got !== 8'h5e) `uvm_fatal("bank_preflight","byte mismatch at 132120576")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd133169151);
$fwrite(fd,"133169151,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 133169151")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd133169152);
$fwrite(fd,"133169152,%02h,%0d\n",got,err);
if(err || got !== 8'h6b) `uvm_fatal("bank_preflight","byte mismatch at 133169152")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd134217727);
$fwrite(fd,"134217727,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 134217727")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd134217728);
$fwrite(fd,"134217728,%02h,%0d\n",got,err);
if(err || got !== 8'h2f) `uvm_fatal("bank_preflight","byte mismatch at 134217728")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd135266303);
$fwrite(fd,"135266303,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 135266303")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd135266304);
$fwrite(fd,"135266304,%02h,%0d\n",got,err);
if(err || got !== 8'h90) `uvm_fatal("bank_preflight","byte mismatch at 135266304")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd136314879);
$fwrite(fd,"136314879,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 136314879")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd136314880);
$fwrite(fd,"136314880,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 136314880")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd137363455);
$fwrite(fd,"137363455,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 137363455")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd137363456);
$fwrite(fd,"137363456,%02h,%0d\n",got,err);
if(err || got !== 8'hce) `uvm_fatal("bank_preflight","byte mismatch at 137363456")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd138412031);
$fwrite(fd,"138412031,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 138412031")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd138412032);
$fwrite(fd,"138412032,%02h,%0d\n",got,err);
if(err || got !== 8'h22) `uvm_fatal("bank_preflight","byte mismatch at 138412032")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd139460607);
$fwrite(fd,"139460607,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 139460607")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd139460608);
$fwrite(fd,"139460608,%02h,%0d\n",got,err);
if(err || got !== 8'hc5) `uvm_fatal("bank_preflight","byte mismatch at 139460608")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd140509183);
$fwrite(fd,"140509183,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 140509183")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd140509184);
$fwrite(fd,"140509184,%02h,%0d\n",got,err);
if(err || got !== 8'h7a) `uvm_fatal("bank_preflight","byte mismatch at 140509184")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd141557759);
$fwrite(fd,"141557759,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 141557759")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd141557760);
$fwrite(fd,"141557760,%02h,%0d\n",got,err);
if(err || got !== 8'h8a) `uvm_fatal("bank_preflight","byte mismatch at 141557760")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd142606335);
$fwrite(fd,"142606335,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 142606335")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd142606336);
$fwrite(fd,"142606336,%02h,%0d\n",got,err);
if(err || got !== 8'haf) `uvm_fatal("bank_preflight","byte mismatch at 142606336")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd143654911);
$fwrite(fd,"143654911,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 143654911")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd143654912);
$fwrite(fd,"143654912,%02h,%0d\n",got,err);
if(err || got !== 8'he5) `uvm_fatal("bank_preflight","byte mismatch at 143654912")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd144703487);
$fwrite(fd,"144703487,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 144703487")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd144703488);
$fwrite(fd,"144703488,%02h,%0d\n",got,err);
if(err || got !== 8'h2d) `uvm_fatal("bank_preflight","byte mismatch at 144703488")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd145752063);
$fwrite(fd,"145752063,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 145752063")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd145752064);
$fwrite(fd,"145752064,%02h,%0d\n",got,err);
if(err || got !== 8'h62) `uvm_fatal("bank_preflight","byte mismatch at 145752064")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd146800639);
$fwrite(fd,"146800639,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 146800639")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd146800640);
$fwrite(fd,"146800640,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 146800640")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd147849215);
$fwrite(fd,"147849215,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 147849215")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd147849216);
$fwrite(fd,"147849216,%02h,%0d\n",got,err);
if(err || got !== 8'hcf) `uvm_fatal("bank_preflight","byte mismatch at 147849216")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd148897791);
$fwrite(fd,"148897791,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 148897791")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd148897792);
$fwrite(fd,"148897792,%02h,%0d\n",got,err);
if(err || got !== 8'hd7) `uvm_fatal("bank_preflight","byte mismatch at 148897792")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd149946367);
$fwrite(fd,"149946367,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 149946367")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd149946368);
$fwrite(fd,"149946368,%02h,%0d\n",got,err);
if(err || got !== 8'h23) `uvm_fatal("bank_preflight","byte mismatch at 149946368")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd150994943);
$fwrite(fd,"150994943,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 150994943")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd150994944);
$fwrite(fd,"150994944,%02h,%0d\n",got,err);
if(err || got !== 8'h7f) `uvm_fatal("bank_preflight","byte mismatch at 150994944")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd152043519);
$fwrite(fd,"152043519,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 152043519")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd152043520);
$fwrite(fd,"152043520,%02h,%0d\n",got,err);
if(err || got !== 8'h26) `uvm_fatal("bank_preflight","byte mismatch at 152043520")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd153092095);
$fwrite(fd,"153092095,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 153092095")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd153092096);
$fwrite(fd,"153092096,%02h,%0d\n",got,err);
if(err || got !== 8'he2) `uvm_fatal("bank_preflight","byte mismatch at 153092096")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd154140671);
$fwrite(fd,"154140671,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 154140671")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd154140672);
$fwrite(fd,"154140672,%02h,%0d\n",got,err);
if(err || got !== 8'h7d) `uvm_fatal("bank_preflight","byte mismatch at 154140672")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd155189247);
$fwrite(fd,"155189247,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 155189247")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd155189248);
$fwrite(fd,"155189248,%02h,%0d\n",got,err);
if(err || got !== 8'h17) `uvm_fatal("bank_preflight","byte mismatch at 155189248")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd156237823);
$fwrite(fd,"156237823,%02h,%0d\n",got,err);
if(err || got !== 8'hbd) `uvm_fatal("bank_preflight","byte mismatch at 156237823")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd156237824);
$fwrite(fd,"156237824,%02h,%0d\n",got,err);
if(err || got !== 8'hda) `uvm_fatal("bank_preflight","byte mismatch at 156237824")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd157286399);
$fwrite(fd,"157286399,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 157286399")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd157286400);
$fwrite(fd,"157286400,%02h,%0d\n",got,err);
if(err || got !== 8'h96) `uvm_fatal("bank_preflight","byte mismatch at 157286400")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd158334975);
$fwrite(fd,"158334975,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 158334975")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd158334976);
$fwrite(fd,"158334976,%02h,%0d\n",got,err);
if(err || got !== 8'h4a) `uvm_fatal("bank_preflight","byte mismatch at 158334976")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd159383551);
$fwrite(fd,"159383551,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 159383551")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd159383552);
$fwrite(fd,"159383552,%02h,%0d\n",got,err);
if(err || got !== 8'h86) `uvm_fatal("bank_preflight","byte mismatch at 159383552")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd160432127);
$fwrite(fd,"160432127,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 160432127")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd160432128);
$fwrite(fd,"160432128,%02h,%0d\n",got,err);
if(err || got !== 8'h1c) `uvm_fatal("bank_preflight","byte mismatch at 160432128")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd161480703);
$fwrite(fd,"161480703,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 161480703")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd161480704);
$fwrite(fd,"161480704,%02h,%0d\n",got,err);
if(err || got !== 8'he5) `uvm_fatal("bank_preflight","byte mismatch at 161480704")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd162529279);
$fwrite(fd,"162529279,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 162529279")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd162529280);
$fwrite(fd,"162529280,%02h,%0d\n",got,err);
if(err || got !== 8'h97) `uvm_fatal("bank_preflight","byte mismatch at 162529280")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd163577855);
$fwrite(fd,"163577855,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 163577855")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd163577856);
$fwrite(fd,"163577856,%02h,%0d\n",got,err);
if(err || got !== 8'h18) `uvm_fatal("bank_preflight","byte mismatch at 163577856")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd164626431);
$fwrite(fd,"164626431,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 164626431")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd164626432);
$fwrite(fd,"164626432,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 164626432")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd165675007);
$fwrite(fd,"165675007,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 165675007")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd165675008);
$fwrite(fd,"165675008,%02h,%0d\n",got,err);
if(err || got !== 8'h20) `uvm_fatal("bank_preflight","byte mismatch at 165675008")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd166723583);
$fwrite(fd,"166723583,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 166723583")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd166723584);
$fwrite(fd,"166723584,%02h,%0d\n",got,err);
if(err || got !== 8'hf8) `uvm_fatal("bank_preflight","byte mismatch at 166723584")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd167772159);
$fwrite(fd,"167772159,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 167772159")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd167772160);
$fwrite(fd,"167772160,%02h,%0d\n",got,err);
if(err || got !== 8'h54) `uvm_fatal("bank_preflight","byte mismatch at 167772160")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd168820735);
$fwrite(fd,"168820735,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 168820735")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd168820736);
$fwrite(fd,"168820736,%02h,%0d\n",got,err);
if(err || got !== 8'h1b) `uvm_fatal("bank_preflight","byte mismatch at 168820736")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd169869311);
$fwrite(fd,"169869311,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 169869311")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd169869312);
$fwrite(fd,"169869312,%02h,%0d\n",got,err);
if(err || got !== 8'h21) `uvm_fatal("bank_preflight","byte mismatch at 169869312")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd170917887);
$fwrite(fd,"170917887,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 170917887")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd170917888);
$fwrite(fd,"170917888,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 170917888")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd171966463);
$fwrite(fd,"171966463,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 171966463")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd171966464);
$fwrite(fd,"171966464,%02h,%0d\n",got,err);
if(err || got !== 8'hd5) `uvm_fatal("bank_preflight","byte mismatch at 171966464")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd173015039);
$fwrite(fd,"173015039,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 173015039")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd173015040);
$fwrite(fd,"173015040,%02h,%0d\n",got,err);
if(err || got !== 8'he8) `uvm_fatal("bank_preflight","byte mismatch at 173015040")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd174063615);
$fwrite(fd,"174063615,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 174063615")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd174063616);
$fwrite(fd,"174063616,%02h,%0d\n",got,err);
if(err || got !== 8'h51) `uvm_fatal("bank_preflight","byte mismatch at 174063616")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd175112191);
$fwrite(fd,"175112191,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 175112191")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd175112192);
$fwrite(fd,"175112192,%02h,%0d\n",got,err);
if(err || got !== 8'h89) `uvm_fatal("bank_preflight","byte mismatch at 175112192")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd176160767);
$fwrite(fd,"176160767,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 176160767")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd176160768);
$fwrite(fd,"176160768,%02h,%0d\n",got,err);
if(err || got !== 8'h12) `uvm_fatal("bank_preflight","byte mismatch at 176160768")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd177209343);
$fwrite(fd,"177209343,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 177209343")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd177209344);
$fwrite(fd,"177209344,%02h,%0d\n",got,err);
if(err || got !== 8'h1f) `uvm_fatal("bank_preflight","byte mismatch at 177209344")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd178257919);
$fwrite(fd,"178257919,%02h,%0d\n",got,err);
if(err || got !== 8'h39) `uvm_fatal("bank_preflight","byte mismatch at 178257919")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd178257920);
$fwrite(fd,"178257920,%02h,%0d\n",got,err);
if(err || got !== 8'hc0) `uvm_fatal("bank_preflight","byte mismatch at 178257920")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd179306495);
$fwrite(fd,"179306495,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 179306495")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd179306496);
$fwrite(fd,"179306496,%02h,%0d\n",got,err);
if(err || got !== 8'h07) `uvm_fatal("bank_preflight","byte mismatch at 179306496")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd180355071);
$fwrite(fd,"180355071,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 180355071")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd180355072);
$fwrite(fd,"180355072,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 180355072")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd181403647);
$fwrite(fd,"181403647,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 181403647")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd181403648);
$fwrite(fd,"181403648,%02h,%0d\n",got,err);
if(err || got !== 8'hf6) `uvm_fatal("bank_preflight","byte mismatch at 181403648")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd182452223);
$fwrite(fd,"182452223,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 182452223")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd182452224);
$fwrite(fd,"182452224,%02h,%0d\n",got,err);
if(err || got !== 8'h68) `uvm_fatal("bank_preflight","byte mismatch at 182452224")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd183500799);
$fwrite(fd,"183500799,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 183500799")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd183500800);
$fwrite(fd,"183500800,%02h,%0d\n",got,err);
if(err || got !== 8'hc1) `uvm_fatal("bank_preflight","byte mismatch at 183500800")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd184549375);
$fwrite(fd,"184549375,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 184549375")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd184549376);
$fwrite(fd,"184549376,%02h,%0d\n",got,err);
if(err || got !== 8'hb1) `uvm_fatal("bank_preflight","byte mismatch at 184549376")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd185597951);
$fwrite(fd,"185597951,%02h,%0d\n",got,err);
if(err || got !== 8'h3d) `uvm_fatal("bank_preflight","byte mismatch at 185597951")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd185597952);
$fwrite(fd,"185597952,%02h,%0d\n",got,err);
if(err || got !== 8'h9b) `uvm_fatal("bank_preflight","byte mismatch at 185597952")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd186646527);
$fwrite(fd,"186646527,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 186646527")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd186646528);
$fwrite(fd,"186646528,%02h,%0d\n",got,err);
if(err || got !== 8'h99) `uvm_fatal("bank_preflight","byte mismatch at 186646528")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd187695103);
$fwrite(fd,"187695103,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 187695103")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd187695104);
$fwrite(fd,"187695104,%02h,%0d\n",got,err);
if(err || got !== 8'h52) `uvm_fatal("bank_preflight","byte mismatch at 187695104")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd188743679);
$fwrite(fd,"188743679,%02h,%0d\n",got,err);
if(err || got !== 8'h3d) `uvm_fatal("bank_preflight","byte mismatch at 188743679")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd188743680);
$fwrite(fd,"188743680,%02h,%0d\n",got,err);
if(err || got !== 8'h8e) `uvm_fatal("bank_preflight","byte mismatch at 188743680")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd189792255);
$fwrite(fd,"189792255,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 189792255")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd189792256);
$fwrite(fd,"189792256,%02h,%0d\n",got,err);
if(err || got !== 8'h82) `uvm_fatal("bank_preflight","byte mismatch at 189792256")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd190840831);
$fwrite(fd,"190840831,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 190840831")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd190840832);
$fwrite(fd,"190840832,%02h,%0d\n",got,err);
if(err || got !== 8'h86) `uvm_fatal("bank_preflight","byte mismatch at 190840832")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd191889407);
$fwrite(fd,"191889407,%02h,%0d\n",got,err);
if(err || got !== 8'h39) `uvm_fatal("bank_preflight","byte mismatch at 191889407")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd191889408);
$fwrite(fd,"191889408,%02h,%0d\n",got,err);
if(err || got !== 8'he2) `uvm_fatal("bank_preflight","byte mismatch at 191889408")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd192937983);
$fwrite(fd,"192937983,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 192937983")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd192937984);
$fwrite(fd,"192937984,%02h,%0d\n",got,err);
if(err || got !== 8'h19) `uvm_fatal("bank_preflight","byte mismatch at 192937984")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd193986559);
$fwrite(fd,"193986559,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 193986559")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd193986560);
$fwrite(fd,"193986560,%02h,%0d\n",got,err);
if(err || got !== 8'ha0) `uvm_fatal("bank_preflight","byte mismatch at 193986560")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd195035135);
$fwrite(fd,"195035135,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 195035135")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd195035136);
$fwrite(fd,"195035136,%02h,%0d\n",got,err);
if(err || got !== 8'hab) `uvm_fatal("bank_preflight","byte mismatch at 195035136")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd196083711);
$fwrite(fd,"196083711,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 196083711")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd196083712);
$fwrite(fd,"196083712,%02h,%0d\n",got,err);
if(err || got !== 8'h83) `uvm_fatal("bank_preflight","byte mismatch at 196083712")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd197132287);
$fwrite(fd,"197132287,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 197132287")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd197132288);
$fwrite(fd,"197132288,%02h,%0d\n",got,err);
if(err || got !== 8'h2c) `uvm_fatal("bank_preflight","byte mismatch at 197132288")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd198180863);
$fwrite(fd,"198180863,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 198180863")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd198180864);
$fwrite(fd,"198180864,%02h,%0d\n",got,err);
if(err || got !== 8'h1e) `uvm_fatal("bank_preflight","byte mismatch at 198180864")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd199229439);
$fwrite(fd,"199229439,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 199229439")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd199229440);
$fwrite(fd,"199229440,%02h,%0d\n",got,err);
if(err || got !== 8'hc6) `uvm_fatal("bank_preflight","byte mismatch at 199229440")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd200278015);
$fwrite(fd,"200278015,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 200278015")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd200278016);
$fwrite(fd,"200278016,%02h,%0d\n",got,err);
if(err || got !== 8'h84) `uvm_fatal("bank_preflight","byte mismatch at 200278016")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd201326591);
$fwrite(fd,"201326591,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 201326591")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd201326592);
$fwrite(fd,"201326592,%02h,%0d\n",got,err);
if(err || got !== 8'hda) `uvm_fatal("bank_preflight","byte mismatch at 201326592")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd202375167);
$fwrite(fd,"202375167,%02h,%0d\n",got,err);
if(err || got !== 8'h3d) `uvm_fatal("bank_preflight","byte mismatch at 202375167")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd202375168);
$fwrite(fd,"202375168,%02h,%0d\n",got,err);
if(err || got !== 8'h81) `uvm_fatal("bank_preflight","byte mismatch at 202375168")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd203423743);
$fwrite(fd,"203423743,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 203423743")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd203423744);
$fwrite(fd,"203423744,%02h,%0d\n",got,err);
if(err || got !== 8'hcd) `uvm_fatal("bank_preflight","byte mismatch at 203423744")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd204472319);
$fwrite(fd,"204472319,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 204472319")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd204472320);
$fwrite(fd,"204472320,%02h,%0d\n",got,err);
if(err || got !== 8'h16) `uvm_fatal("bank_preflight","byte mismatch at 204472320")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd205520895);
$fwrite(fd,"205520895,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 205520895")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd205520896);
$fwrite(fd,"205520896,%02h,%0d\n",got,err);
if(err || got !== 8'h2b) `uvm_fatal("bank_preflight","byte mismatch at 205520896")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd206569471);
$fwrite(fd,"206569471,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 206569471")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd206569472);
$fwrite(fd,"206569472,%02h,%0d\n",got,err);
if(err || got !== 8'h40) `uvm_fatal("bank_preflight","byte mismatch at 206569472")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd207618047);
$fwrite(fd,"207618047,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 207618047")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd207618048);
$fwrite(fd,"207618048,%02h,%0d\n",got,err);
if(err || got !== 8'h14) `uvm_fatal("bank_preflight","byte mismatch at 207618048")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd208666623);
$fwrite(fd,"208666623,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 208666623")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd208666624);
$fwrite(fd,"208666624,%02h,%0d\n",got,err);
if(err || got !== 8'ha1) `uvm_fatal("bank_preflight","byte mismatch at 208666624")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd209715199);
$fwrite(fd,"209715199,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 209715199")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd209715200);
$fwrite(fd,"209715200,%02h,%0d\n",got,err);
if(err || got !== 8'h1c) `uvm_fatal("bank_preflight","byte mismatch at 209715200")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd210763775);
$fwrite(fd,"210763775,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 210763775")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd210763776);
$fwrite(fd,"210763776,%02h,%0d\n",got,err);
if(err || got !== 8'hb7) `uvm_fatal("bank_preflight","byte mismatch at 210763776")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd211812351);
$fwrite(fd,"211812351,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 211812351")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd211812352);
$fwrite(fd,"211812352,%02h,%0d\n",got,err);
if(err || got !== 8'h48) `uvm_fatal("bank_preflight","byte mismatch at 211812352")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd212860927);
$fwrite(fd,"212860927,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 212860927")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd212860928);
$fwrite(fd,"212860928,%02h,%0d\n",got,err);
if(err || got !== 8'hc2) `uvm_fatal("bank_preflight","byte mismatch at 212860928")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd213909503);
$fwrite(fd,"213909503,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 213909503")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd213909504);
$fwrite(fd,"213909504,%02h,%0d\n",got,err);
if(err || got !== 8'h29) `uvm_fatal("bank_preflight","byte mismatch at 213909504")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd214958079);
$fwrite(fd,"214958079,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 214958079")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd214958080);
$fwrite(fd,"214958080,%02h,%0d\n",got,err);
if(err || got !== 8'h4e) `uvm_fatal("bank_preflight","byte mismatch at 214958080")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd216006655);
$fwrite(fd,"216006655,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 216006655")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd216006656);
$fwrite(fd,"216006656,%02h,%0d\n",got,err);
if(err || got !== 8'h28) `uvm_fatal("bank_preflight","byte mismatch at 216006656")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd217055231);
$fwrite(fd,"217055231,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 217055231")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd217055232);
$fwrite(fd,"217055232,%02h,%0d\n",got,err);
if(err || got !== 8'h24) `uvm_fatal("bank_preflight","byte mismatch at 217055232")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd218103807);
$fwrite(fd,"218103807,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 218103807")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd218103808);
$fwrite(fd,"218103808,%02h,%0d\n",got,err);
if(err || got !== 8'h0b) `uvm_fatal("bank_preflight","byte mismatch at 218103808")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd219152383);
$fwrite(fd,"219152383,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 219152383")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd219152384);
$fwrite(fd,"219152384,%02h,%0d\n",got,err);
if(err || got !== 8'h7a) `uvm_fatal("bank_preflight","byte mismatch at 219152384")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd220200959);
$fwrite(fd,"220200959,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 220200959")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd220200960);
$fwrite(fd,"220200960,%02h,%0d\n",got,err);
if(err || got !== 8'hc6) `uvm_fatal("bank_preflight","byte mismatch at 220200960")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd221249535);
$fwrite(fd,"221249535,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 221249535")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd221249536);
$fwrite(fd,"221249536,%02h,%0d\n",got,err);
if(err || got !== 8'ha6) `uvm_fatal("bank_preflight","byte mismatch at 221249536")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd222298111);
$fwrite(fd,"222298111,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 222298111")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd222298112);
$fwrite(fd,"222298112,%02h,%0d\n",got,err);
if(err || got !== 8'h5f) `uvm_fatal("bank_preflight","byte mismatch at 222298112")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd223346687);
$fwrite(fd,"223346687,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 223346687")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd223346688);
$fwrite(fd,"223346688,%02h,%0d\n",got,err);
if(err || got !== 8'ha6) `uvm_fatal("bank_preflight","byte mismatch at 223346688")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd224395263);
$fwrite(fd,"224395263,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 224395263")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd224395264);
$fwrite(fd,"224395264,%02h,%0d\n",got,err);
if(err || got !== 8'hce) `uvm_fatal("bank_preflight","byte mismatch at 224395264")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd225443839);
$fwrite(fd,"225443839,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 225443839")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd225443840);
$fwrite(fd,"225443840,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 225443840")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd226492415);
$fwrite(fd,"226492415,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 226492415")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd226492416);
$fwrite(fd,"226492416,%02h,%0d\n",got,err);
if(err || got !== 8'hb4) `uvm_fatal("bank_preflight","byte mismatch at 226492416")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd227540991);
$fwrite(fd,"227540991,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 227540991")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd227540992);
$fwrite(fd,"227540992,%02h,%0d\n",got,err);
if(err || got !== 8'he1) `uvm_fatal("bank_preflight","byte mismatch at 227540992")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd228589567);
$fwrite(fd,"228589567,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 228589567")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd228589568);
$fwrite(fd,"228589568,%02h,%0d\n",got,err);
if(err || got !== 8'h6c) `uvm_fatal("bank_preflight","byte mismatch at 228589568")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd229638143);
$fwrite(fd,"229638143,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 229638143")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd229638144);
$fwrite(fd,"229638144,%02h,%0d\n",got,err);
if(err || got !== 8'h92) `uvm_fatal("bank_preflight","byte mismatch at 229638144")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd230686719);
$fwrite(fd,"230686719,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 230686719")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd230686720);
$fwrite(fd,"230686720,%02h,%0d\n",got,err);
if(err || got !== 8'ha7) `uvm_fatal("bank_preflight","byte mismatch at 230686720")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd231735295);
$fwrite(fd,"231735295,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 231735295")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd231735296);
$fwrite(fd,"231735296,%02h,%0d\n",got,err);
if(err || got !== 8'hf4) `uvm_fatal("bank_preflight","byte mismatch at 231735296")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd232783871);
$fwrite(fd,"232783871,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 232783871")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd232783872);
$fwrite(fd,"232783872,%02h,%0d\n",got,err);
if(err || got !== 8'h2f) `uvm_fatal("bank_preflight","byte mismatch at 232783872")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd233832447);
$fwrite(fd,"233832447,%02h,%0d\n",got,err);
if(err || got !== 8'h3d) `uvm_fatal("bank_preflight","byte mismatch at 233832447")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd233832448);
$fwrite(fd,"233832448,%02h,%0d\n",got,err);
if(err || got !== 8'h9e) `uvm_fatal("bank_preflight","byte mismatch at 233832448")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd234881023);
$fwrite(fd,"234881023,%02h,%0d\n",got,err);
if(err || got !== 8'h3d) `uvm_fatal("bank_preflight","byte mismatch at 234881023")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd234881024);
$fwrite(fd,"234881024,%02h,%0d\n",got,err);
if(err || got !== 8'h35) `uvm_fatal("bank_preflight","byte mismatch at 234881024")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd235929599);
$fwrite(fd,"235929599,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 235929599")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd235929600);
$fwrite(fd,"235929600,%02h,%0d\n",got,err);
if(err || got !== 8'hbf) `uvm_fatal("bank_preflight","byte mismatch at 235929600")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd236978175);
$fwrite(fd,"236978175,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 236978175")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd236978176);
$fwrite(fd,"236978176,%02h,%0d\n",got,err);
if(err || got !== 8'h21) `uvm_fatal("bank_preflight","byte mismatch at 236978176")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd238026751);
$fwrite(fd,"238026751,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 238026751")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd238026752);
$fwrite(fd,"238026752,%02h,%0d\n",got,err);
if(err || got !== 8'h7e) `uvm_fatal("bank_preflight","byte mismatch at 238026752")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd239075327);
$fwrite(fd,"239075327,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 239075327")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd239075328);
$fwrite(fd,"239075328,%02h,%0d\n",got,err);
if(err || got !== 8'h04) `uvm_fatal("bank_preflight","byte mismatch at 239075328")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd240123903);
$fwrite(fd,"240123903,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 240123903")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd240123904);
$fwrite(fd,"240123904,%02h,%0d\n",got,err);
if(err || got !== 8'h96) `uvm_fatal("bank_preflight","byte mismatch at 240123904")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd241172479);
$fwrite(fd,"241172479,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 241172479")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd241172480);
$fwrite(fd,"241172480,%02h,%0d\n",got,err);
if(err || got !== 8'hb7) `uvm_fatal("bank_preflight","byte mismatch at 241172480")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd242221055);
$fwrite(fd,"242221055,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 242221055")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd242221056);
$fwrite(fd,"242221056,%02h,%0d\n",got,err);
if(err || got !== 8'h78) `uvm_fatal("bank_preflight","byte mismatch at 242221056")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd243269631);
$fwrite(fd,"243269631,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 243269631")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd243269632);
$fwrite(fd,"243269632,%02h,%0d\n",got,err);
if(err || got !== 8'hed) `uvm_fatal("bank_preflight","byte mismatch at 243269632")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd244318207);
$fwrite(fd,"244318207,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 244318207")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd244318208);
$fwrite(fd,"244318208,%02h,%0d\n",got,err);
if(err || got !== 8'h4f) `uvm_fatal("bank_preflight","byte mismatch at 244318208")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd245366783);
$fwrite(fd,"245366783,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 245366783")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd245366784);
$fwrite(fd,"245366784,%02h,%0d\n",got,err);
if(err || got !== 8'hc4) `uvm_fatal("bank_preflight","byte mismatch at 245366784")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd246415359);
$fwrite(fd,"246415359,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 246415359")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd246415360);
$fwrite(fd,"246415360,%02h,%0d\n",got,err);
if(err || got !== 8'h8e) `uvm_fatal("bank_preflight","byte mismatch at 246415360")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd247463935);
$fwrite(fd,"247463935,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 247463935")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd247463936);
$fwrite(fd,"247463936,%02h,%0d\n",got,err);
if(err || got !== 8'ha5) `uvm_fatal("bank_preflight","byte mismatch at 247463936")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd248512511);
$fwrite(fd,"248512511,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 248512511")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd248512512);
$fwrite(fd,"248512512,%02h,%0d\n",got,err);
if(err || got !== 8'h75) `uvm_fatal("bank_preflight","byte mismatch at 248512512")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd249561087);
$fwrite(fd,"249561087,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 249561087")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd249561088);
$fwrite(fd,"249561088,%02h,%0d\n",got,err);
if(err || got !== 8'h06) `uvm_fatal("bank_preflight","byte mismatch at 249561088")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd250609663);
$fwrite(fd,"250609663,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 250609663")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd250609664);
$fwrite(fd,"250609664,%02h,%0d\n",got,err);
if(err || got !== 8'hff) `uvm_fatal("bank_preflight","byte mismatch at 250609664")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd251658239);
$fwrite(fd,"251658239,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 251658239")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd251658240);
$fwrite(fd,"251658240,%02h,%0d\n",got,err);
if(err || got !== 8'hcd) `uvm_fatal("bank_preflight","byte mismatch at 251658240")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd252706815);
$fwrite(fd,"252706815,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 252706815")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd252706816);
$fwrite(fd,"252706816,%02h,%0d\n",got,err);
if(err || got !== 8'h29) `uvm_fatal("bank_preflight","byte mismatch at 252706816")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd253755391);
$fwrite(fd,"253755391,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 253755391")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd253755392);
$fwrite(fd,"253755392,%02h,%0d\n",got,err);
if(err || got !== 8'h97) `uvm_fatal("bank_preflight","byte mismatch at 253755392")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd254803967);
$fwrite(fd,"254803967,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 254803967")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd254803968);
$fwrite(fd,"254803968,%02h,%0d\n",got,err);
if(err || got !== 8'hbd) `uvm_fatal("bank_preflight","byte mismatch at 254803968")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd255852543);
$fwrite(fd,"255852543,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 255852543")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd255852544);
$fwrite(fd,"255852544,%02h,%0d\n",got,err);
if(err || got !== 8'h82) `uvm_fatal("bank_preflight","byte mismatch at 255852544")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd256901119);
$fwrite(fd,"256901119,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 256901119")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd256901120);
$fwrite(fd,"256901120,%02h,%0d\n",got,err);
if(err || got !== 8'h75) `uvm_fatal("bank_preflight","byte mismatch at 256901120")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd257949695);
$fwrite(fd,"257949695,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 257949695")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd257949696);
$fwrite(fd,"257949696,%02h,%0d\n",got,err);
if(err || got !== 8'h7e) `uvm_fatal("bank_preflight","byte mismatch at 257949696")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd258998271);
$fwrite(fd,"258998271,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 258998271")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd258998272);
$fwrite(fd,"258998272,%02h,%0d\n",got,err);
if(err || got !== 8'h57) `uvm_fatal("bank_preflight","byte mismatch at 258998272")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd260046847);
$fwrite(fd,"260046847,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 260046847")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd260046848);
$fwrite(fd,"260046848,%02h,%0d\n",got,err);
if(err || got !== 8'h68) `uvm_fatal("bank_preflight","byte mismatch at 260046848")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd261095423);
$fwrite(fd,"261095423,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 261095423")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd261095424);
$fwrite(fd,"261095424,%02h,%0d\n",got,err);
if(err || got !== 8'hb6) `uvm_fatal("bank_preflight","byte mismatch at 261095424")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd262143999);
$fwrite(fd,"262143999,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 262143999")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd262144000);
$fwrite(fd,"262144000,%02h,%0d\n",got,err);
if(err || got !== 8'h90) `uvm_fatal("bank_preflight","byte mismatch at 262144000")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd263192575);
$fwrite(fd,"263192575,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 263192575")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd263192576);
$fwrite(fd,"263192576,%02h,%0d\n",got,err);
if(err || got !== 8'h33) `uvm_fatal("bank_preflight","byte mismatch at 263192576")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd264241151);
$fwrite(fd,"264241151,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 264241151")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd264241152);
$fwrite(fd,"264241152,%02h,%0d\n",got,err);
if(err || got !== 8'h9d) `uvm_fatal("bank_preflight","byte mismatch at 264241152")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd265289727);
$fwrite(fd,"265289727,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 265289727")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd265289728);
$fwrite(fd,"265289728,%02h,%0d\n",got,err);
if(err || got !== 8'h73) `uvm_fatal("bank_preflight","byte mismatch at 265289728")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd266338303);
$fwrite(fd,"266338303,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 266338303")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd266338304);
$fwrite(fd,"266338304,%02h,%0d\n",got,err);
if(err || got !== 8'h77) `uvm_fatal("bank_preflight","byte mismatch at 266338304")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd267386879);
$fwrite(fd,"267386879,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 267386879")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd267386880);
$fwrite(fd,"267386880,%02h,%0d\n",got,err);
if(err || got !== 8'h12) `uvm_fatal("bank_preflight","byte mismatch at 267386880")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd268435455);
$fwrite(fd,"268435455,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 268435455")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd268435456);
$fwrite(fd,"268435456,%02h,%0d\n",got,err);
if(err || got !== 8'ha2) `uvm_fatal("bank_preflight","byte mismatch at 268435456")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd269484031);
$fwrite(fd,"269484031,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 269484031")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd269484032);
$fwrite(fd,"269484032,%02h,%0d\n",got,err);
if(err || got !== 8'h1e) `uvm_fatal("bank_preflight","byte mismatch at 269484032")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd270532607);
$fwrite(fd,"270532607,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 270532607")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd270532608);
$fwrite(fd,"270532608,%02h,%0d\n",got,err);
if(err || got !== 8'h86) `uvm_fatal("bank_preflight","byte mismatch at 270532608")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd271581183);
$fwrite(fd,"271581183,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 271581183")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd271581184);
$fwrite(fd,"271581184,%02h,%0d\n",got,err);
if(err || got !== 8'hbd) `uvm_fatal("bank_preflight","byte mismatch at 271581184")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd272629759);
$fwrite(fd,"272629759,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 272629759")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd272629760);
$fwrite(fd,"272629760,%02h,%0d\n",got,err);
if(err || got !== 8'h13) `uvm_fatal("bank_preflight","byte mismatch at 272629760")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416160);
$fwrite(fd,"273416160,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416160")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416161);
$fwrite(fd,"273416161,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416161")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416162);
$fwrite(fd,"273416162,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416162")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416163);
$fwrite(fd,"273416163,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416163")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416164);
$fwrite(fd,"273416164,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416164")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416165);
$fwrite(fd,"273416165,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416165")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416166);
$fwrite(fd,"273416166,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416166")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416167);
$fwrite(fd,"273416167,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416167")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416168);
$fwrite(fd,"273416168,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416168")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416169);
$fwrite(fd,"273416169,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416169")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416170);
$fwrite(fd,"273416170,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416170")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416171);
$fwrite(fd,"273416171,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416171")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416172);
$fwrite(fd,"273416172,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416172")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416173);
$fwrite(fd,"273416173,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416173")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416174);
$fwrite(fd,"273416174,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416174")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416175);
$fwrite(fd,"273416175,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416175")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416176);
$fwrite(fd,"273416176,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416176")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416177);
$fwrite(fd,"273416177,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416177")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416178);
$fwrite(fd,"273416178,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416178")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416179);
$fwrite(fd,"273416179,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416179")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416180);
$fwrite(fd,"273416180,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416180")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416181);
$fwrite(fd,"273416181,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416181")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416182);
$fwrite(fd,"273416182,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416182")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416183);
$fwrite(fd,"273416183,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416183")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416184);
$fwrite(fd,"273416184,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416184")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416185);
$fwrite(fd,"273416185,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416185")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416186);
$fwrite(fd,"273416186,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416186")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416187);
$fwrite(fd,"273416187,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416187")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416188);
$fwrite(fd,"273416188,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416188")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416189);
$fwrite(fd,"273416189,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416189")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416190);
$fwrite(fd,"273416190,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416190")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416191);
$fwrite(fd,"273416191,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 273416191")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416192);
$fwrite(fd,"273416192,%02h,%0d\n",got,err);
if(err || got !== 8'h2a) `uvm_fatal("bank_preflight","byte mismatch at 273416192")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416193);
$fwrite(fd,"273416193,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 273416193")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416194);
$fwrite(fd,"273416194,%02h,%0d\n",got,err);
if(err || got !== 8'h27) `uvm_fatal("bank_preflight","byte mismatch at 273416194")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416195);
$fwrite(fd,"273416195,%02h,%0d\n",got,err);
if(err || got !== 8'h3d) `uvm_fatal("bank_preflight","byte mismatch at 273416195")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416196);
$fwrite(fd,"273416196,%02h,%0d\n",got,err);
if(err || got !== 8'h1f) `uvm_fatal("bank_preflight","byte mismatch at 273416196")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416197);
$fwrite(fd,"273416197,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 273416197")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416198);
$fwrite(fd,"273416198,%02h,%0d\n",got,err);
if(err || got !== 8'h92) `uvm_fatal("bank_preflight","byte mismatch at 273416198")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416199);
$fwrite(fd,"273416199,%02h,%0d\n",got,err);
if(err || got !== 8'h38) `uvm_fatal("bank_preflight","byte mismatch at 273416199")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416200);
$fwrite(fd,"273416200,%02h,%0d\n",got,err);
if(err || got !== 8'hde) `uvm_fatal("bank_preflight","byte mismatch at 273416200")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416201);
$fwrite(fd,"273416201,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 273416201")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416202);
$fwrite(fd,"273416202,%02h,%0d\n",got,err);
if(err || got !== 8'h43) `uvm_fatal("bank_preflight","byte mismatch at 273416202")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416203);
$fwrite(fd,"273416203,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 273416203")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416204);
$fwrite(fd,"273416204,%02h,%0d\n",got,err);
if(err || got !== 8'h98) `uvm_fatal("bank_preflight","byte mismatch at 273416204")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416205);
$fwrite(fd,"273416205,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 273416205")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416206);
$fwrite(fd,"273416206,%02h,%0d\n",got,err);
if(err || got !== 8'ha0) `uvm_fatal("bank_preflight","byte mismatch at 273416206")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416207);
$fwrite(fd,"273416207,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 273416207")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416208);
$fwrite(fd,"273416208,%02h,%0d\n",got,err);
if(err || got !== 8'he9) `uvm_fatal("bank_preflight","byte mismatch at 273416208")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416209);
$fwrite(fd,"273416209,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 273416209")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416210);
$fwrite(fd,"273416210,%02h,%0d\n",got,err);
if(err || got !== 8'hdd) `uvm_fatal("bank_preflight","byte mismatch at 273416210")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416211);
$fwrite(fd,"273416211,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 273416211")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416212);
$fwrite(fd,"273416212,%02h,%0d\n",got,err);
if(err || got !== 8'he2) `uvm_fatal("bank_preflight","byte mismatch at 273416212")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416213);
$fwrite(fd,"273416213,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 273416213")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416214);
$fwrite(fd,"273416214,%02h,%0d\n",got,err);
if(err || got !== 8'h73) `uvm_fatal("bank_preflight","byte mismatch at 273416214")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416215);
$fwrite(fd,"273416215,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 273416215")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416216);
$fwrite(fd,"273416216,%02h,%0d\n",got,err);
if(err || got !== 8'h78) `uvm_fatal("bank_preflight","byte mismatch at 273416216")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416217);
$fwrite(fd,"273416217,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 273416217")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416218);
$fwrite(fd,"273416218,%02h,%0d\n",got,err);
if(err || got !== 8'h5f) `uvm_fatal("bank_preflight","byte mismatch at 273416218")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416219);
$fwrite(fd,"273416219,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 273416219")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416220);
$fwrite(fd,"273416220,%02h,%0d\n",got,err);
if(err || got !== 8'he9) `uvm_fatal("bank_preflight","byte mismatch at 273416220")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416221);
$fwrite(fd,"273416221,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 273416221")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416222);
$fwrite(fd,"273416222,%02h,%0d\n",got,err);
if(err || got !== 8'h52) `uvm_fatal("bank_preflight","byte mismatch at 273416222")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416223);
$fwrite(fd,"273416223,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 273416223")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273416224);
$fwrite(fd,"273416224,%02h,%0d\n",got,err);
if(err || got !== 8'ha7) `uvm_fatal("bank_preflight","byte mismatch at 273416224")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273678335);
$fwrite(fd,"273678335,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 273678335")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd273678336);
$fwrite(fd,"273678336,%02h,%0d\n",got,err);
if(err || got !== 8'h1f) `uvm_fatal("bank_preflight","byte mismatch at 273678336")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd274726911);
$fwrite(fd,"274726911,%02h,%0d\n",got,err);
if(err || got !== 8'h3d) `uvm_fatal("bank_preflight","byte mismatch at 274726911")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd274726912);
$fwrite(fd,"274726912,%02h,%0d\n",got,err);
if(err || got !== 8'h91) `uvm_fatal("bank_preflight","byte mismatch at 274726912")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd275775487);
$fwrite(fd,"275775487,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 275775487")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd275775488);
$fwrite(fd,"275775488,%02h,%0d\n",got,err);
if(err || got !== 8'h8e) `uvm_fatal("bank_preflight","byte mismatch at 275775488")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd276824063);
$fwrite(fd,"276824063,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 276824063")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd276824064);
$fwrite(fd,"276824064,%02h,%0d\n",got,err);
if(err || got !== 8'h5d) `uvm_fatal("bank_preflight","byte mismatch at 276824064")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd277872639);
$fwrite(fd,"277872639,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 277872639")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd277872640);
$fwrite(fd,"277872640,%02h,%0d\n",got,err);
if(err || got !== 8'hd4) `uvm_fatal("bank_preflight","byte mismatch at 277872640")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd278921215);
$fwrite(fd,"278921215,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 278921215")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd278921216);
$fwrite(fd,"278921216,%02h,%0d\n",got,err);
if(err || got !== 8'h30) `uvm_fatal("bank_preflight","byte mismatch at 278921216")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd279969791);
$fwrite(fd,"279969791,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 279969791")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd279969792);
$fwrite(fd,"279969792,%02h,%0d\n",got,err);
if(err || got !== 8'hf7) `uvm_fatal("bank_preflight","byte mismatch at 279969792")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd281018367);
$fwrite(fd,"281018367,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 281018367")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd281018368);
$fwrite(fd,"281018368,%02h,%0d\n",got,err);
if(err || got !== 8'ha8) `uvm_fatal("bank_preflight","byte mismatch at 281018368")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd282066943);
$fwrite(fd,"282066943,%02h,%0d\n",got,err);
if(err || got !== 8'hbd) `uvm_fatal("bank_preflight","byte mismatch at 282066943")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd282066944);
$fwrite(fd,"282066944,%02h,%0d\n",got,err);
if(err || got !== 8'h69) `uvm_fatal("bank_preflight","byte mismatch at 282066944")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd283115519);
$fwrite(fd,"283115519,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 283115519")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd283115520);
$fwrite(fd,"283115520,%02h,%0d\n",got,err);
if(err || got !== 8'h31) `uvm_fatal("bank_preflight","byte mismatch at 283115520")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd284164095);
$fwrite(fd,"284164095,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 284164095")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd284164096);
$fwrite(fd,"284164096,%02h,%0d\n",got,err);
if(err || got !== 8'h96) `uvm_fatal("bank_preflight","byte mismatch at 284164096")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd285212671);
$fwrite(fd,"285212671,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 285212671")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd285212672);
$fwrite(fd,"285212672,%02h,%0d\n",got,err);
if(err || got !== 8'h17) `uvm_fatal("bank_preflight","byte mismatch at 285212672")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd286261247);
$fwrite(fd,"286261247,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 286261247")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd286261248);
$fwrite(fd,"286261248,%02h,%0d\n",got,err);
if(err || got !== 8'h25) `uvm_fatal("bank_preflight","byte mismatch at 286261248")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd287309823);
$fwrite(fd,"287309823,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 287309823")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd287309824);
$fwrite(fd,"287309824,%02h,%0d\n",got,err);
if(err || got !== 8'hc8) `uvm_fatal("bank_preflight","byte mismatch at 287309824")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd288358399);
$fwrite(fd,"288358399,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 288358399")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd288358400);
$fwrite(fd,"288358400,%02h,%0d\n",got,err);
if(err || got !== 8'h5e) `uvm_fatal("bank_preflight","byte mismatch at 288358400")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd289406975);
$fwrite(fd,"289406975,%02h,%0d\n",got,err);
if(err || got !== 8'hbd) `uvm_fatal("bank_preflight","byte mismatch at 289406975")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd289406976);
$fwrite(fd,"289406976,%02h,%0d\n",got,err);
if(err || got !== 8'hbf) `uvm_fatal("bank_preflight","byte mismatch at 289406976")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd290455551);
$fwrite(fd,"290455551,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 290455551")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd290455552);
$fwrite(fd,"290455552,%02h,%0d\n",got,err);
if(err || got !== 8'h25) `uvm_fatal("bank_preflight","byte mismatch at 290455552")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd291504127);
$fwrite(fd,"291504127,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 291504127")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd291504128);
$fwrite(fd,"291504128,%02h,%0d\n",got,err);
if(err || got !== 8'h30) `uvm_fatal("bank_preflight","byte mismatch at 291504128")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd292552703);
$fwrite(fd,"292552703,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 292552703")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd292552704);
$fwrite(fd,"292552704,%02h,%0d\n",got,err);
if(err || got !== 8'h5a) `uvm_fatal("bank_preflight","byte mismatch at 292552704")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd293601279);
$fwrite(fd,"293601279,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 293601279")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd293601280);
$fwrite(fd,"293601280,%02h,%0d\n",got,err);
if(err || got !== 8'h46) `uvm_fatal("bank_preflight","byte mismatch at 293601280")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd294649855);
$fwrite(fd,"294649855,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 294649855")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd294649856);
$fwrite(fd,"294649856,%02h,%0d\n",got,err);
if(err || got !== 8'h7d) `uvm_fatal("bank_preflight","byte mismatch at 294649856")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd295698431);
$fwrite(fd,"295698431,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 295698431")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd295698432);
$fwrite(fd,"295698432,%02h,%0d\n",got,err);
if(err || got !== 8'h37) `uvm_fatal("bank_preflight","byte mismatch at 295698432")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd296747007);
$fwrite(fd,"296747007,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 296747007")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd296747008);
$fwrite(fd,"296747008,%02h,%0d\n",got,err);
if(err || got !== 8'h85) `uvm_fatal("bank_preflight","byte mismatch at 296747008")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd297795583);
$fwrite(fd,"297795583,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 297795583")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd297795584);
$fwrite(fd,"297795584,%02h,%0d\n",got,err);
if(err || got !== 8'h82) `uvm_fatal("bank_preflight","byte mismatch at 297795584")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd298844159);
$fwrite(fd,"298844159,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 298844159")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd298844160);
$fwrite(fd,"298844160,%02h,%0d\n",got,err);
if(err || got !== 8'h69) `uvm_fatal("bank_preflight","byte mismatch at 298844160")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd299892735);
$fwrite(fd,"299892735,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 299892735")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd299892736);
$fwrite(fd,"299892736,%02h,%0d\n",got,err);
if(err || got !== 8'h21) `uvm_fatal("bank_preflight","byte mismatch at 299892736")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd300941311);
$fwrite(fd,"300941311,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 300941311")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd300941312);
$fwrite(fd,"300941312,%02h,%0d\n",got,err);
if(err || got !== 8'h30) `uvm_fatal("bank_preflight","byte mismatch at 300941312")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd301989887);
$fwrite(fd,"301989887,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 301989887")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd301989888);
$fwrite(fd,"301989888,%02h,%0d\n",got,err);
if(err || got !== 8'h8c) `uvm_fatal("bank_preflight","byte mismatch at 301989888")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd303038463);
$fwrite(fd,"303038463,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 303038463")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd303038464);
$fwrite(fd,"303038464,%02h,%0d\n",got,err);
if(err || got !== 8'h98) `uvm_fatal("bank_preflight","byte mismatch at 303038464")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd304087039);
$fwrite(fd,"304087039,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 304087039")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd304087040);
$fwrite(fd,"304087040,%02h,%0d\n",got,err);
if(err || got !== 8'h85) `uvm_fatal("bank_preflight","byte mismatch at 304087040")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd305135615);
$fwrite(fd,"305135615,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 305135615")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd305135616);
$fwrite(fd,"305135616,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 305135616")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd306184191);
$fwrite(fd,"306184191,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 306184191")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd306184192);
$fwrite(fd,"306184192,%02h,%0d\n",got,err);
if(err || got !== 8'h80) `uvm_fatal("bank_preflight","byte mismatch at 306184192")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd307232767);
$fwrite(fd,"307232767,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 307232767")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd307232768);
$fwrite(fd,"307232768,%02h,%0d\n",got,err);
if(err || got !== 8'hf5) `uvm_fatal("bank_preflight","byte mismatch at 307232768")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd308281343);
$fwrite(fd,"308281343,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 308281343")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd308281344);
$fwrite(fd,"308281344,%02h,%0d\n",got,err);
if(err || got !== 8'h95) `uvm_fatal("bank_preflight","byte mismatch at 308281344")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd309329919);
$fwrite(fd,"309329919,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 309329919")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd309329920);
$fwrite(fd,"309329920,%02h,%0d\n",got,err);
if(err || got !== 8'he2) `uvm_fatal("bank_preflight","byte mismatch at 309329920")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd310378495);
$fwrite(fd,"310378495,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 310378495")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd310378496);
$fwrite(fd,"310378496,%02h,%0d\n",got,err);
if(err || got !== 8'h0e) `uvm_fatal("bank_preflight","byte mismatch at 310378496")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd311427071);
$fwrite(fd,"311427071,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 311427071")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd311427072);
$fwrite(fd,"311427072,%02h,%0d\n",got,err);
if(err || got !== 8'hf5) `uvm_fatal("bank_preflight","byte mismatch at 311427072")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd312475647);
$fwrite(fd,"312475647,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 312475647")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd312475648);
$fwrite(fd,"312475648,%02h,%0d\n",got,err);
if(err || got !== 8'h7d) `uvm_fatal("bank_preflight","byte mismatch at 312475648")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd313524223);
$fwrite(fd,"313524223,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 313524223")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd313524224);
$fwrite(fd,"313524224,%02h,%0d\n",got,err);
if(err || got !== 8'h6c) `uvm_fatal("bank_preflight","byte mismatch at 313524224")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd314572799);
$fwrite(fd,"314572799,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 314572799")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd314572800);
$fwrite(fd,"314572800,%02h,%0d\n",got,err);
if(err || got !== 8'he7) `uvm_fatal("bank_preflight","byte mismatch at 314572800")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd315621375);
$fwrite(fd,"315621375,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 315621375")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd315621376);
$fwrite(fd,"315621376,%02h,%0d\n",got,err);
if(err || got !== 8'h90) `uvm_fatal("bank_preflight","byte mismatch at 315621376")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd316669951);
$fwrite(fd,"316669951,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 316669951")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd316669952);
$fwrite(fd,"316669952,%02h,%0d\n",got,err);
if(err || got !== 8'hbd) `uvm_fatal("bank_preflight","byte mismatch at 316669952")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd317718527);
$fwrite(fd,"317718527,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 317718527")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd317718528);
$fwrite(fd,"317718528,%02h,%0d\n",got,err);
if(err || got !== 8'h2e) `uvm_fatal("bank_preflight","byte mismatch at 317718528")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd318767103);
$fwrite(fd,"318767103,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 318767103")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd318767104);
$fwrite(fd,"318767104,%02h,%0d\n",got,err);
if(err || got !== 8'ha3) `uvm_fatal("bank_preflight","byte mismatch at 318767104")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd319815679);
$fwrite(fd,"319815679,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 319815679")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd319815680);
$fwrite(fd,"319815680,%02h,%0d\n",got,err);
if(err || got !== 8'hbe) `uvm_fatal("bank_preflight","byte mismatch at 319815680")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd320864255);
$fwrite(fd,"320864255,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 320864255")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd320864256);
$fwrite(fd,"320864256,%02h,%0d\n",got,err);
if(err || got !== 8'hf8) `uvm_fatal("bank_preflight","byte mismatch at 320864256")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd321912831);
$fwrite(fd,"321912831,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 321912831")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd321912832);
$fwrite(fd,"321912832,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 321912832")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd322961407);
$fwrite(fd,"322961407,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 322961407")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd322961408);
$fwrite(fd,"322961408,%02h,%0d\n",got,err);
if(err || got !== 8'h20) `uvm_fatal("bank_preflight","byte mismatch at 322961408")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd324009983);
$fwrite(fd,"324009983,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 324009983")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd324009984);
$fwrite(fd,"324009984,%02h,%0d\n",got,err);
if(err || got !== 8'h52) `uvm_fatal("bank_preflight","byte mismatch at 324009984")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd325058559);
$fwrite(fd,"325058559,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 325058559")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd325058560);
$fwrite(fd,"325058560,%02h,%0d\n",got,err);
if(err || got !== 8'h18) `uvm_fatal("bank_preflight","byte mismatch at 325058560")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd326107135);
$fwrite(fd,"326107135,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 326107135")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd326107136);
$fwrite(fd,"326107136,%02h,%0d\n",got,err);
if(err || got !== 8'h16) `uvm_fatal("bank_preflight","byte mismatch at 326107136")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd327155711);
$fwrite(fd,"327155711,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 327155711")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd327155712);
$fwrite(fd,"327155712,%02h,%0d\n",got,err);
if(err || got !== 8'hce) `uvm_fatal("bank_preflight","byte mismatch at 327155712")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd328204287);
$fwrite(fd,"328204287,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 328204287")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd328204288);
$fwrite(fd,"328204288,%02h,%0d\n",got,err);
if(err || got !== 8'hbd) `uvm_fatal("bank_preflight","byte mismatch at 328204288")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd329252863);
$fwrite(fd,"329252863,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 329252863")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd329252864);
$fwrite(fd,"329252864,%02h,%0d\n",got,err);
if(err || got !== 8'h86) `uvm_fatal("bank_preflight","byte mismatch at 329252864")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd330301439);
$fwrite(fd,"330301439,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 330301439")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd330301440);
$fwrite(fd,"330301440,%02h,%0d\n",got,err);
if(err || got !== 8'h7e) `uvm_fatal("bank_preflight","byte mismatch at 330301440")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd331350015);
$fwrite(fd,"331350015,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 331350015")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd331350016);
$fwrite(fd,"331350016,%02h,%0d\n",got,err);
if(err || got !== 8'h82) `uvm_fatal("bank_preflight","byte mismatch at 331350016")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd332398591);
$fwrite(fd,"332398591,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 332398591")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd332398592);
$fwrite(fd,"332398592,%02h,%0d\n",got,err);
if(err || got !== 8'h98) `uvm_fatal("bank_preflight","byte mismatch at 332398592")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd333447167);
$fwrite(fd,"333447167,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 333447167")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd333447168);
$fwrite(fd,"333447168,%02h,%0d\n",got,err);
if(err || got !== 8'h5a) `uvm_fatal("bank_preflight","byte mismatch at 333447168")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd334495743);
$fwrite(fd,"334495743,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 334495743")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd334495744);
$fwrite(fd,"334495744,%02h,%0d\n",got,err);
if(err || got !== 8'hd0) `uvm_fatal("bank_preflight","byte mismatch at 334495744")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd335544319);
$fwrite(fd,"335544319,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 335544319")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd335544320);
$fwrite(fd,"335544320,%02h,%0d\n",got,err);
if(err || got !== 8'h11) `uvm_fatal("bank_preflight","byte mismatch at 335544320")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd336592895);
$fwrite(fd,"336592895,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 336592895")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd336592896);
$fwrite(fd,"336592896,%02h,%0d\n",got,err);
if(err || got !== 8'hfb) `uvm_fatal("bank_preflight","byte mismatch at 336592896")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd337641471);
$fwrite(fd,"337641471,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 337641471")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd337641472);
$fwrite(fd,"337641472,%02h,%0d\n",got,err);
if(err || got !== 8'h55) `uvm_fatal("bank_preflight","byte mismatch at 337641472")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd338690047);
$fwrite(fd,"338690047,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 338690047")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd338690048);
$fwrite(fd,"338690048,%02h,%0d\n",got,err);
if(err || got !== 8'hc2) `uvm_fatal("bank_preflight","byte mismatch at 338690048")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd339738623);
$fwrite(fd,"339738623,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 339738623")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd339738624);
$fwrite(fd,"339738624,%02h,%0d\n",got,err);
if(err || got !== 8'h6b) `uvm_fatal("bank_preflight","byte mismatch at 339738624")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd340787199);
$fwrite(fd,"340787199,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 340787199")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd340787200);
$fwrite(fd,"340787200,%02h,%0d\n",got,err);
if(err || got !== 8'hc9) `uvm_fatal("bank_preflight","byte mismatch at 340787200")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd341835775);
$fwrite(fd,"341835775,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 341835775")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd341835776);
$fwrite(fd,"341835776,%02h,%0d\n",got,err);
if(err || got !== 8'hf9) `uvm_fatal("bank_preflight","byte mismatch at 341835776")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd342884351);
$fwrite(fd,"342884351,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 342884351")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd342884352);
$fwrite(fd,"342884352,%02h,%0d\n",got,err);
if(err || got !== 8'h82) `uvm_fatal("bank_preflight","byte mismatch at 342884352")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd343932927);
$fwrite(fd,"343932927,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 343932927")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd343932928);
$fwrite(fd,"343932928,%02h,%0d\n",got,err);
if(err || got !== 8'h61) `uvm_fatal("bank_preflight","byte mismatch at 343932928")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd344981503);
$fwrite(fd,"344981503,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 344981503")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd344981504);
$fwrite(fd,"344981504,%02h,%0d\n",got,err);
if(err || got !== 8'hea) `uvm_fatal("bank_preflight","byte mismatch at 344981504")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd346030079);
$fwrite(fd,"346030079,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 346030079")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd346030080);
$fwrite(fd,"346030080,%02h,%0d\n",got,err);
if(err || got !== 8'h06) `uvm_fatal("bank_preflight","byte mismatch at 346030080")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd347078655);
$fwrite(fd,"347078655,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 347078655")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd347078656);
$fwrite(fd,"347078656,%02h,%0d\n",got,err);
if(err || got !== 8'h29) `uvm_fatal("bank_preflight","byte mismatch at 347078656")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd348127231);
$fwrite(fd,"348127231,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 348127231")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd348127232);
$fwrite(fd,"348127232,%02h,%0d\n",got,err);
if(err || got !== 8'h29) `uvm_fatal("bank_preflight","byte mismatch at 348127232")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd349175807);
$fwrite(fd,"349175807,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 349175807")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd349175808);
$fwrite(fd,"349175808,%02h,%0d\n",got,err);
if(err || got !== 8'h8a) `uvm_fatal("bank_preflight","byte mismatch at 349175808")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd350224383);
$fwrite(fd,"350224383,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 350224383")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd350224384);
$fwrite(fd,"350224384,%02h,%0d\n",got,err);
if(err || got !== 8'h23) `uvm_fatal("bank_preflight","byte mismatch at 350224384")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd351272959);
$fwrite(fd,"351272959,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 351272959")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd351272960);
$fwrite(fd,"351272960,%02h,%0d\n",got,err);
if(err || got !== 8'h1e) `uvm_fatal("bank_preflight","byte mismatch at 351272960")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd352321535);
$fwrite(fd,"352321535,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 352321535")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd352321536);
$fwrite(fd,"352321536,%02h,%0d\n",got,err);
if(err || got !== 8'h09) `uvm_fatal("bank_preflight","byte mismatch at 352321536")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd353370111);
$fwrite(fd,"353370111,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 353370111")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd353370112);
$fwrite(fd,"353370112,%02h,%0d\n",got,err);
if(err || got !== 8'h0c) `uvm_fatal("bank_preflight","byte mismatch at 353370112")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd354418687);
$fwrite(fd,"354418687,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 354418687")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd354418688);
$fwrite(fd,"354418688,%02h,%0d\n",got,err);
if(err || got !== 8'h64) `uvm_fatal("bank_preflight","byte mismatch at 354418688")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd355467263);
$fwrite(fd,"355467263,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 355467263")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd355467264);
$fwrite(fd,"355467264,%02h,%0d\n",got,err);
if(err || got !== 8'h97) `uvm_fatal("bank_preflight","byte mismatch at 355467264")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd356515839);
$fwrite(fd,"356515839,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 356515839")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd356515840);
$fwrite(fd,"356515840,%02h,%0d\n",got,err);
if(err || got !== 8'h5a) `uvm_fatal("bank_preflight","byte mismatch at 356515840")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd357564415);
$fwrite(fd,"357564415,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 357564415")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd357564416);
$fwrite(fd,"357564416,%02h,%0d\n",got,err);
if(err || got !== 8'h5c) `uvm_fatal("bank_preflight","byte mismatch at 357564416")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd358612991);
$fwrite(fd,"358612991,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 358612991")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd358612992);
$fwrite(fd,"358612992,%02h,%0d\n",got,err);
if(err || got !== 8'h67) `uvm_fatal("bank_preflight","byte mismatch at 358612992")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd359661567);
$fwrite(fd,"359661567,%02h,%0d\n",got,err);
if(err || got !== 8'hb9) `uvm_fatal("bank_preflight","byte mismatch at 359661567")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd359661568);
$fwrite(fd,"359661568,%02h,%0d\n",got,err);
if(err || got !== 8'h06) `uvm_fatal("bank_preflight","byte mismatch at 359661568")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd360710143);
$fwrite(fd,"360710143,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 360710143")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd360710144);
$fwrite(fd,"360710144,%02h,%0d\n",got,err);
if(err || got !== 8'h58) `uvm_fatal("bank_preflight","byte mismatch at 360710144")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd361758719);
$fwrite(fd,"361758719,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 361758719")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd361758720);
$fwrite(fd,"361758720,%02h,%0d\n",got,err);
if(err || got !== 8'h15) `uvm_fatal("bank_preflight","byte mismatch at 361758720")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd362807295);
$fwrite(fd,"362807295,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 362807295")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd362807296);
$fwrite(fd,"362807296,%02h,%0d\n",got,err);
if(err || got !== 8'hf5) `uvm_fatal("bank_preflight","byte mismatch at 362807296")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd363855871);
$fwrite(fd,"363855871,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 363855871")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd363855872);
$fwrite(fd,"363855872,%02h,%0d\n",got,err);
if(err || got !== 8'h98) `uvm_fatal("bank_preflight","byte mismatch at 363855872")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd364904447);
$fwrite(fd,"364904447,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 364904447")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd364904448);
$fwrite(fd,"364904448,%02h,%0d\n",got,err);
if(err || got !== 8'h87) `uvm_fatal("bank_preflight","byte mismatch at 364904448")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd365953023);
$fwrite(fd,"365953023,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 365953023")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd365953024);
$fwrite(fd,"365953024,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 365953024")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd367001599);
$fwrite(fd,"367001599,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 367001599")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd367001600);
$fwrite(fd,"367001600,%02h,%0d\n",got,err);
if(err || got !== 8'h40) `uvm_fatal("bank_preflight","byte mismatch at 367001600")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd368050175);
$fwrite(fd,"368050175,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 368050175")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd368050176);
$fwrite(fd,"368050176,%02h,%0d\n",got,err);
if(err || got !== 8'h5c) `uvm_fatal("bank_preflight","byte mismatch at 368050176")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd369098751);
$fwrite(fd,"369098751,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 369098751")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd369098752);
$fwrite(fd,"369098752,%02h,%0d\n",got,err);
if(err || got !== 8'h3e) `uvm_fatal("bank_preflight","byte mismatch at 369098752")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd370147327);
$fwrite(fd,"370147327,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 370147327")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd370147328);
$fwrite(fd,"370147328,%02h,%0d\n",got,err);
if(err || got !== 8'h66) `uvm_fatal("bank_preflight","byte mismatch at 370147328")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd371195903);
$fwrite(fd,"371195903,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 371195903")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd371195904);
$fwrite(fd,"371195904,%02h,%0d\n",got,err);
if(err || got !== 8'h90) `uvm_fatal("bank_preflight","byte mismatch at 371195904")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd372244479);
$fwrite(fd,"372244479,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 372244479")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd372244480);
$fwrite(fd,"372244480,%02h,%0d\n",got,err);
if(err || got !== 8'h9b) `uvm_fatal("bank_preflight","byte mismatch at 372244480")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd373293055);
$fwrite(fd,"373293055,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 373293055")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd373293056);
$fwrite(fd,"373293056,%02h,%0d\n",got,err);
if(err || got !== 8'h35) `uvm_fatal("bank_preflight","byte mismatch at 373293056")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd374341631);
$fwrite(fd,"374341631,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 374341631")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd374341632);
$fwrite(fd,"374341632,%02h,%0d\n",got,err);
if(err || got !== 8'hc5) `uvm_fatal("bank_preflight","byte mismatch at 374341632")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd375390207);
$fwrite(fd,"375390207,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 375390207")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd375390208);
$fwrite(fd,"375390208,%02h,%0d\n",got,err);
if(err || got !== 8'he5) `uvm_fatal("bank_preflight","byte mismatch at 375390208")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd376438783);
$fwrite(fd,"376438783,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 376438783")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd376438784);
$fwrite(fd,"376438784,%02h,%0d\n",got,err);
if(err || got !== 8'hd7) `uvm_fatal("bank_preflight","byte mismatch at 376438784")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd377487359);
$fwrite(fd,"377487359,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 377487359")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd377487360);
$fwrite(fd,"377487360,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 377487360")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd378535935);
$fwrite(fd,"378535935,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 378535935")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd378535936);
$fwrite(fd,"378535936,%02h,%0d\n",got,err);
if(err || got !== 8'h90) `uvm_fatal("bank_preflight","byte mismatch at 378535936")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd379584511);
$fwrite(fd,"379584511,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 379584511")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd379584512);
$fwrite(fd,"379584512,%02h,%0d\n",got,err);
if(err || got !== 8'he0) `uvm_fatal("bank_preflight","byte mismatch at 379584512")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd380633087);
$fwrite(fd,"380633087,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 380633087")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd380633088);
$fwrite(fd,"380633088,%02h,%0d\n",got,err);
if(err || got !== 8'h44) `uvm_fatal("bank_preflight","byte mismatch at 380633088")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd381681663);
$fwrite(fd,"381681663,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 381681663")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd381681664);
$fwrite(fd,"381681664,%02h,%0d\n",got,err);
if(err || got !== 8'h11) `uvm_fatal("bank_preflight","byte mismatch at 381681664")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd382730239);
$fwrite(fd,"382730239,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 382730239")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd382730240);
$fwrite(fd,"382730240,%02h,%0d\n",got,err);
if(err || got !== 8'h66) `uvm_fatal("bank_preflight","byte mismatch at 382730240")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd383778815);
$fwrite(fd,"383778815,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 383778815")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd383778816);
$fwrite(fd,"383778816,%02h,%0d\n",got,err);
if(err || got !== 8'h9f) `uvm_fatal("bank_preflight","byte mismatch at 383778816")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd384827391);
$fwrite(fd,"384827391,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 384827391")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd384827392);
$fwrite(fd,"384827392,%02h,%0d\n",got,err);
if(err || got !== 8'h72) `uvm_fatal("bank_preflight","byte mismatch at 384827392")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd385875967);
$fwrite(fd,"385875967,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 385875967")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd385875968);
$fwrite(fd,"385875968,%02h,%0d\n",got,err);
if(err || got !== 8'hae) `uvm_fatal("bank_preflight","byte mismatch at 385875968")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd386924543);
$fwrite(fd,"386924543,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 386924543")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd386924544);
$fwrite(fd,"386924544,%02h,%0d\n",got,err);
if(err || got !== 8'h1d) `uvm_fatal("bank_preflight","byte mismatch at 386924544")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd387973119);
$fwrite(fd,"387973119,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 387973119")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd387973120);
$fwrite(fd,"387973120,%02h,%0d\n",got,err);
if(err || got !== 8'hc0) `uvm_fatal("bank_preflight","byte mismatch at 387973120")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd389021695);
$fwrite(fd,"389021695,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 389021695")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd389021696);
$fwrite(fd,"389021696,%02h,%0d\n",got,err);
if(err || got !== 8'hed) `uvm_fatal("bank_preflight","byte mismatch at 389021696")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd390070271);
$fwrite(fd,"390070271,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 390070271")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd390070272);
$fwrite(fd,"390070272,%02h,%0d\n",got,err);
if(err || got !== 8'h6a) `uvm_fatal("bank_preflight","byte mismatch at 390070272")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd391118847);
$fwrite(fd,"391118847,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 391118847")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd391118848);
$fwrite(fd,"391118848,%02h,%0d\n",got,err);
if(err || got !== 8'hb0) `uvm_fatal("bank_preflight","byte mismatch at 391118848")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd392167423);
$fwrite(fd,"392167423,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 392167423")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd392167424);
$fwrite(fd,"392167424,%02h,%0d\n",got,err);
if(err || got !== 8'hb1) `uvm_fatal("bank_preflight","byte mismatch at 392167424")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd393215999);
$fwrite(fd,"393215999,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 393215999")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd393216000);
$fwrite(fd,"393216000,%02h,%0d\n",got,err);
if(err || got !== 8'h65) `uvm_fatal("bank_preflight","byte mismatch at 393216000")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd394264575);
$fwrite(fd,"394264575,%02h,%0d\n",got,err);
if(err || got !== 8'hbd) `uvm_fatal("bank_preflight","byte mismatch at 394264575")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd394264576);
$fwrite(fd,"394264576,%02h,%0d\n",got,err);
if(err || got !== 8'ha5) `uvm_fatal("bank_preflight","byte mismatch at 394264576")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd395313151);
$fwrite(fd,"395313151,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 395313151")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd395313152);
$fwrite(fd,"395313152,%02h,%0d\n",got,err);
if(err || got !== 8'hd6) `uvm_fatal("bank_preflight","byte mismatch at 395313152")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd396361727);
$fwrite(fd,"396361727,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 396361727")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd396361728);
$fwrite(fd,"396361728,%02h,%0d\n",got,err);
if(err || got !== 8'h8b) `uvm_fatal("bank_preflight","byte mismatch at 396361728")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd397410303);
$fwrite(fd,"397410303,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 397410303")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd397410304);
$fwrite(fd,"397410304,%02h,%0d\n",got,err);
if(err || got !== 8'hb8) `uvm_fatal("bank_preflight","byte mismatch at 397410304")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd398458879);
$fwrite(fd,"398458879,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 398458879")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd398458880);
$fwrite(fd,"398458880,%02h,%0d\n",got,err);
if(err || got !== 8'h89) `uvm_fatal("bank_preflight","byte mismatch at 398458880")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd399507455);
$fwrite(fd,"399507455,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 399507455")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd399507456);
$fwrite(fd,"399507456,%02h,%0d\n",got,err);
if(err || got !== 8'h94) `uvm_fatal("bank_preflight","byte mismatch at 399507456")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd400556031);
$fwrite(fd,"400556031,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 400556031")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd400556032);
$fwrite(fd,"400556032,%02h,%0d\n",got,err);
if(err || got !== 8'h56) `uvm_fatal("bank_preflight","byte mismatch at 400556032")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd401604607);
$fwrite(fd,"401604607,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 401604607")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd401604608);
$fwrite(fd,"401604608,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 401604608")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd402653183);
$fwrite(fd,"402653183,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 402653183")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd402653184);
$fwrite(fd,"402653184,%02h,%0d\n",got,err);
if(err || got !== 8'hdb) `uvm_fatal("bank_preflight","byte mismatch at 402653184")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd403701759);
$fwrite(fd,"403701759,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 403701759")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd403701760);
$fwrite(fd,"403701760,%02h,%0d\n",got,err);
if(err || got !== 8'h92) `uvm_fatal("bank_preflight","byte mismatch at 403701760")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd404750335);
$fwrite(fd,"404750335,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 404750335")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd404750336);
$fwrite(fd,"404750336,%02h,%0d\n",got,err);
if(err || got !== 8'h5f) `uvm_fatal("bank_preflight","byte mismatch at 404750336")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd405798911);
$fwrite(fd,"405798911,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 405798911")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd405798912);
$fwrite(fd,"405798912,%02h,%0d\n",got,err);
if(err || got !== 8'h51) `uvm_fatal("bank_preflight","byte mismatch at 405798912")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd406847487);
$fwrite(fd,"406847487,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 406847487")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd406847488);
$fwrite(fd,"406847488,%02h,%0d\n",got,err);
if(err || got !== 8'h8a) `uvm_fatal("bank_preflight","byte mismatch at 406847488")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd407896063);
$fwrite(fd,"407896063,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 407896063")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd407896064);
$fwrite(fd,"407896064,%02h,%0d\n",got,err);
if(err || got !== 8'h7e) `uvm_fatal("bank_preflight","byte mismatch at 407896064")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd408944639);
$fwrite(fd,"408944639,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 408944639")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd408944640);
$fwrite(fd,"408944640,%02h,%0d\n",got,err);
if(err || got !== 8'h9c) `uvm_fatal("bank_preflight","byte mismatch at 408944640")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd409993215);
$fwrite(fd,"409993215,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 409993215")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd409993216);
$fwrite(fd,"409993216,%02h,%0d\n",got,err);
if(err || got !== 8'hf9) `uvm_fatal("bank_preflight","byte mismatch at 409993216")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd411041791);
$fwrite(fd,"411041791,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 411041791")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd411041792);
$fwrite(fd,"411041792,%02h,%0d\n",got,err);
if(err || got !== 8'h4d) `uvm_fatal("bank_preflight","byte mismatch at 411041792")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd412090367);
$fwrite(fd,"412090367,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 412090367")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd412090368);
$fwrite(fd,"412090368,%02h,%0d\n",got,err);
if(err || got !== 8'h87) `uvm_fatal("bank_preflight","byte mismatch at 412090368")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd413138943);
$fwrite(fd,"413138943,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 413138943")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd413138944);
$fwrite(fd,"413138944,%02h,%0d\n",got,err);
if(err || got !== 8'hf7) `uvm_fatal("bank_preflight","byte mismatch at 413138944")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd414187519);
$fwrite(fd,"414187519,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 414187519")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd414187520);
$fwrite(fd,"414187520,%02h,%0d\n",got,err);
if(err || got !== 8'h13) `uvm_fatal("bank_preflight","byte mismatch at 414187520")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd415236095);
$fwrite(fd,"415236095,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 415236095")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd415236096);
$fwrite(fd,"415236096,%02h,%0d\n",got,err);
if(err || got !== 8'h44) `uvm_fatal("bank_preflight","byte mismatch at 415236096")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd416284671);
$fwrite(fd,"416284671,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 416284671")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd416284672);
$fwrite(fd,"416284672,%02h,%0d\n",got,err);
if(err || got !== 8'h57) `uvm_fatal("bank_preflight","byte mismatch at 416284672")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd417333247);
$fwrite(fd,"417333247,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 417333247")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd417333248);
$fwrite(fd,"417333248,%02h,%0d\n",got,err);
if(err || got !== 8'h47) `uvm_fatal("bank_preflight","byte mismatch at 417333248")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd418381823);
$fwrite(fd,"418381823,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 418381823")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd418381824);
$fwrite(fd,"418381824,%02h,%0d\n",got,err);
if(err || got !== 8'h3f) `uvm_fatal("bank_preflight","byte mismatch at 418381824")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd419430399);
$fwrite(fd,"419430399,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 419430399")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd419430400);
$fwrite(fd,"419430400,%02h,%0d\n",got,err);
if(err || got !== 8'h72) `uvm_fatal("bank_preflight","byte mismatch at 419430400")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd420478975);
$fwrite(fd,"420478975,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 420478975")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd420478976);
$fwrite(fd,"420478976,%02h,%0d\n",got,err);
if(err || got !== 8'hc6) `uvm_fatal("bank_preflight","byte mismatch at 420478976")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd421527551);
$fwrite(fd,"421527551,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 421527551")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd421527552);
$fwrite(fd,"421527552,%02h,%0d\n",got,err);
if(err || got !== 8'h81) `uvm_fatal("bank_preflight","byte mismatch at 421527552")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd422576127);
$fwrite(fd,"422576127,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 422576127")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd422576128);
$fwrite(fd,"422576128,%02h,%0d\n",got,err);
if(err || got !== 8'hb2) `uvm_fatal("bank_preflight","byte mismatch at 422576128")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd423624703);
$fwrite(fd,"423624703,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 423624703")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd423624704);
$fwrite(fd,"423624704,%02h,%0d\n",got,err);
if(err || got !== 8'h5e) `uvm_fatal("bank_preflight","byte mismatch at 423624704")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd424673279);
$fwrite(fd,"424673279,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 424673279")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd424673280);
$fwrite(fd,"424673280,%02h,%0d\n",got,err);
if(err || got !== 8'h88) `uvm_fatal("bank_preflight","byte mismatch at 424673280")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd425721855);
$fwrite(fd,"425721855,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 425721855")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd425721856);
$fwrite(fd,"425721856,%02h,%0d\n",got,err);
if(err || got !== 8'hb1) `uvm_fatal("bank_preflight","byte mismatch at 425721856")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd426770431);
$fwrite(fd,"426770431,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 426770431")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd426770432);
$fwrite(fd,"426770432,%02h,%0d\n",got,err);
if(err || got !== 8'hfd) `uvm_fatal("bank_preflight","byte mismatch at 426770432")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd427819007);
$fwrite(fd,"427819007,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 427819007")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd427819008);
$fwrite(fd,"427819008,%02h,%0d\n",got,err);
if(err || got !== 8'h5b) `uvm_fatal("bank_preflight","byte mismatch at 427819008")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd428867583);
$fwrite(fd,"428867583,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 428867583")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd428867584);
$fwrite(fd,"428867584,%02h,%0d\n",got,err);
if(err || got !== 8'hc0) `uvm_fatal("bank_preflight","byte mismatch at 428867584")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd429916159);
$fwrite(fd,"429916159,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 429916159")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd429916160);
$fwrite(fd,"429916160,%02h,%0d\n",got,err);
if(err || got !== 8'h9a) `uvm_fatal("bank_preflight","byte mismatch at 429916160")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd430964735);
$fwrite(fd,"430964735,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 430964735")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd430964736);
$fwrite(fd,"430964736,%02h,%0d\n",got,err);
if(err || got !== 8'hc1) `uvm_fatal("bank_preflight","byte mismatch at 430964736")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd432013311);
$fwrite(fd,"432013311,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 432013311")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd432013312);
$fwrite(fd,"432013312,%02h,%0d\n",got,err);
if(err || got !== 8'ha3) `uvm_fatal("bank_preflight","byte mismatch at 432013312")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd433061887);
$fwrite(fd,"433061887,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 433061887")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd433061888);
$fwrite(fd,"433061888,%02h,%0d\n",got,err);
if(err || got !== 8'hd1) `uvm_fatal("bank_preflight","byte mismatch at 433061888")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd434110463);
$fwrite(fd,"434110463,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 434110463")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd434110464);
$fwrite(fd,"434110464,%02h,%0d\n",got,err);
if(err || got !== 8'h48) `uvm_fatal("bank_preflight","byte mismatch at 434110464")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd435159039);
$fwrite(fd,"435159039,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 435159039")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd435159040);
$fwrite(fd,"435159040,%02h,%0d\n",got,err);
if(err || got !== 8'h3d) `uvm_fatal("bank_preflight","byte mismatch at 435159040")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd436207615);
$fwrite(fd,"436207615,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 436207615")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd436207616);
$fwrite(fd,"436207616,%02h,%0d\n",got,err);
if(err || got !== 8'hbd) `uvm_fatal("bank_preflight","byte mismatch at 436207616")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd437256191);
$fwrite(fd,"437256191,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 437256191")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd437256192);
$fwrite(fd,"437256192,%02h,%0d\n",got,err);
if(err || got !== 8'h39) `uvm_fatal("bank_preflight","byte mismatch at 437256192")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd438304767);
$fwrite(fd,"438304767,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 438304767")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd438304768);
$fwrite(fd,"438304768,%02h,%0d\n",got,err);
if(err || got !== 8'h2c) `uvm_fatal("bank_preflight","byte mismatch at 438304768")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd439353343);
$fwrite(fd,"439353343,%02h,%0d\n",got,err);
if(err || got !== 8'h3d) `uvm_fatal("bank_preflight","byte mismatch at 439353343")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd439353344);
$fwrite(fd,"439353344,%02h,%0d\n",got,err);
if(err || got !== 8'h60) `uvm_fatal("bank_preflight","byte mismatch at 439353344")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd440401919);
$fwrite(fd,"440401919,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 440401919")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd440401920);
$fwrite(fd,"440401920,%02h,%0d\n",got,err);
if(err || got !== 8'he1) `uvm_fatal("bank_preflight","byte mismatch at 440401920")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd441450495);
$fwrite(fd,"441450495,%02h,%0d\n",got,err);
if(err || got !== 8'hbd) `uvm_fatal("bank_preflight","byte mismatch at 441450495")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd441450496);
$fwrite(fd,"441450496,%02h,%0d\n",got,err);
if(err || got !== 8'h35) `uvm_fatal("bank_preflight","byte mismatch at 441450496")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd442499071);
$fwrite(fd,"442499071,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 442499071")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd442499072);
$fwrite(fd,"442499072,%02h,%0d\n",got,err);
if(err || got !== 8'hfd) `uvm_fatal("bank_preflight","byte mismatch at 442499072")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd443547647);
$fwrite(fd,"443547647,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 443547647")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd443547648);
$fwrite(fd,"443547648,%02h,%0d\n",got,err);
if(err || got !== 8'h28) `uvm_fatal("bank_preflight","byte mismatch at 443547648")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd444596223);
$fwrite(fd,"444596223,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 444596223")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd444596224);
$fwrite(fd,"444596224,%02h,%0d\n",got,err);
if(err || got !== 8'h8c) `uvm_fatal("bank_preflight","byte mismatch at 444596224")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd445644799);
$fwrite(fd,"445644799,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 445644799")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd445644800);
$fwrite(fd,"445644800,%02h,%0d\n",got,err);
if(err || got !== 8'hc0) `uvm_fatal("bank_preflight","byte mismatch at 445644800")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd446693375);
$fwrite(fd,"446693375,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 446693375")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd446693376);
$fwrite(fd,"446693376,%02h,%0d\n",got,err);
if(err || got !== 8'h92) `uvm_fatal("bank_preflight","byte mismatch at 446693376")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd447741951);
$fwrite(fd,"447741951,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 447741951")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd447741952);
$fwrite(fd,"447741952,%02h,%0d\n",got,err);
if(err || got !== 8'h9f) `uvm_fatal("bank_preflight","byte mismatch at 447741952")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd448790527);
$fwrite(fd,"448790527,%02h,%0d\n",got,err);
if(err || got !== 8'h39) `uvm_fatal("bank_preflight","byte mismatch at 448790527")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd448790528);
$fwrite(fd,"448790528,%02h,%0d\n",got,err);
if(err || got !== 8'h94) `uvm_fatal("bank_preflight","byte mismatch at 448790528")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd449839103);
$fwrite(fd,"449839103,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 449839103")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd449839104);
$fwrite(fd,"449839104,%02h,%0d\n",got,err);
if(err || got !== 8'h3d) `uvm_fatal("bank_preflight","byte mismatch at 449839104")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd450887679);
$fwrite(fd,"450887679,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 450887679")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd450887680);
$fwrite(fd,"450887680,%02h,%0d\n",got,err);
if(err || got !== 8'h1d) `uvm_fatal("bank_preflight","byte mismatch at 450887680")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd451936255);
$fwrite(fd,"451936255,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 451936255")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd451936256);
$fwrite(fd,"451936256,%02h,%0d\n",got,err);
if(err || got !== 8'hf3) `uvm_fatal("bank_preflight","byte mismatch at 451936256")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd452984831);
$fwrite(fd,"452984831,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 452984831")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd452984832);
$fwrite(fd,"452984832,%02h,%0d\n",got,err);
if(err || got !== 8'hea) `uvm_fatal("bank_preflight","byte mismatch at 452984832")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd454033407);
$fwrite(fd,"454033407,%02h,%0d\n",got,err);
if(err || got !== 8'hb9) `uvm_fatal("bank_preflight","byte mismatch at 454033407")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd454033408);
$fwrite(fd,"454033408,%02h,%0d\n",got,err);
if(err || got !== 8'h9f) `uvm_fatal("bank_preflight","byte mismatch at 454033408")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd455081983);
$fwrite(fd,"455081983,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 455081983")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd455081984);
$fwrite(fd,"455081984,%02h,%0d\n",got,err);
if(err || got !== 8'ha4) `uvm_fatal("bank_preflight","byte mismatch at 455081984")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd456130559);
$fwrite(fd,"456130559,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 456130559")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd456130560);
$fwrite(fd,"456130560,%02h,%0d\n",got,err);
if(err || got !== 8'he7) `uvm_fatal("bank_preflight","byte mismatch at 456130560")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd457179135);
$fwrite(fd,"457179135,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 457179135")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd457179136);
$fwrite(fd,"457179136,%02h,%0d\n",got,err);
if(err || got !== 8'h31) `uvm_fatal("bank_preflight","byte mismatch at 457179136")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd458227711);
$fwrite(fd,"458227711,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 458227711")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd458227712);
$fwrite(fd,"458227712,%02h,%0d\n",got,err);
if(err || got !== 8'hfd) `uvm_fatal("bank_preflight","byte mismatch at 458227712")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd459276287);
$fwrite(fd,"459276287,%02h,%0d\n",got,err);
if(err || got !== 8'h3d) `uvm_fatal("bank_preflight","byte mismatch at 459276287")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd459276288);
$fwrite(fd,"459276288,%02h,%0d\n",got,err);
if(err || got !== 8'h5b) `uvm_fatal("bank_preflight","byte mismatch at 459276288")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd460324863);
$fwrite(fd,"460324863,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 460324863")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd460324864);
$fwrite(fd,"460324864,%02h,%0d\n",got,err);
if(err || got !== 8'hf3) `uvm_fatal("bank_preflight","byte mismatch at 460324864")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd461373439);
$fwrite(fd,"461373439,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 461373439")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd461373440);
$fwrite(fd,"461373440,%02h,%0d\n",got,err);
if(err || got !== 8'he9) `uvm_fatal("bank_preflight","byte mismatch at 461373440")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd462422015);
$fwrite(fd,"462422015,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 462422015")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd462422016);
$fwrite(fd,"462422016,%02h,%0d\n",got,err);
if(err || got !== 8'h36) `uvm_fatal("bank_preflight","byte mismatch at 462422016")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd463470591);
$fwrite(fd,"463470591,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 463470591")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd463470592);
$fwrite(fd,"463470592,%02h,%0d\n",got,err);
if(err || got !== 8'h48) `uvm_fatal("bank_preflight","byte mismatch at 463470592")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd464519167);
$fwrite(fd,"464519167,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 464519167")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd464519168);
$fwrite(fd,"464519168,%02h,%0d\n",got,err);
if(err || got !== 8'h5e) `uvm_fatal("bank_preflight","byte mismatch at 464519168")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd465567743);
$fwrite(fd,"465567743,%02h,%0d\n",got,err);
if(err || got !== 8'hbd) `uvm_fatal("bank_preflight","byte mismatch at 465567743")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd465567744);
$fwrite(fd,"465567744,%02h,%0d\n",got,err);
if(err || got !== 8'hcc) `uvm_fatal("bank_preflight","byte mismatch at 465567744")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd466616319);
$fwrite(fd,"466616319,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 466616319")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd466616320);
$fwrite(fd,"466616320,%02h,%0d\n",got,err);
if(err || got !== 8'h5a) `uvm_fatal("bank_preflight","byte mismatch at 466616320")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd467664895);
$fwrite(fd,"467664895,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 467664895")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd467664896);
$fwrite(fd,"467664896,%02h,%0d\n",got,err);
if(err || got !== 8'h89) `uvm_fatal("bank_preflight","byte mismatch at 467664896")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd468713471);
$fwrite(fd,"468713471,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 468713471")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd468713472);
$fwrite(fd,"468713472,%02h,%0d\n",got,err);
if(err || got !== 8'h98) `uvm_fatal("bank_preflight","byte mismatch at 468713472")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd469762047);
$fwrite(fd,"469762047,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 469762047")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd469762048);
$fwrite(fd,"469762048,%02h,%0d\n",got,err);
if(err || got !== 8'h17) `uvm_fatal("bank_preflight","byte mismatch at 469762048")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd470810623);
$fwrite(fd,"470810623,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 470810623")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd470810624);
$fwrite(fd,"470810624,%02h,%0d\n",got,err);
if(err || got !== 8'h68) `uvm_fatal("bank_preflight","byte mismatch at 470810624")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd471859199);
$fwrite(fd,"471859199,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 471859199")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd471859200);
$fwrite(fd,"471859200,%02h,%0d\n",got,err);
if(err || got !== 8'h7e) `uvm_fatal("bank_preflight","byte mismatch at 471859200")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd472907775);
$fwrite(fd,"472907775,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 472907775")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd472907776);
$fwrite(fd,"472907776,%02h,%0d\n",got,err);
if(err || got !== 8'h81) `uvm_fatal("bank_preflight","byte mismatch at 472907776")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd473956351);
$fwrite(fd,"473956351,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 473956351")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd473956352);
$fwrite(fd,"473956352,%02h,%0d\n",got,err);
if(err || got !== 8'h14) `uvm_fatal("bank_preflight","byte mismatch at 473956352")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd475004927);
$fwrite(fd,"475004927,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 475004927")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd475004928);
$fwrite(fd,"475004928,%02h,%0d\n",got,err);
if(err || got !== 8'hf2) `uvm_fatal("bank_preflight","byte mismatch at 475004928")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd476053503);
$fwrite(fd,"476053503,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 476053503")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd476053504);
$fwrite(fd,"476053504,%02h,%0d\n",got,err);
if(err || got !== 8'ha7) `uvm_fatal("bank_preflight","byte mismatch at 476053504")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd477102079);
$fwrite(fd,"477102079,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 477102079")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd477102080);
$fwrite(fd,"477102080,%02h,%0d\n",got,err);
if(err || got !== 8'h5d) `uvm_fatal("bank_preflight","byte mismatch at 477102080")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd478150655);
$fwrite(fd,"478150655,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 478150655")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd478150656);
$fwrite(fd,"478150656,%02h,%0d\n",got,err);
if(err || got !== 8'h05) `uvm_fatal("bank_preflight","byte mismatch at 478150656")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd479199231);
$fwrite(fd,"479199231,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 479199231")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd479199232);
$fwrite(fd,"479199232,%02h,%0d\n",got,err);
if(err || got !== 8'h82) `uvm_fatal("bank_preflight","byte mismatch at 479199232")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd480247807);
$fwrite(fd,"480247807,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 480247807")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd480247808);
$fwrite(fd,"480247808,%02h,%0d\n",got,err);
if(err || got !== 8'h51) `uvm_fatal("bank_preflight","byte mismatch at 480247808")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd481296383);
$fwrite(fd,"481296383,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 481296383")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd481296384);
$fwrite(fd,"481296384,%02h,%0d\n",got,err);
if(err || got !== 8'hc2) `uvm_fatal("bank_preflight","byte mismatch at 481296384")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd482344959);
$fwrite(fd,"482344959,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 482344959")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd482344960);
$fwrite(fd,"482344960,%02h,%0d\n",got,err);
if(err || got !== 8'ha6) `uvm_fatal("bank_preflight","byte mismatch at 482344960")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd483393535);
$fwrite(fd,"483393535,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 483393535")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd483393536);
$fwrite(fd,"483393536,%02h,%0d\n",got,err);
if(err || got !== 8'h4d) `uvm_fatal("bank_preflight","byte mismatch at 483393536")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd484442111);
$fwrite(fd,"484442111,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 484442111")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd484442112);
$fwrite(fd,"484442112,%02h,%0d\n",got,err);
if(err || got !== 8'hcc) `uvm_fatal("bank_preflight","byte mismatch at 484442112")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd485490687);
$fwrite(fd,"485490687,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 485490687")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd485490688);
$fwrite(fd,"485490688,%02h,%0d\n",got,err);
if(err || got !== 8'h6d) `uvm_fatal("bank_preflight","byte mismatch at 485490688")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd486539263);
$fwrite(fd,"486539263,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 486539263")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd486539264);
$fwrite(fd,"486539264,%02h,%0d\n",got,err);
if(err || got !== 8'h00) `uvm_fatal("bank_preflight","byte mismatch at 486539264")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd487587839);
$fwrite(fd,"487587839,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 487587839")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd487587840);
$fwrite(fd,"487587840,%02h,%0d\n",got,err);
if(err || got !== 8'h4d) `uvm_fatal("bank_preflight","byte mismatch at 487587840")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd488636415);
$fwrite(fd,"488636415,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 488636415")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd488636416);
$fwrite(fd,"488636416,%02h,%0d\n",got,err);
if(err || got !== 8'h20) `uvm_fatal("bank_preflight","byte mismatch at 488636416")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd489684991);
$fwrite(fd,"489684991,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 489684991")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd489684992);
$fwrite(fd,"489684992,%02h,%0d\n",got,err);
if(err || got !== 8'h47) `uvm_fatal("bank_preflight","byte mismatch at 489684992")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd490733567);
$fwrite(fd,"490733567,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 490733567")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd490733568);
$fwrite(fd,"490733568,%02h,%0d\n",got,err);
if(err || got !== 8'h10) `uvm_fatal("bank_preflight","byte mismatch at 490733568")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd491782143);
$fwrite(fd,"491782143,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 491782143")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd491782144);
$fwrite(fd,"491782144,%02h,%0d\n",got,err);
if(err || got !== 8'h9a) `uvm_fatal("bank_preflight","byte mismatch at 491782144")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd492830719);
$fwrite(fd,"492830719,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 492830719")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd492830720);
$fwrite(fd,"492830720,%02h,%0d\n",got,err);
if(err || got !== 8'h48) `uvm_fatal("bank_preflight","byte mismatch at 492830720")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd493879295);
$fwrite(fd,"493879295,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 493879295")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd493879296);
$fwrite(fd,"493879296,%02h,%0d\n",got,err);
if(err || got !== 8'h1b) `uvm_fatal("bank_preflight","byte mismatch at 493879296")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd494927871);
$fwrite(fd,"494927871,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 494927871")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd494927872);
$fwrite(fd,"494927872,%02h,%0d\n",got,err);
if(err || got !== 8'h8b) `uvm_fatal("bank_preflight","byte mismatch at 494927872")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd495976447);
$fwrite(fd,"495976447,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 495976447")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd495976448);
$fwrite(fd,"495976448,%02h,%0d\n",got,err);
if(err || got !== 8'h4f) `uvm_fatal("bank_preflight","byte mismatch at 495976448")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd497025023);
$fwrite(fd,"497025023,%02h,%0d\n",got,err);
if(err || got !== 8'h3d) `uvm_fatal("bank_preflight","byte mismatch at 497025023")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd497025024);
$fwrite(fd,"497025024,%02h,%0d\n",got,err);
if(err || got !== 8'h7d) `uvm_fatal("bank_preflight","byte mismatch at 497025024")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd498073599);
$fwrite(fd,"498073599,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 498073599")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd498073600);
$fwrite(fd,"498073600,%02h,%0d\n",got,err);
if(err || got !== 8'h20) `uvm_fatal("bank_preflight","byte mismatch at 498073600")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd499122175);
$fwrite(fd,"499122175,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 499122175")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd499122176);
$fwrite(fd,"499122176,%02h,%0d\n",got,err);
if(err || got !== 8'h8a) `uvm_fatal("bank_preflight","byte mismatch at 499122176")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd500170751);
$fwrite(fd,"500170751,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 500170751")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd500170752);
$fwrite(fd,"500170752,%02h,%0d\n",got,err);
if(err || got !== 8'h56) `uvm_fatal("bank_preflight","byte mismatch at 500170752")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd501219327);
$fwrite(fd,"501219327,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 501219327")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd501219328);
$fwrite(fd,"501219328,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 501219328")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd502267903);
$fwrite(fd,"502267903,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 502267903")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd502267904);
$fwrite(fd,"502267904,%02h,%0d\n",got,err);
if(err || got !== 8'h4c) `uvm_fatal("bank_preflight","byte mismatch at 502267904")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd503316479);
$fwrite(fd,"503316479,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 503316479")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd503316480);
$fwrite(fd,"503316480,%02h,%0d\n",got,err);
if(err || got !== 8'ha8) `uvm_fatal("bank_preflight","byte mismatch at 503316480")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd504365055);
$fwrite(fd,"504365055,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 504365055")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd504365056);
$fwrite(fd,"504365056,%02h,%0d\n",got,err);
if(err || got !== 8'hc2) `uvm_fatal("bank_preflight","byte mismatch at 504365056")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd505413631);
$fwrite(fd,"505413631,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 505413631")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd505413632);
$fwrite(fd,"505413632,%02h,%0d\n",got,err);
if(err || got !== 8'hc7) `uvm_fatal("bank_preflight","byte mismatch at 505413632")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd506462207);
$fwrite(fd,"506462207,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 506462207")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd506462208);
$fwrite(fd,"506462208,%02h,%0d\n",got,err);
if(err || got !== 8'hb2) `uvm_fatal("bank_preflight","byte mismatch at 506462208")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd507510783);
$fwrite(fd,"507510783,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 507510783")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd507510784);
$fwrite(fd,"507510784,%02h,%0d\n",got,err);
if(err || got !== 8'h8e) `uvm_fatal("bank_preflight","byte mismatch at 507510784")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd508559359);
$fwrite(fd,"508559359,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 508559359")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd508559360);
$fwrite(fd,"508559360,%02h,%0d\n",got,err);
if(err || got !== 8'h5d) `uvm_fatal("bank_preflight","byte mismatch at 508559360")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd509607935);
$fwrite(fd,"509607935,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 509607935")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd509607936);
$fwrite(fd,"509607936,%02h,%0d\n",got,err);
if(err || got !== 8'hae) `uvm_fatal("bank_preflight","byte mismatch at 509607936")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd510656511);
$fwrite(fd,"510656511,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 510656511")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd510656512);
$fwrite(fd,"510656512,%02h,%0d\n",got,err);
if(err || got !== 8'h8e) `uvm_fatal("bank_preflight","byte mismatch at 510656512")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd511705087);
$fwrite(fd,"511705087,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 511705087")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd511705088);
$fwrite(fd,"511705088,%02h,%0d\n",got,err);
if(err || got !== 8'h39) `uvm_fatal("bank_preflight","byte mismatch at 511705088")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd512753663);
$fwrite(fd,"512753663,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 512753663")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd512753664);
$fwrite(fd,"512753664,%02h,%0d\n",got,err);
if(err || got !== 8'h39) `uvm_fatal("bank_preflight","byte mismatch at 512753664")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd513802239);
$fwrite(fd,"513802239,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 513802239")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd513802240);
$fwrite(fd,"513802240,%02h,%0d\n",got,err);
if(err || got !== 8'hce) `uvm_fatal("bank_preflight","byte mismatch at 513802240")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd514850815);
$fwrite(fd,"514850815,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 514850815")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd514850816);
$fwrite(fd,"514850816,%02h,%0d\n",got,err);
if(err || got !== 8'h35) `uvm_fatal("bank_preflight","byte mismatch at 514850816")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd515899391);
$fwrite(fd,"515899391,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 515899391")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd515899392);
$fwrite(fd,"515899392,%02h,%0d\n",got,err);
if(err || got !== 8'hf7) `uvm_fatal("bank_preflight","byte mismatch at 515899392")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd516947967);
$fwrite(fd,"516947967,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 516947967")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd516947968);
$fwrite(fd,"516947968,%02h,%0d\n",got,err);
if(err || got !== 8'h5e) `uvm_fatal("bank_preflight","byte mismatch at 516947968")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd517996543);
$fwrite(fd,"517996543,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 517996543")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd517996544);
$fwrite(fd,"517996544,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 517996544")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd519045119);
$fwrite(fd,"519045119,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 519045119")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd519045120);
$fwrite(fd,"519045120,%02h,%0d\n",got,err);
if(err || got !== 8'ha9) `uvm_fatal("bank_preflight","byte mismatch at 519045120")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd520093695);
$fwrite(fd,"520093695,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 520093695")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd520093696);
$fwrite(fd,"520093696,%02h,%0d\n",got,err);
if(err || got !== 8'h68) `uvm_fatal("bank_preflight","byte mismatch at 520093696")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd521142271);
$fwrite(fd,"521142271,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 521142271")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd521142272);
$fwrite(fd,"521142272,%02h,%0d\n",got,err);
if(err || got !== 8'h0b) `uvm_fatal("bank_preflight","byte mismatch at 521142272")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd522190847);
$fwrite(fd,"522190847,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 522190847")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd522190848);
$fwrite(fd,"522190848,%02h,%0d\n",got,err);
if(err || got !== 8'h85) `uvm_fatal("bank_preflight","byte mismatch at 522190848")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd523239423);
$fwrite(fd,"523239423,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 523239423")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd523239424);
$fwrite(fd,"523239424,%02h,%0d\n",got,err);
if(err || got !== 8'hd3) `uvm_fatal("bank_preflight","byte mismatch at 523239424")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd524287999);
$fwrite(fd,"524287999,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 524287999")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd524288000);
$fwrite(fd,"524288000,%02h,%0d\n",got,err);
if(err || got !== 8'h2e) `uvm_fatal("bank_preflight","byte mismatch at 524288000")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd525336575);
$fwrite(fd,"525336575,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 525336575")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd525336576);
$fwrite(fd,"525336576,%02h,%0d\n",got,err);
if(err || got !== 8'hb2) `uvm_fatal("bank_preflight","byte mismatch at 525336576")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd526385151);
$fwrite(fd,"526385151,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 526385151")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd526385152);
$fwrite(fd,"526385152,%02h,%0d\n",got,err);
if(err || got !== 8'h64) `uvm_fatal("bank_preflight","byte mismatch at 526385152")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd527433727);
$fwrite(fd,"527433727,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 527433727")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd527433728);
$fwrite(fd,"527433728,%02h,%0d\n",got,err);
if(err || got !== 8'h4c) `uvm_fatal("bank_preflight","byte mismatch at 527433728")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd528482303);
$fwrite(fd,"528482303,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 528482303")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd528482304);
$fwrite(fd,"528482304,%02h,%0d\n",got,err);
if(err || got !== 8'h99) `uvm_fatal("bank_preflight","byte mismatch at 528482304")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd529530879);
$fwrite(fd,"529530879,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 529530879")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd529530880);
$fwrite(fd,"529530880,%02h,%0d\n",got,err);
if(err || got !== 8'ha8) `uvm_fatal("bank_preflight","byte mismatch at 529530880")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd530579455);
$fwrite(fd,"530579455,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 530579455")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd530579456);
$fwrite(fd,"530579456,%02h,%0d\n",got,err);
if(err || got !== 8'h70) `uvm_fatal("bank_preflight","byte mismatch at 530579456")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd531628031);
$fwrite(fd,"531628031,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 531628031")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd531628032);
$fwrite(fd,"531628032,%02h,%0d\n",got,err);
if(err || got !== 8'h75) `uvm_fatal("bank_preflight","byte mismatch at 531628032")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd532676607);
$fwrite(fd,"532676607,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 532676607")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd532676608);
$fwrite(fd,"532676608,%02h,%0d\n",got,err);
if(err || got !== 8'hc1) `uvm_fatal("bank_preflight","byte mismatch at 532676608")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd533725183);
$fwrite(fd,"533725183,%02h,%0d\n",got,err);
if(err || got !== 8'hb9) `uvm_fatal("bank_preflight","byte mismatch at 533725183")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd533725184);
$fwrite(fd,"533725184,%02h,%0d\n",got,err);
if(err || got !== 8'ha7) `uvm_fatal("bank_preflight","byte mismatch at 533725184")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd534773759);
$fwrite(fd,"534773759,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 534773759")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd534773760);
$fwrite(fd,"534773760,%02h,%0d\n",got,err);
if(err || got !== 8'hd7) `uvm_fatal("bank_preflight","byte mismatch at 534773760")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd535822335);
$fwrite(fd,"535822335,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 535822335")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd535822336);
$fwrite(fd,"535822336,%02h,%0d\n",got,err);
if(err || got !== 8'h09) `uvm_fatal("bank_preflight","byte mismatch at 535822336")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870880);
$fwrite(fd,"536870880,%02h,%0d\n",got,err);
if(err || got !== 8'h4b) `uvm_fatal("bank_preflight","byte mismatch at 536870880")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870881);
$fwrite(fd,"536870881,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 536870881")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870882);
$fwrite(fd,"536870882,%02h,%0d\n",got,err);
if(err || got !== 8'h10) `uvm_fatal("bank_preflight","byte mismatch at 536870882")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870883);
$fwrite(fd,"536870883,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 536870883")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870884);
$fwrite(fd,"536870884,%02h,%0d\n",got,err);
if(err || got !== 8'hd7) `uvm_fatal("bank_preflight","byte mismatch at 536870884")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870885);
$fwrite(fd,"536870885,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 536870885")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870886);
$fwrite(fd,"536870886,%02h,%0d\n",got,err);
if(err || got !== 8'hf1) `uvm_fatal("bank_preflight","byte mismatch at 536870886")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870887);
$fwrite(fd,"536870887,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 536870887")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870888);
$fwrite(fd,"536870888,%02h,%0d\n",got,err);
if(err || got !== 8'h7d) `uvm_fatal("bank_preflight","byte mismatch at 536870888")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870889);
$fwrite(fd,"536870889,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 536870889")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870890);
$fwrite(fd,"536870890,%02h,%0d\n",got,err);
if(err || got !== 8'h29) `uvm_fatal("bank_preflight","byte mismatch at 536870890")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870891);
$fwrite(fd,"536870891,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 536870891")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870892);
$fwrite(fd,"536870892,%02h,%0d\n",got,err);
if(err || got !== 8'h45) `uvm_fatal("bank_preflight","byte mismatch at 536870892")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870893);
$fwrite(fd,"536870893,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 536870893")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870894);
$fwrite(fd,"536870894,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 536870894")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870895);
$fwrite(fd,"536870895,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 536870895")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870896);
$fwrite(fd,"536870896,%02h,%0d\n",got,err);
if(err || got !== 8'h47) `uvm_fatal("bank_preflight","byte mismatch at 536870896")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870897);
$fwrite(fd,"536870897,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 536870897")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870898);
$fwrite(fd,"536870898,%02h,%0d\n",got,err);
if(err || got !== 8'ha7) `uvm_fatal("bank_preflight","byte mismatch at 536870898")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870899);
$fwrite(fd,"536870899,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 536870899")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870900);
$fwrite(fd,"536870900,%02h,%0d\n",got,err);
if(err || got !== 8'h9d) `uvm_fatal("bank_preflight","byte mismatch at 536870900")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870901);
$fwrite(fd,"536870901,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 536870901")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870902);
$fwrite(fd,"536870902,%02h,%0d\n",got,err);
if(err || got !== 8'h0b) `uvm_fatal("bank_preflight","byte mismatch at 536870902")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870903);
$fwrite(fd,"536870903,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 536870903")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870904);
$fwrite(fd,"536870904,%02h,%0d\n",got,err);
if(err || got !== 8'h0b) `uvm_fatal("bank_preflight","byte mismatch at 536870904")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870905);
$fwrite(fd,"536870905,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 536870905")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870906);
$fwrite(fd,"536870906,%02h,%0d\n",got,err);
if(err || got !== 8'h55) `uvm_fatal("bank_preflight","byte mismatch at 536870906")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870907);
$fwrite(fd,"536870907,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 536870907")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870908);
$fwrite(fd,"536870908,%02h,%0d\n",got,err);
if(err || got !== 8'hc4) `uvm_fatal("bank_preflight","byte mismatch at 536870908")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870909);
$fwrite(fd,"536870909,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 536870909")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870910);
$fwrite(fd,"536870910,%02h,%0d\n",got,err);
if(err || got !== 8'h64) `uvm_fatal("bank_preflight","byte mismatch at 536870910")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870911);
$fwrite(fd,"536870911,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 536870911")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870912);
$fwrite(fd,"536870912,%02h,%0d\n",got,err);
if(err || got !== 8'h41) `uvm_fatal("bank_preflight","byte mismatch at 536870912")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870913);
$fwrite(fd,"536870913,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 536870913")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870914);
$fwrite(fd,"536870914,%02h,%0d\n",got,err);
if(err || got !== 8'h6f) `uvm_fatal("bank_preflight","byte mismatch at 536870914")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870915);
$fwrite(fd,"536870915,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 536870915")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870916);
$fwrite(fd,"536870916,%02h,%0d\n",got,err);
if(err || got !== 8'hd5) `uvm_fatal("bank_preflight","byte mismatch at 536870916")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870917);
$fwrite(fd,"536870917,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 536870917")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870918);
$fwrite(fd,"536870918,%02h,%0d\n",got,err);
if(err || got !== 8'h37) `uvm_fatal("bank_preflight","byte mismatch at 536870918")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870919);
$fwrite(fd,"536870919,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 536870919")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870920);
$fwrite(fd,"536870920,%02h,%0d\n",got,err);
if(err || got !== 8'had) `uvm_fatal("bank_preflight","byte mismatch at 536870920")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870921);
$fwrite(fd,"536870921,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 536870921")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870922);
$fwrite(fd,"536870922,%02h,%0d\n",got,err);
if(err || got !== 8'h01) `uvm_fatal("bank_preflight","byte mismatch at 536870922")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870923);
$fwrite(fd,"536870923,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 536870923")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870924);
$fwrite(fd,"536870924,%02h,%0d\n",got,err);
if(err || got !== 8'hc9) `uvm_fatal("bank_preflight","byte mismatch at 536870924")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870925);
$fwrite(fd,"536870925,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 536870925")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870926);
$fwrite(fd,"536870926,%02h,%0d\n",got,err);
if(err || got !== 8'h09) `uvm_fatal("bank_preflight","byte mismatch at 536870926")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870927);
$fwrite(fd,"536870927,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 536870927")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870928);
$fwrite(fd,"536870928,%02h,%0d\n",got,err);
if(err || got !== 8'h62) `uvm_fatal("bank_preflight","byte mismatch at 536870928")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870929);
$fwrite(fd,"536870929,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 536870929")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870930);
$fwrite(fd,"536870930,%02h,%0d\n",got,err);
if(err || got !== 8'h0c) `uvm_fatal("bank_preflight","byte mismatch at 536870930")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870931);
$fwrite(fd,"536870931,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 536870931")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870932);
$fwrite(fd,"536870932,%02h,%0d\n",got,err);
if(err || got !== 8'he7) `uvm_fatal("bank_preflight","byte mismatch at 536870932")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870933);
$fwrite(fd,"536870933,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 536870933")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870934);
$fwrite(fd,"536870934,%02h,%0d\n",got,err);
if(err || got !== 8'h86) `uvm_fatal("bank_preflight","byte mismatch at 536870934")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870935);
$fwrite(fd,"536870935,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 536870935")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870936);
$fwrite(fd,"536870936,%02h,%0d\n",got,err);
if(err || got !== 8'h42) `uvm_fatal("bank_preflight","byte mismatch at 536870936")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870937);
$fwrite(fd,"536870937,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 536870937")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870938);
$fwrite(fd,"536870938,%02h,%0d\n",got,err);
if(err || got !== 8'h02) `uvm_fatal("bank_preflight","byte mismatch at 536870938")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870939);
$fwrite(fd,"536870939,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 536870939")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870940);
$fwrite(fd,"536870940,%02h,%0d\n",got,err);
if(err || got !== 8'hde) `uvm_fatal("bank_preflight","byte mismatch at 536870940")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870941);
$fwrite(fd,"536870941,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 536870941")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870942);
$fwrite(fd,"536870942,%02h,%0d\n",got,err);
if(err || got !== 8'he4) `uvm_fatal("bank_preflight","byte mismatch at 536870942")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870943);
$fwrite(fd,"536870943,%02h,%0d\n",got,err);
if(err || got !== 8'hb9) `uvm_fatal("bank_preflight","byte mismatch at 536870943")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd536870944);
$fwrite(fd,"536870944,%02h,%0d\n",got,err);
if(err || got !== 8'h59) `uvm_fatal("bank_preflight","byte mismatch at 536870944")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd537919487);
$fwrite(fd,"537919487,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 537919487")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd537919488);
$fwrite(fd,"537919488,%02h,%0d\n",got,err);
if(err || got !== 8'h70) `uvm_fatal("bank_preflight","byte mismatch at 537919488")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd538968063);
$fwrite(fd,"538968063,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 538968063")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd538968064);
$fwrite(fd,"538968064,%02h,%0d\n",got,err);
if(err || got !== 8'h66) `uvm_fatal("bank_preflight","byte mismatch at 538968064")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd540016639);
$fwrite(fd,"540016639,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 540016639")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd540016640);
$fwrite(fd,"540016640,%02h,%0d\n",got,err);
if(err || got !== 8'he4) `uvm_fatal("bank_preflight","byte mismatch at 540016640")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd541065215);
$fwrite(fd,"541065215,%02h,%0d\n",got,err);
if(err || got !== 8'hba) `uvm_fatal("bank_preflight","byte mismatch at 541065215")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd541065216);
$fwrite(fd,"541065216,%02h,%0d\n",got,err);
if(err || got !== 8'h39) `uvm_fatal("bank_preflight","byte mismatch at 541065216")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd542113791);
$fwrite(fd,"542113791,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 542113791")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd542113792);
$fwrite(fd,"542113792,%02h,%0d\n",got,err);
if(err || got !== 8'h28) `uvm_fatal("bank_preflight","byte mismatch at 542113792")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd543162367);
$fwrite(fd,"543162367,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 543162367")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd543162368);
$fwrite(fd,"543162368,%02h,%0d\n",got,err);
if(err || got !== 8'hbd) `uvm_fatal("bank_preflight","byte mismatch at 543162368")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd544210943);
$fwrite(fd,"544210943,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 544210943")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd544210944);
$fwrite(fd,"544210944,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 544210944")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545259519);
$fwrite(fd,"545259519,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 545259519")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545259520);
$fwrite(fd,"545259520,%02h,%0d\n",got,err);
if(err || got !== 8'hf7) `uvm_fatal("bank_preflight","byte mismatch at 545259520")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685471);
$fwrite(fd,"545685471,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 545685471")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685472);
$fwrite(fd,"545685472,%02h,%0d\n",got,err);
if(err || got !== 8'h4b) `uvm_fatal("bank_preflight","byte mismatch at 545685472")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685473);
$fwrite(fd,"545685473,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 545685473")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685474);
$fwrite(fd,"545685474,%02h,%0d\n",got,err);
if(err || got !== 8'h1b) `uvm_fatal("bank_preflight","byte mismatch at 545685474")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685475);
$fwrite(fd,"545685475,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 545685475")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685476);
$fwrite(fd,"545685476,%02h,%0d\n",got,err);
if(err || got !== 8'h2f) `uvm_fatal("bank_preflight","byte mismatch at 545685476")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685477);
$fwrite(fd,"545685477,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 545685477")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685478);
$fwrite(fd,"545685478,%02h,%0d\n",got,err);
if(err || got !== 8'hc5) `uvm_fatal("bank_preflight","byte mismatch at 545685478")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685479);
$fwrite(fd,"545685479,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 545685479")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685480);
$fwrite(fd,"545685480,%02h,%0d\n",got,err);
if(err || got !== 8'h1b) `uvm_fatal("bank_preflight","byte mismatch at 545685480")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685481);
$fwrite(fd,"545685481,%02h,%0d\n",got,err);
if(err || got !== 8'hbb) `uvm_fatal("bank_preflight","byte mismatch at 545685481")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685482);
$fwrite(fd,"545685482,%02h,%0d\n",got,err);
if(err || got !== 8'h0e) `uvm_fatal("bank_preflight","byte mismatch at 545685482")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685483);
$fwrite(fd,"545685483,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 545685483")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685484);
$fwrite(fd,"545685484,%02h,%0d\n",got,err);
if(err || got !== 8'h7c) `uvm_fatal("bank_preflight","byte mismatch at 545685484")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685485);
$fwrite(fd,"545685485,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 545685485")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685486);
$fwrite(fd,"545685486,%02h,%0d\n",got,err);
if(err || got !== 8'h84) `uvm_fatal("bank_preflight","byte mismatch at 545685486")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685487);
$fwrite(fd,"545685487,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 545685487")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685488);
$fwrite(fd,"545685488,%02h,%0d\n",got,err);
if(err || got !== 8'h25) `uvm_fatal("bank_preflight","byte mismatch at 545685488")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685489);
$fwrite(fd,"545685489,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 545685489")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685490);
$fwrite(fd,"545685490,%02h,%0d\n",got,err);
if(err || got !== 8'ha6) `uvm_fatal("bank_preflight","byte mismatch at 545685490")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685491);
$fwrite(fd,"545685491,%02h,%0d\n",got,err);
if(err || got !== 8'h3b) `uvm_fatal("bank_preflight","byte mismatch at 545685491")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685492);
$fwrite(fd,"545685492,%02h,%0d\n",got,err);
if(err || got !== 8'h3a) `uvm_fatal("bank_preflight","byte mismatch at 545685492")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685493);
$fwrite(fd,"545685493,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 545685493")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685494);
$fwrite(fd,"545685494,%02h,%0d\n",got,err);
if(err || got !== 8'h7b) `uvm_fatal("bank_preflight","byte mismatch at 545685494")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685495);
$fwrite(fd,"545685495,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 545685495")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685496);
$fwrite(fd,"545685496,%02h,%0d\n",got,err);
if(err || got !== 8'h75) `uvm_fatal("bank_preflight","byte mismatch at 545685496")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685497);
$fwrite(fd,"545685497,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 545685497")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685498);
$fwrite(fd,"545685498,%02h,%0d\n",got,err);
if(err || got !== 8'h06) `uvm_fatal("bank_preflight","byte mismatch at 545685498")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685499);
$fwrite(fd,"545685499,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 545685499")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685500);
$fwrite(fd,"545685500,%02h,%0d\n",got,err);
if(err || got !== 8'h06) `uvm_fatal("bank_preflight","byte mismatch at 545685500")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685501);
$fwrite(fd,"545685501,%02h,%0d\n",got,err);
if(err || got !== 8'hbc) `uvm_fatal("bank_preflight","byte mismatch at 545685501")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685502);
$fwrite(fd,"545685502,%02h,%0d\n",got,err);
if(err || got !== 8'h99) `uvm_fatal("bank_preflight","byte mismatch at 545685502")
err=mem_blk_pages_weights.pages[0].read_one_elem(got,64'd545685503);
$fwrite(fd,"545685503,%02h,%0d\n",got,err);
if(err || got !== 8'h3c) `uvm_fatal("bank_preflight","byte mismatch at 545685503")
$fclose(fd);
$display("BANK_FULL_INPUT_SENTINEL_PASS checked=1522");
lmh_memory_probe_pkg::sample("after_1522_sentinels",1522);
end

        fpath.delete();

        fork
            forever begin
                wait(write_data_finish_control);
                `uvm_info("", "trigger_allaxilite_data_write_finish", UVM_LOW)
                @(posedge misc_if.clock);
                write_data_finish_control = 0;
                -> allaxilite_write_data_finish;
            end
            forever begin
                wait(read_data_finish_control);
                `uvm_info("", "trigger_allaxilite_data_read_finish", UVM_LOW)
                @(posedge misc_if.clock);
                read_data_finish_control = 0;
                -> allaxilite_read_data_finish;
            end
            forever begin
                //this is non-pipeline case
                forever begin
                    @(negedge misc_if.clock);
                    if(misc_if.dut2tb_ap_done===1) break;
                end
                @(posedge misc_if.clock);
                @allaxilite_read_data_finish;
                @(posedge misc_if.clock);
                @allaxilite_write_data_finish;
                @(posedge misc_if.clock);
                -> ap_ready_for_nexttrans;
                `uvm_info(this.get_full_name(), "trigger event ap_ready_for_nexttrans", UVM_LOW)
                fork
                    begin
                        misc_if.ap_ready_for_nexttrans = 1;
                        @(posedge misc_if.clock);
                        misc_if.ap_ready_for_nexttrans = 0;
                    end
                join_none
            end
            forever begin
                forever begin
                    @(negedge misc_if.clock);
                    if(misc_if.dut2tb_ap_done===1) break;
                end
                @(posedge misc_if.clock);
                fork
                    begin
                        @(negedge misc_if.clock);
                        -> misc_if.dut2tb_ap_done_evt;
                        #0;
                        -> misc_if.dut2tb_ap_ready_evt;
                    end
                join_none
                @allaxilite_read_data_finish;
                @(posedge misc_if.clock);
                -> ap_done_for_nexttrans;
                `uvm_info(this.get_full_name(), "trigger event ap_done_for_nexttrans", UVM_LOW)
                fork
                    begin
                        misc_if.ap_done_for_nexttrans = 1;
                        @(posedge misc_if.clock);
                        misc_if.ap_done_for_nexttrans = 0;
                    end
                join_none
            end

            for(int i=1; i<1; i++) begin
                @dut2tb_ap_ready;
                mem_blk_pages_meta.incr_rd_page_idx() ;
                mem_blk_pages_weights.incr_rd_page_idx() ;
            end
            forever begin
                forever begin
                    @(negedge misc_if.clock);
                    if (misc_if.dut2tb_ap_ready === 1)   break;
                end
                @(posedge misc_if.clock);
                `uvm_info(this.get_full_name(), "trigger event DUT2TB_AP_READY", UVM_LOW)
                -> dut2tb_ap_ready;
                 misc_if.tb2dut_ap_start = 0;
            end
        join
    endtask

    virtual function void write_axi_wtr_meta(axi_pkg::axi_transfer tr);
        mem_blk_pages_meta.write_elems_pipepage(tr.data,tr.byte_addr);
    endfunction

    virtual function void write_axi_rtr_meta(axi_pkg::axi_transfer tr);
    endfunction

    virtual function void write_axi_wtr_weights(axi_pkg::axi_transfer tr);
        mem_blk_pages_weights.write_elems_pipepage(tr.data,tr.byte_addr);
    endfunction

    virtual function void write_axi_rtr_weights(axi_pkg::axi_transfer tr);
    endfunction

    virtual function void write_axi_wtr_control(axi_pkg::axi_transfer tr);
        if(tr.addr == 0 && tr.len == 0 && tr.data[0][0]==1) begin //addr 0 and bit 0 are parameter
            -> write_start_finish;
            misc_if.tb2dut_ap_start = 1;
        end
    endfunction
    virtual function void write_axi_rtr_control(axi_pkg::axi_transfer tr);
            `uvm_info("receive axi read data", tr.sprint(), UVM_HIGH)
        if(tr.addr == 0 && tr.len == 0) begin
            if(tr.data[0][1]==1) begin  //bit 1 is parameter
                `uvm_info("status polling", "ap_done is polled", UVM_LOW);
                fork
                    begin
                        misc_if.dut2tb_ap_done = 1;
                        @(posedge misc_if.clock);
                        #0;
                        misc_if.dut2tb_ap_done = 0;
                        misc_if.tb2dut_ap_continue = 0;
                        -> dut2tb_ap_done;
                    end
                join_none
            end
            begin
                misc_if.dut2tb_ap_idle = tr.data[0][2];
            end
        end else begin
            mem_blk_pages_control_status.write_elems_frontpage(tr.data, tr.byte_addr);
            mem_blk_pages_control_token.write_elems_frontpage(tr.data, tr.byte_addr);
            mem_blk_pages_control_score_bits.write_elems_frontpage(tr.data, tr.byte_addr);
            mem_blk_pages_control_candidate_count.write_elems_frontpage(tr.data, tr.byte_addr);
            mem_blk_pages_control_output_crc.write_elems_frontpage(tr.data, tr.byte_addr);
            mem_blk_pages_control_preview_read_beats.write_elems_frontpage(tr.data, tr.byte_addr);
        end
    endfunction
endclass
`endif
