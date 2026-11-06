// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2021.1 (64-bit)
// Copyright 1986-2021 Xilinx, Inc. All Rights Reserved.
// ==============================================================
`timescale 1ns/1ps
module lm_head_v4_selector_control_s_axi
#(parameter
    C_S_AXI_ADDR_WIDTH = 8,
    C_S_AXI_DATA_WIDTH = 32
)(
    input  wire                          ACLK,
    input  wire                          ARESET,
    input  wire                          ACLK_EN,
    input  wire [C_S_AXI_ADDR_WIDTH-1:0] AWADDR,
    input  wire                          AWVALID,
    output wire                          AWREADY,
    input  wire [C_S_AXI_DATA_WIDTH-1:0] WDATA,
    input  wire [C_S_AXI_DATA_WIDTH/8-1:0] WSTRB,
    input  wire                          WVALID,
    output wire                          WREADY,
    output wire [1:0]                    BRESP,
    output wire                          BVALID,
    input  wire                          BREADY,
    input  wire [C_S_AXI_ADDR_WIDTH-1:0] ARADDR,
    input  wire                          ARVALID,
    output wire                          ARREADY,
    output wire [C_S_AXI_DATA_WIDTH-1:0] RDATA,
    output wire [1:0]                    RRESP,
    output wire                          RVALID,
    input  wire                          RREADY,
    output wire                          interrupt,
    output wire [63:0]                   pl_ddr,
    output wire [63:0]                   history_bitmap,
    output wire [63:0]                   arena_bytes,
    output wire [63:0]                   descriptor_offset,
    output wire [31:0]                   command,
    input  wire [31:0]                   status,
    input  wire                          status_ap_vld,
    input  wire [31:0]                   stage,
    input  wire                          stage_ap_vld,
    input  wire [31:0]                   child_status,
    input  wire                          child_status_ap_vld,
    input  wire [31:0]                   route_count,
    input  wire                          route_count_ap_vld,
    input  wire [31:0]                   candidate_count,
    input  wire                          candidate_count_ap_vld,
    input  wire [31:0]                   dense_fallback,
    input  wire                          dense_fallback_ap_vld,
    input  wire [31:0]                   selected_token_out,
    input  wire                          selected_token_out_ap_vld,
    input  wire [31:0]                   score,
    input  wire                          score_ap_vld,
    input  wire [31:0]                   output_crc,
    input  wire                          output_crc_ap_vld,
    output wire                          ap_start,
    input  wire                          ap_done,
    input  wire                          ap_ready,
    input  wire                          ap_idle
);
//------------------------Address Info-------------------
// 0x00 : Control signals
//        bit 0  - ap_start (Read/Write/COH)
//        bit 1  - ap_done (Read/COR)
//        bit 2  - ap_idle (Read)
//        bit 3  - ap_ready (Read/COR)
//        bit 7  - auto_restart (Read/Write)
//        others - reserved
// 0x04 : Global Interrupt Enable Register
//        bit 0  - Global Interrupt Enable (Read/Write)
//        others - reserved
// 0x08 : IP Interrupt Enable Register (Read/Write)
//        bit 0  - enable ap_done interrupt (Read/Write)
//        bit 1  - enable ap_ready interrupt (Read/Write)
//        others - reserved
// 0x0c : IP Interrupt Status Register (Read/TOW)
//        bit 0  - ap_done (COR/TOW)
//        bit 1  - ap_ready (COR/TOW)
//        others - reserved
// 0x10 : Data signal of pl_ddr
//        bit 31~0 - pl_ddr[31:0] (Read/Write)
// 0x14 : Data signal of pl_ddr
//        bit 31~0 - pl_ddr[63:32] (Read/Write)
// 0x18 : reserved
// 0x1c : Data signal of history_bitmap
//        bit 31~0 - history_bitmap[31:0] (Read/Write)
// 0x20 : Data signal of history_bitmap
//        bit 31~0 - history_bitmap[63:32] (Read/Write)
// 0x24 : reserved
// 0x28 : Data signal of arena_bytes
//        bit 31~0 - arena_bytes[31:0] (Read/Write)
// 0x2c : Data signal of arena_bytes
//        bit 31~0 - arena_bytes[63:32] (Read/Write)
// 0x30 : reserved
// 0x34 : Data signal of descriptor_offset
//        bit 31~0 - descriptor_offset[31:0] (Read/Write)
// 0x38 : Data signal of descriptor_offset
//        bit 31~0 - descriptor_offset[63:32] (Read/Write)
// 0x3c : reserved
// 0x40 : Data signal of command
//        bit 31~0 - command[31:0] (Read/Write)
// 0x44 : reserved
// 0x48 : Data signal of status
//        bit 31~0 - status[31:0] (Read)
// 0x4c : Control signal of status
//        bit 0  - status_ap_vld (Read/COR)
//        others - reserved
// 0x58 : Data signal of stage
//        bit 31~0 - stage[31:0] (Read)
// 0x5c : Control signal of stage
//        bit 0  - stage_ap_vld (Read/COR)
//        others - reserved
// 0x68 : Data signal of child_status
//        bit 31~0 - child_status[31:0] (Read)
// 0x6c : Control signal of child_status
//        bit 0  - child_status_ap_vld (Read/COR)
//        others - reserved
// 0x78 : Data signal of route_count
//        bit 31~0 - route_count[31:0] (Read)
// 0x7c : Control signal of route_count
//        bit 0  - route_count_ap_vld (Read/COR)
//        others - reserved
// 0x88 : Data signal of candidate_count
//        bit 31~0 - candidate_count[31:0] (Read)
// 0x8c : Control signal of candidate_count
//        bit 0  - candidate_count_ap_vld (Read/COR)
//        others - reserved
// 0x98 : Data signal of dense_fallback
//        bit 31~0 - dense_fallback[31:0] (Read)
// 0x9c : Control signal of dense_fallback
//        bit 0  - dense_fallback_ap_vld (Read/COR)
//        others - reserved
// 0xa8 : Data signal of selected_token_out
//        bit 31~0 - selected_token_out[31:0] (Read)
// 0xac : Control signal of selected_token_out
//        bit 0  - selected_token_out_ap_vld (Read/COR)
//        others - reserved
// 0xb8 : Data signal of score
//        bit 31~0 - score[31:0] (Read)
// 0xbc : Control signal of score
//        bit 0  - score_ap_vld (Read/COR)
//        others - reserved
// 0xc8 : Data signal of output_crc
//        bit 31~0 - output_crc[31:0] (Read)
// 0xcc : Control signal of output_crc
//        bit 0  - output_crc_ap_vld (Read/COR)
//        others - reserved
// (SC = Self Clear, COR = Clear on Read, TOW = Toggle on Write, COH = Clear on Handshake)

//------------------------Parameter----------------------
localparam
    ADDR_AP_CTRL                   = 8'h00,
    ADDR_GIE                       = 8'h04,
    ADDR_IER                       = 8'h08,
    ADDR_ISR                       = 8'h0c,
    ADDR_PL_DDR_DATA_0             = 8'h10,
    ADDR_PL_DDR_DATA_1             = 8'h14,
    ADDR_PL_DDR_CTRL               = 8'h18,
    ADDR_HISTORY_BITMAP_DATA_0     = 8'h1c,
    ADDR_HISTORY_BITMAP_DATA_1     = 8'h20,
    ADDR_HISTORY_BITMAP_CTRL       = 8'h24,
    ADDR_ARENA_BYTES_DATA_0        = 8'h28,
    ADDR_ARENA_BYTES_DATA_1        = 8'h2c,
    ADDR_ARENA_BYTES_CTRL          = 8'h30,
    ADDR_DESCRIPTOR_OFFSET_DATA_0  = 8'h34,
    ADDR_DESCRIPTOR_OFFSET_DATA_1  = 8'h38,
    ADDR_DESCRIPTOR_OFFSET_CTRL    = 8'h3c,
    ADDR_COMMAND_DATA_0            = 8'h40,
    ADDR_COMMAND_CTRL              = 8'h44,
    ADDR_STATUS_DATA_0             = 8'h48,
    ADDR_STATUS_CTRL               = 8'h4c,
    ADDR_STAGE_DATA_0              = 8'h58,
    ADDR_STAGE_CTRL                = 8'h5c,
    ADDR_CHILD_STATUS_DATA_0       = 8'h68,
    ADDR_CHILD_STATUS_CTRL         = 8'h6c,
    ADDR_ROUTE_COUNT_DATA_0        = 8'h78,
    ADDR_ROUTE_COUNT_CTRL          = 8'h7c,
    ADDR_CANDIDATE_COUNT_DATA_0    = 8'h88,
    ADDR_CANDIDATE_COUNT_CTRL      = 8'h8c,
    ADDR_DENSE_FALLBACK_DATA_0     = 8'h98,
    ADDR_DENSE_FALLBACK_CTRL       = 8'h9c,
    ADDR_SELECTED_TOKEN_OUT_DATA_0 = 8'ha8,
    ADDR_SELECTED_TOKEN_OUT_CTRL   = 8'hac,
    ADDR_SCORE_DATA_0              = 8'hb8,
    ADDR_SCORE_CTRL                = 8'hbc,
    ADDR_OUTPUT_CRC_DATA_0         = 8'hc8,
    ADDR_OUTPUT_CRC_CTRL           = 8'hcc,
    WRIDLE                         = 2'd0,
    WRDATA                         = 2'd1,
    WRRESP                         = 2'd2,
    WRRESET                        = 2'd3,
    RDIDLE                         = 2'd0,
    RDDATA                         = 2'd1,
    RDRESET                        = 2'd2,
    ADDR_BITS                = 8;

//------------------------Local signal-------------------
    reg  [1:0]                    wstate = WRRESET;
    reg  [1:0]                    wnext;
    reg  [ADDR_BITS-1:0]          waddr;
    wire [C_S_AXI_DATA_WIDTH-1:0] wmask;
    wire                          aw_hs;
    wire                          w_hs;
    reg  [1:0]                    rstate = RDRESET;
    reg  [1:0]                    rnext;
    reg  [C_S_AXI_DATA_WIDTH-1:0] rdata;
    wire                          ar_hs;
    wire [ADDR_BITS-1:0]          raddr;
    // internal registers
    reg                           int_ap_idle;
    reg                           int_ap_ready = 1'b0;
    wire                          task_ap_ready;
    reg                           int_ap_done = 1'b0;
    wire                          task_ap_done;
    reg                           int_task_ap_done = 1'b0;
    reg                           int_ap_start = 1'b0;
    reg                           int_auto_restart = 1'b0;
    reg                           auto_restart_status = 1'b0;
    wire                          auto_restart_done;
    reg                           int_gie = 1'b0;
    reg  [1:0]                    int_ier = 2'b0;
    reg  [1:0]                    int_isr = 2'b0;
    reg  [63:0]                   int_pl_ddr = 'b0;
    reg  [63:0]                   int_history_bitmap = 'b0;
    reg  [63:0]                   int_arena_bytes = 'b0;
    reg  [63:0]                   int_descriptor_offset = 'b0;
    reg  [31:0]                   int_command = 'b0;
    reg                           int_status_ap_vld;
    reg  [31:0]                   int_status = 'b0;
    reg                           int_stage_ap_vld;
    reg  [31:0]                   int_stage = 'b0;
    reg                           int_child_status_ap_vld;
    reg  [31:0]                   int_child_status = 'b0;
    reg                           int_route_count_ap_vld;
    reg  [31:0]                   int_route_count = 'b0;
    reg                           int_candidate_count_ap_vld;
    reg  [31:0]                   int_candidate_count = 'b0;
    reg                           int_dense_fallback_ap_vld;
    reg  [31:0]                   int_dense_fallback = 'b0;
    reg                           int_selected_token_out_ap_vld;
    reg  [31:0]                   int_selected_token_out = 'b0;
    reg                           int_score_ap_vld;
    reg  [31:0]                   int_score = 'b0;
    reg                           int_output_crc_ap_vld;
    reg  [31:0]                   int_output_crc = 'b0;

//------------------------Instantiation------------------


//------------------------AXI write fsm------------------
assign AWREADY = (wstate == WRIDLE);
assign WREADY  = (wstate == WRDATA);
assign BRESP   = 2'b00;  // OKAY
assign BVALID  = (wstate == WRRESP);
assign wmask   = { {8{WSTRB[3]}}, {8{WSTRB[2]}}, {8{WSTRB[1]}}, {8{WSTRB[0]}} };
assign aw_hs   = AWVALID & AWREADY;
assign w_hs    = WVALID & WREADY;

// wstate
always @(posedge ACLK) begin
    if (ARESET)
        wstate <= WRRESET;
    else if (ACLK_EN)
        wstate <= wnext;
end

// wnext
always @(*) begin
    case (wstate)
        WRIDLE:
            if (AWVALID)
                wnext = WRDATA;
            else
                wnext = WRIDLE;
        WRDATA:
            if (WVALID)
                wnext = WRRESP;
            else
                wnext = WRDATA;
        WRRESP:
            if (BREADY)
                wnext = WRIDLE;
            else
                wnext = WRRESP;
        default:
            wnext = WRIDLE;
    endcase
end

// waddr
always @(posedge ACLK) begin
    if (ACLK_EN) begin
        if (aw_hs)
            waddr <= AWADDR[ADDR_BITS-1:0];
    end
end

//------------------------AXI read fsm-------------------
assign ARREADY = (rstate == RDIDLE);
assign RDATA   = rdata;
assign RRESP   = 2'b00;  // OKAY
assign RVALID  = (rstate == RDDATA);
assign ar_hs   = ARVALID & ARREADY;
assign raddr   = ARADDR[ADDR_BITS-1:0];

// rstate
always @(posedge ACLK) begin
    if (ARESET)
        rstate <= RDRESET;
    else if (ACLK_EN)
        rstate <= rnext;
end

// rnext
always @(*) begin
    case (rstate)
        RDIDLE:
            if (ARVALID)
                rnext = RDDATA;
            else
                rnext = RDIDLE;
        RDDATA:
            if (RREADY & RVALID)
                rnext = RDIDLE;
            else
                rnext = RDDATA;
        default:
            rnext = RDIDLE;
    endcase
end

// rdata
always @(posedge ACLK) begin
    if (ACLK_EN) begin
        if (ar_hs) begin
            rdata <= 'b0;
            case (raddr)
                ADDR_AP_CTRL: begin
                    rdata[0] <= int_ap_start;
                    rdata[1] <= int_task_ap_done;
                    rdata[2] <= int_ap_idle;
                    rdata[3] <= int_ap_ready;
                    rdata[7] <= int_auto_restart;
                end
                ADDR_GIE: begin
                    rdata <= int_gie;
                end
                ADDR_IER: begin
                    rdata <= int_ier;
                end
                ADDR_ISR: begin
                    rdata <= int_isr;
                end
                ADDR_PL_DDR_DATA_0: begin
                    rdata <= int_pl_ddr[31:0];
                end
                ADDR_PL_DDR_DATA_1: begin
                    rdata <= int_pl_ddr[63:32];
                end
                ADDR_HISTORY_BITMAP_DATA_0: begin
                    rdata <= int_history_bitmap[31:0];
                end
                ADDR_HISTORY_BITMAP_DATA_1: begin
                    rdata <= int_history_bitmap[63:32];
                end
                ADDR_ARENA_BYTES_DATA_0: begin
                    rdata <= int_arena_bytes[31:0];
                end
                ADDR_ARENA_BYTES_DATA_1: begin
                    rdata <= int_arena_bytes[63:32];
                end
                ADDR_DESCRIPTOR_OFFSET_DATA_0: begin
                    rdata <= int_descriptor_offset[31:0];
                end
                ADDR_DESCRIPTOR_OFFSET_DATA_1: begin
                    rdata <= int_descriptor_offset[63:32];
                end
                ADDR_COMMAND_DATA_0: begin
                    rdata <= int_command[31:0];
                end
                ADDR_STATUS_DATA_0: begin
                    rdata <= int_status[31:0];
                end
                ADDR_STATUS_CTRL: begin
                    rdata[0] <= int_status_ap_vld;
                end
                ADDR_STAGE_DATA_0: begin
                    rdata <= int_stage[31:0];
                end
                ADDR_STAGE_CTRL: begin
                    rdata[0] <= int_stage_ap_vld;
                end
                ADDR_CHILD_STATUS_DATA_0: begin
                    rdata <= int_child_status[31:0];
                end
                ADDR_CHILD_STATUS_CTRL: begin
                    rdata[0] <= int_child_status_ap_vld;
                end
                ADDR_ROUTE_COUNT_DATA_0: begin
                    rdata <= int_route_count[31:0];
                end
                ADDR_ROUTE_COUNT_CTRL: begin
                    rdata[0] <= int_route_count_ap_vld;
                end
                ADDR_CANDIDATE_COUNT_DATA_0: begin
                    rdata <= int_candidate_count[31:0];
                end
                ADDR_CANDIDATE_COUNT_CTRL: begin
                    rdata[0] <= int_candidate_count_ap_vld;
                end
                ADDR_DENSE_FALLBACK_DATA_0: begin
                    rdata <= int_dense_fallback[31:0];
                end
                ADDR_DENSE_FALLBACK_CTRL: begin
                    rdata[0] <= int_dense_fallback_ap_vld;
                end
                ADDR_SELECTED_TOKEN_OUT_DATA_0: begin
                    rdata <= int_selected_token_out[31:0];
                end
                ADDR_SELECTED_TOKEN_OUT_CTRL: begin
                    rdata[0] <= int_selected_token_out_ap_vld;
                end
                ADDR_SCORE_DATA_0: begin
                    rdata <= int_score[31:0];
                end
                ADDR_SCORE_CTRL: begin
                    rdata[0] <= int_score_ap_vld;
                end
                ADDR_OUTPUT_CRC_DATA_0: begin
                    rdata <= int_output_crc[31:0];
                end
                ADDR_OUTPUT_CRC_CTRL: begin
                    rdata[0] <= int_output_crc_ap_vld;
                end
            endcase
        end
    end
end


//------------------------Register logic-----------------
assign interrupt         = int_gie & (|int_isr);
assign ap_start          = int_ap_start;
assign task_ap_done      = (ap_done && !auto_restart_status) || auto_restart_done;
assign task_ap_ready     = ap_ready && !int_auto_restart;
assign auto_restart_done = auto_restart_status && (ap_idle && !int_ap_idle);
assign pl_ddr            = int_pl_ddr;
assign history_bitmap    = int_history_bitmap;
assign arena_bytes       = int_arena_bytes;
assign descriptor_offset = int_descriptor_offset;
assign command           = int_command;
// int_ap_start
always @(posedge ACLK) begin
    if (ARESET)
        int_ap_start <= 1'b0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_AP_CTRL && WSTRB[0] && WDATA[0])
            int_ap_start <= 1'b1;
        else if (ap_ready)
            int_ap_start <= int_auto_restart; // clear on handshake/auto restart
    end
end

// int_ap_done
always @(posedge ACLK) begin
    if (ARESET)
        int_ap_done <= 1'b0;
    else if (ACLK_EN) begin
            int_ap_done <= ap_done;
    end
end

// int_task_ap_done
always @(posedge ACLK) begin
    if (ARESET)
        int_task_ap_done <= 1'b0;
    else if (ACLK_EN) begin
        if (task_ap_done)
            int_task_ap_done <= 1'b1;
        else if (ar_hs && raddr == ADDR_AP_CTRL)
            int_task_ap_done <= 1'b0; // clear on read
    end
end

// int_ap_idle
always @(posedge ACLK) begin
    if (ARESET)
        int_ap_idle <= 1'b0;
    else if (ACLK_EN) begin
            int_ap_idle <= ap_idle;
    end
end

// int_ap_ready
always @(posedge ACLK) begin
    if (ARESET)
        int_ap_ready <= 1'b0;
    else if (ACLK_EN) begin
        if (task_ap_ready)
            int_ap_ready <= 1'b1;
        else if (ar_hs && raddr == ADDR_AP_CTRL)
            int_ap_ready <= 1'b0;
    end
end

// int_auto_restart
always @(posedge ACLK) begin
    if (ARESET)
        int_auto_restart <= 1'b0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_AP_CTRL && WSTRB[0])
            int_auto_restart <=  WDATA[7];
    end
end

// auto_restart_status
always @(posedge ACLK) begin
    if (ARESET)
        auto_restart_status <= 1'b0;
    else if (ACLK_EN) begin
        if (int_auto_restart)
            auto_restart_status <= 1'b1;
        else if (ap_idle)
            auto_restart_status <= 1'b0;
    end
end

// int_gie
always @(posedge ACLK) begin
    if (ARESET)
        int_gie <= 1'b0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_GIE && WSTRB[0])
            int_gie <= WDATA[0];
    end
end

// int_ier
always @(posedge ACLK) begin
    if (ARESET)
        int_ier <= 1'b0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_IER && WSTRB[0])
            int_ier <= WDATA[1:0];
    end
end

// int_isr[0]
always @(posedge ACLK) begin
    if (ARESET)
        int_isr[0] <= 1'b0;
    else if (ACLK_EN) begin
        if (int_ier[0] & ap_done)
            int_isr[0] <= 1'b1;
        else if (w_hs && waddr == ADDR_ISR && WSTRB[0])
            int_isr[0] <= int_isr[0] ^ WDATA[0]; // toggle on write
    end
end

// int_isr[1]
always @(posedge ACLK) begin
    if (ARESET)
        int_isr[1] <= 1'b0;
    else if (ACLK_EN) begin
        if (int_ier[1] & ap_ready)
            int_isr[1] <= 1'b1;
        else if (w_hs && waddr == ADDR_ISR && WSTRB[0])
            int_isr[1] <= int_isr[1] ^ WDATA[1]; // toggle on write
    end
end

// int_pl_ddr[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_pl_ddr[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_PL_DDR_DATA_0)
            int_pl_ddr[31:0] <= (WDATA[31:0] & wmask) | (int_pl_ddr[31:0] & ~wmask);
    end
end

// int_pl_ddr[63:32]
always @(posedge ACLK) begin
    if (ARESET)
        int_pl_ddr[63:32] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_PL_DDR_DATA_1)
            int_pl_ddr[63:32] <= (WDATA[31:0] & wmask) | (int_pl_ddr[63:32] & ~wmask);
    end
end

// int_history_bitmap[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_history_bitmap[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_HISTORY_BITMAP_DATA_0)
            int_history_bitmap[31:0] <= (WDATA[31:0] & wmask) | (int_history_bitmap[31:0] & ~wmask);
    end
end

// int_history_bitmap[63:32]
always @(posedge ACLK) begin
    if (ARESET)
        int_history_bitmap[63:32] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_HISTORY_BITMAP_DATA_1)
            int_history_bitmap[63:32] <= (WDATA[31:0] & wmask) | (int_history_bitmap[63:32] & ~wmask);
    end
end

// int_arena_bytes[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_arena_bytes[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_ARENA_BYTES_DATA_0)
            int_arena_bytes[31:0] <= (WDATA[31:0] & wmask) | (int_arena_bytes[31:0] & ~wmask);
    end
end

// int_arena_bytes[63:32]
always @(posedge ACLK) begin
    if (ARESET)
        int_arena_bytes[63:32] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_ARENA_BYTES_DATA_1)
            int_arena_bytes[63:32] <= (WDATA[31:0] & wmask) | (int_arena_bytes[63:32] & ~wmask);
    end
end

// int_descriptor_offset[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_descriptor_offset[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_DESCRIPTOR_OFFSET_DATA_0)
            int_descriptor_offset[31:0] <= (WDATA[31:0] & wmask) | (int_descriptor_offset[31:0] & ~wmask);
    end
end

// int_descriptor_offset[63:32]
always @(posedge ACLK) begin
    if (ARESET)
        int_descriptor_offset[63:32] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_DESCRIPTOR_OFFSET_DATA_1)
            int_descriptor_offset[63:32] <= (WDATA[31:0] & wmask) | (int_descriptor_offset[63:32] & ~wmask);
    end
end

// int_command[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_command[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_COMMAND_DATA_0)
            int_command[31:0] <= (WDATA[31:0] & wmask) | (int_command[31:0] & ~wmask);
    end
end

// int_status
always @(posedge ACLK) begin
    if (ARESET)
        int_status <= 0;
    else if (ACLK_EN) begin
        if (status_ap_vld)
            int_status <= status;
    end
end

// int_status_ap_vld
always @(posedge ACLK) begin
    if (ARESET)
        int_status_ap_vld <= 1'b0;
    else if (ACLK_EN) begin
        if (status_ap_vld)
            int_status_ap_vld <= 1'b1;
        else if (ar_hs && raddr == ADDR_STATUS_CTRL)
            int_status_ap_vld <= 1'b0; // clear on read
    end
end

// int_stage
always @(posedge ACLK) begin
    if (ARESET)
        int_stage <= 0;
    else if (ACLK_EN) begin
        if (stage_ap_vld)
            int_stage <= stage;
    end
end

// int_stage_ap_vld
always @(posedge ACLK) begin
    if (ARESET)
        int_stage_ap_vld <= 1'b0;
    else if (ACLK_EN) begin
        if (stage_ap_vld)
            int_stage_ap_vld <= 1'b1;
        else if (ar_hs && raddr == ADDR_STAGE_CTRL)
            int_stage_ap_vld <= 1'b0; // clear on read
    end
end

// int_child_status
always @(posedge ACLK) begin
    if (ARESET)
        int_child_status <= 0;
    else if (ACLK_EN) begin
        if (child_status_ap_vld)
            int_child_status <= child_status;
    end
end

// int_child_status_ap_vld
always @(posedge ACLK) begin
    if (ARESET)
        int_child_status_ap_vld <= 1'b0;
    else if (ACLK_EN) begin
        if (child_status_ap_vld)
            int_child_status_ap_vld <= 1'b1;
        else if (ar_hs && raddr == ADDR_CHILD_STATUS_CTRL)
            int_child_status_ap_vld <= 1'b0; // clear on read
    end
end

// int_route_count
always @(posedge ACLK) begin
    if (ARESET)
        int_route_count <= 0;
    else if (ACLK_EN) begin
        if (route_count_ap_vld)
            int_route_count <= route_count;
    end
end

// int_route_count_ap_vld
always @(posedge ACLK) begin
    if (ARESET)
        int_route_count_ap_vld <= 1'b0;
    else if (ACLK_EN) begin
        if (route_count_ap_vld)
            int_route_count_ap_vld <= 1'b1;
        else if (ar_hs && raddr == ADDR_ROUTE_COUNT_CTRL)
            int_route_count_ap_vld <= 1'b0; // clear on read
    end
end

// int_candidate_count
always @(posedge ACLK) begin
    if (ARESET)
        int_candidate_count <= 0;
    else if (ACLK_EN) begin
        if (candidate_count_ap_vld)
            int_candidate_count <= candidate_count;
    end
end

// int_candidate_count_ap_vld
always @(posedge ACLK) begin
    if (ARESET)
        int_candidate_count_ap_vld <= 1'b0;
    else if (ACLK_EN) begin
        if (candidate_count_ap_vld)
            int_candidate_count_ap_vld <= 1'b1;
        else if (ar_hs && raddr == ADDR_CANDIDATE_COUNT_CTRL)
            int_candidate_count_ap_vld <= 1'b0; // clear on read
    end
end

// int_dense_fallback
always @(posedge ACLK) begin
    if (ARESET)
        int_dense_fallback <= 0;
    else if (ACLK_EN) begin
        if (dense_fallback_ap_vld)
            int_dense_fallback <= dense_fallback;
    end
end

// int_dense_fallback_ap_vld
always @(posedge ACLK) begin
    if (ARESET)
        int_dense_fallback_ap_vld <= 1'b0;
    else if (ACLK_EN) begin
        if (dense_fallback_ap_vld)
            int_dense_fallback_ap_vld <= 1'b1;
        else if (ar_hs && raddr == ADDR_DENSE_FALLBACK_CTRL)
            int_dense_fallback_ap_vld <= 1'b0; // clear on read
    end
end

// int_selected_token_out
always @(posedge ACLK) begin
    if (ARESET)
        int_selected_token_out <= 0;
    else if (ACLK_EN) begin
        if (selected_token_out_ap_vld)
            int_selected_token_out <= selected_token_out;
    end
end

// int_selected_token_out_ap_vld
always @(posedge ACLK) begin
    if (ARESET)
        int_selected_token_out_ap_vld <= 1'b0;
    else if (ACLK_EN) begin
        if (selected_token_out_ap_vld)
            int_selected_token_out_ap_vld <= 1'b1;
        else if (ar_hs && raddr == ADDR_SELECTED_TOKEN_OUT_CTRL)
            int_selected_token_out_ap_vld <= 1'b0; // clear on read
    end
end

// int_score
always @(posedge ACLK) begin
    if (ARESET)
        int_score <= 0;
    else if (ACLK_EN) begin
        if (score_ap_vld)
            int_score <= score;
    end
end

// int_score_ap_vld
always @(posedge ACLK) begin
    if (ARESET)
        int_score_ap_vld <= 1'b0;
    else if (ACLK_EN) begin
        if (score_ap_vld)
            int_score_ap_vld <= 1'b1;
        else if (ar_hs && raddr == ADDR_SCORE_CTRL)
            int_score_ap_vld <= 1'b0; // clear on read
    end
end

// int_output_crc
always @(posedge ACLK) begin
    if (ARESET)
        int_output_crc <= 0;
    else if (ACLK_EN) begin
        if (output_crc_ap_vld)
            int_output_crc <= output_crc;
    end
end

// int_output_crc_ap_vld
always @(posedge ACLK) begin
    if (ARESET)
        int_output_crc_ap_vld <= 1'b0;
    else if (ACLK_EN) begin
        if (output_crc_ap_vld)
            int_output_crc_ap_vld <= 1'b1;
        else if (ar_hs && raddr == ADDR_OUTPUT_CRC_CTRL)
            int_output_crc_ap_vld <= 1'b0; // clear on read
    end
end


//------------------------Memory logic-------------------

endmodule
