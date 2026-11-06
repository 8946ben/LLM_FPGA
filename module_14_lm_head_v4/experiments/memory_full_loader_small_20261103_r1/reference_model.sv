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
        mem_blk_pages_weights.whole_page_size=8388864;
        mem_blk_pages_weights.maxi_bundlevar_fpath["tiled_weight"]=`TV_IN_OFFSET_tiled_weight;
        mem_blk_pages_weights.maxi_bundlevar_fpath["canonical_weight"]=`TV_IN_OFFSET_canonical_weight;
        lmh_memory_probe_pkg::sample("before_weights_load",8388608);
        mem_blk_pages_weights.tvinload_pagechk_atinit(fpath, 524288*((128+7)/8), 0);
        lmh_memory_probe_pkg::sample("after_weights_load",8388608);
begin : small_full_context
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
