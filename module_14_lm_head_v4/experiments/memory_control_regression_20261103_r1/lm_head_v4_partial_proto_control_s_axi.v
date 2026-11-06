// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2022.2 (64-bit)
// Tool Version Limit: 2019.12
// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// ==============================================================
`timescale 1ns/1ps
module lm_head_v4_partial_proto_control_s_axi
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
    output wire [63:0]                   meta_offset,
    output wire [63:0]                   tiled_weight,
    output wire [63:0]                   canonical_weight,
    output wire [63:0]                   workspace,
    output wire [31:0]                   capacity_beats,
    output wire [31:0]                   debug,
    input  wire [31:0]                   status,
    input  wire                          status_ap_vld,
    input  wire [31:0]                   token,
    input  wire                          token_ap_vld,
    input  wire [31:0]                   score_bits,
    input  wire                          score_bits_ap_vld,
    input  wire [31:0]                   candidate_count,
    input  wire                          candidate_count_ap_vld,
    input  wire [31:0]                   output_crc,
    input  wire                          output_crc_ap_vld,
    input  wire [63:0]                   preview_read_beats,
    input  wire                          preview_read_beats_ap_vld,
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
//        bit 9  - interrupt (Read)
//        others - reserved
// 0x04 : Global Interrupt Enable Register
//        bit 0  - Global Interrupt Enable (Read/Write)
//        others - reserved
// 0x08 : IP Interrupt Enable Register (Read/Write)
//        bit 0 - enable ap_done interrupt (Read/Write)
//        bit 1 - enable ap_ready interrupt (Read/Write)
//        others - reserved
// 0x0c : IP Interrupt Status Register (Read/TOW)
//        bit 0 - ap_done (Read/TOW)
//        bit 1 - ap_ready (Read/TOW)
//        others - reserved
// 0x10 : Data signal of meta_offset
//        bit 31~0 - meta_offset[31:0] (Read/Write)
// 0x14 : Data signal of meta_offset
//        bit 31~0 - meta_offset[63:32] (Read/Write)
// 0x18 : reserved
// 0x1c : Data signal of tiled_weight
//        bit 31~0 - tiled_weight[31:0] (Read/Write)
// 0x20 : Data signal of tiled_weight
//        bit 31~0 - tiled_weight[63:32] (Read/Write)
// 0x24 : reserved
// 0x28 : Data signal of canonical_weight
//        bit 31~0 - canonical_weight[31:0] (Read/Write)
// 0x2c : Data signal of canonical_weight
//        bit 31~0 - canonical_weight[63:32] (Read/Write)
// 0x30 : reserved
// 0x34 : Data signal of workspace
//        bit 31~0 - workspace[31:0] (Read/Write)
// 0x38 : Data signal of workspace
//        bit 31~0 - workspace[63:32] (Read/Write)
// 0x3c : reserved
// 0x40 : Data signal of capacity_beats
//        bit 31~0 - capacity_beats[31:0] (Read/Write)
// 0x44 : reserved
// 0x48 : Data signal of debug
//        bit 31~0 - debug[31:0] (Read/Write)
// 0x4c : reserved
// 0x50 : Data signal of status
//        bit 31~0 - status[31:0] (Read)
// 0x54 : Control signal of status
//        bit 0  - status_ap_vld (Read/COR)
//        others - reserved
// 0x60 : Data signal of token
//        bit 31~0 - token[31:0] (Read)
// 0x64 : Control signal of token
//        bit 0  - token_ap_vld (Read/COR)
//        others - reserved
// 0x70 : Data signal of score_bits
//        bit 31~0 - score_bits[31:0] (Read)
// 0x74 : Control signal of score_bits
//        bit 0  - score_bits_ap_vld (Read/COR)
//        others - reserved
// 0x80 : Data signal of candidate_count
//        bit 31~0 - candidate_count[31:0] (Read)
// 0x84 : Control signal of candidate_count
//        bit 0  - candidate_count_ap_vld (Read/COR)
//        others - reserved
// 0x90 : Data signal of output_crc
//        bit 31~0 - output_crc[31:0] (Read)
// 0x94 : Control signal of output_crc
//        bit 0  - output_crc_ap_vld (Read/COR)
//        others - reserved
// 0xa0 : Data signal of preview_read_beats
//        bit 31~0 - preview_read_beats[31:0] (Read)
// 0xa4 : Data signal of preview_read_beats
//        bit 31~0 - preview_read_beats[63:32] (Read)
// 0xa8 : Control signal of preview_read_beats
//        bit 0  - preview_read_beats_ap_vld (Read/COR)
//        others - reserved
// (SC = Self Clear, COR = Clear on Read, TOW = Toggle on Write, COH = Clear on Handshake)

//------------------------Parameter----------------------
localparam
    ADDR_AP_CTRL                   = 8'h00,
    ADDR_GIE                       = 8'h04,
    ADDR_IER                       = 8'h08,
    ADDR_ISR                       = 8'h0c,
    ADDR_META_OFFSET_DATA_0        = 8'h10,
    ADDR_META_OFFSET_DATA_1        = 8'h14,
    ADDR_META_OFFSET_CTRL          = 8'h18,
    ADDR_TILED_WEIGHT_DATA_0       = 8'h1c,
    ADDR_TILED_WEIGHT_DATA_1       = 8'h20,
    ADDR_TILED_WEIGHT_CTRL         = 8'h24,
    ADDR_CANONICAL_WEIGHT_DATA_0   = 8'h28,
    ADDR_CANONICAL_WEIGHT_DATA_1   = 8'h2c,
    ADDR_CANONICAL_WEIGHT_CTRL     = 8'h30,
    ADDR_WORKSPACE_DATA_0          = 8'h34,
    ADDR_WORKSPACE_DATA_1          = 8'h38,
    ADDR_WORKSPACE_CTRL            = 8'h3c,
    ADDR_CAPACITY_BEATS_DATA_0     = 8'h40,
    ADDR_CAPACITY_BEATS_CTRL       = 8'h44,
    ADDR_DEBUG_DATA_0              = 8'h48,
    ADDR_DEBUG_CTRL                = 8'h4c,
    ADDR_STATUS_DATA_0             = 8'h50,
    ADDR_STATUS_CTRL               = 8'h54,
    ADDR_TOKEN_DATA_0              = 8'h60,
    ADDR_TOKEN_CTRL                = 8'h64,
    ADDR_SCORE_BITS_DATA_0         = 8'h70,
    ADDR_SCORE_BITS_CTRL           = 8'h74,
    ADDR_CANDIDATE_COUNT_DATA_0    = 8'h80,
    ADDR_CANDIDATE_COUNT_CTRL      = 8'h84,
    ADDR_OUTPUT_CRC_DATA_0         = 8'h90,
    ADDR_OUTPUT_CRC_CTRL           = 8'h94,
    ADDR_PREVIEW_READ_BEATS_DATA_0 = 8'ha0,
    ADDR_PREVIEW_READ_BEATS_DATA_1 = 8'ha4,
    ADDR_PREVIEW_READ_BEATS_CTRL   = 8'ha8,
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
    reg                           int_interrupt = 1'b0;
    reg                           int_auto_restart = 1'b0;
    reg                           auto_restart_status = 1'b0;
    wire                          auto_restart_done;
    reg                           int_gie = 1'b0;
    reg  [1:0]                    int_ier = 2'b0;
    reg  [1:0]                    int_isr = 2'b0;
    reg  [63:0]                   int_meta_offset = 'b0;
    reg  [63:0]                   int_tiled_weight = 'b0;
    reg  [63:0]                   int_canonical_weight = 'b0;
    reg  [63:0]                   int_workspace = 'b0;
    reg  [31:0]                   int_capacity_beats = 'b0;
    reg  [31:0]                   int_debug = 'b0;
    reg                           int_status_ap_vld;
    reg  [31:0]                   int_status = 'b0;
    reg                           int_token_ap_vld;
    reg  [31:0]                   int_token = 'b0;
    reg                           int_score_bits_ap_vld;
    reg  [31:0]                   int_score_bits = 'b0;
    reg                           int_candidate_count_ap_vld;
    reg  [31:0]                   int_candidate_count = 'b0;
    reg                           int_output_crc_ap_vld;
    reg  [31:0]                   int_output_crc = 'b0;
    reg                           int_preview_read_beats_ap_vld;
    reg  [63:0]                   int_preview_read_beats = 'b0;

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
                    rdata[9] <= int_interrupt;
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
                ADDR_META_OFFSET_DATA_0: begin
                    rdata <= int_meta_offset[31:0];
                end
                ADDR_META_OFFSET_DATA_1: begin
                    rdata <= int_meta_offset[63:32];
                end
                ADDR_TILED_WEIGHT_DATA_0: begin
                    rdata <= int_tiled_weight[31:0];
                end
                ADDR_TILED_WEIGHT_DATA_1: begin
                    rdata <= int_tiled_weight[63:32];
                end
                ADDR_CANONICAL_WEIGHT_DATA_0: begin
                    rdata <= int_canonical_weight[31:0];
                end
                ADDR_CANONICAL_WEIGHT_DATA_1: begin
                    rdata <= int_canonical_weight[63:32];
                end
                ADDR_WORKSPACE_DATA_0: begin
                    rdata <= int_workspace[31:0];
                end
                ADDR_WORKSPACE_DATA_1: begin
                    rdata <= int_workspace[63:32];
                end
                ADDR_CAPACITY_BEATS_DATA_0: begin
                    rdata <= int_capacity_beats[31:0];
                end
                ADDR_DEBUG_DATA_0: begin
                    rdata <= int_debug[31:0];
                end
                ADDR_STATUS_DATA_0: begin
                    rdata <= int_status[31:0];
                end
                ADDR_STATUS_CTRL: begin
                    rdata[0] <= int_status_ap_vld;
                end
                ADDR_TOKEN_DATA_0: begin
                    rdata <= int_token[31:0];
                end
                ADDR_TOKEN_CTRL: begin
                    rdata[0] <= int_token_ap_vld;
                end
                ADDR_SCORE_BITS_DATA_0: begin
                    rdata <= int_score_bits[31:0];
                end
                ADDR_SCORE_BITS_CTRL: begin
                    rdata[0] <= int_score_bits_ap_vld;
                end
                ADDR_CANDIDATE_COUNT_DATA_0: begin
                    rdata <= int_candidate_count[31:0];
                end
                ADDR_CANDIDATE_COUNT_CTRL: begin
                    rdata[0] <= int_candidate_count_ap_vld;
                end
                ADDR_OUTPUT_CRC_DATA_0: begin
                    rdata <= int_output_crc[31:0];
                end
                ADDR_OUTPUT_CRC_CTRL: begin
                    rdata[0] <= int_output_crc_ap_vld;
                end
                ADDR_PREVIEW_READ_BEATS_DATA_0: begin
                    rdata <= int_preview_read_beats[31:0];
                end
                ADDR_PREVIEW_READ_BEATS_DATA_1: begin
                    rdata <= int_preview_read_beats[63:32];
                end
                ADDR_PREVIEW_READ_BEATS_CTRL: begin
                    rdata[0] <= int_preview_read_beats_ap_vld;
                end
            endcase
        end
    end
end


//------------------------Register logic-----------------
assign interrupt         = int_interrupt;
assign ap_start          = int_ap_start;
assign task_ap_done      = (ap_done && !auto_restart_status) || auto_restart_done;
assign task_ap_ready     = ap_ready && !int_auto_restart;
assign auto_restart_done = auto_restart_status && (ap_idle && !int_ap_idle);
assign meta_offset       = int_meta_offset;
assign tiled_weight      = int_tiled_weight;
assign canonical_weight  = int_canonical_weight;
assign workspace         = int_workspace;
assign capacity_beats    = int_capacity_beats;
assign debug             = int_debug;
// int_interrupt
always @(posedge ACLK) begin
    if (ARESET)
        int_interrupt <= 1'b0;
    else if (ACLK_EN) begin
        if (int_gie && (|int_isr))
            int_interrupt <= 1'b1;
        else
            int_interrupt <= 1'b0;
    end
end

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

// int_meta_offset[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_meta_offset[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_META_OFFSET_DATA_0)
            int_meta_offset[31:0] <= (WDATA[31:0] & wmask) | (int_meta_offset[31:0] & ~wmask);
    end
end

// int_meta_offset[63:32]
always @(posedge ACLK) begin
    if (ARESET)
        int_meta_offset[63:32] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_META_OFFSET_DATA_1)
            int_meta_offset[63:32] <= (WDATA[31:0] & wmask) | (int_meta_offset[63:32] & ~wmask);
    end
end

// int_tiled_weight[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_tiled_weight[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_TILED_WEIGHT_DATA_0)
            int_tiled_weight[31:0] <= (WDATA[31:0] & wmask) | (int_tiled_weight[31:0] & ~wmask);
    end
end

// int_tiled_weight[63:32]
always @(posedge ACLK) begin
    if (ARESET)
        int_tiled_weight[63:32] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_TILED_WEIGHT_DATA_1)
            int_tiled_weight[63:32] <= (WDATA[31:0] & wmask) | (int_tiled_weight[63:32] & ~wmask);
    end
end

// int_canonical_weight[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_canonical_weight[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_CANONICAL_WEIGHT_DATA_0)
            int_canonical_weight[31:0] <= (WDATA[31:0] & wmask) | (int_canonical_weight[31:0] & ~wmask);
    end
end

// int_canonical_weight[63:32]
always @(posedge ACLK) begin
    if (ARESET)
        int_canonical_weight[63:32] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_CANONICAL_WEIGHT_DATA_1)
            int_canonical_weight[63:32] <= (WDATA[31:0] & wmask) | (int_canonical_weight[63:32] & ~wmask);
    end
end

// int_workspace[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_workspace[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_WORKSPACE_DATA_0)
            int_workspace[31:0] <= (WDATA[31:0] & wmask) | (int_workspace[31:0] & ~wmask);
    end
end

// int_workspace[63:32]
always @(posedge ACLK) begin
    if (ARESET)
        int_workspace[63:32] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_WORKSPACE_DATA_1)
            int_workspace[63:32] <= (WDATA[31:0] & wmask) | (int_workspace[63:32] & ~wmask);
    end
end

// int_capacity_beats[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_capacity_beats[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_CAPACITY_BEATS_DATA_0)
            int_capacity_beats[31:0] <= (WDATA[31:0] & wmask) | (int_capacity_beats[31:0] & ~wmask);
    end
end

// int_debug[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_debug[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_DEBUG_DATA_0)
            int_debug[31:0] <= (WDATA[31:0] & wmask) | (int_debug[31:0] & ~wmask);
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

// int_token
always @(posedge ACLK) begin
    if (ARESET)
        int_token <= 0;
    else if (ACLK_EN) begin
        if (token_ap_vld)
            int_token <= token;
    end
end

// int_token_ap_vld
always @(posedge ACLK) begin
    if (ARESET)
        int_token_ap_vld <= 1'b0;
    else if (ACLK_EN) begin
        if (token_ap_vld)
            int_token_ap_vld <= 1'b1;
        else if (ar_hs && raddr == ADDR_TOKEN_CTRL)
            int_token_ap_vld <= 1'b0; // clear on read
    end
end

// int_score_bits
always @(posedge ACLK) begin
    if (ARESET)
        int_score_bits <= 0;
    else if (ACLK_EN) begin
        if (score_bits_ap_vld)
            int_score_bits <= score_bits;
    end
end

// int_score_bits_ap_vld
always @(posedge ACLK) begin
    if (ARESET)
        int_score_bits_ap_vld <= 1'b0;
    else if (ACLK_EN) begin
        if (score_bits_ap_vld)
            int_score_bits_ap_vld <= 1'b1;
        else if (ar_hs && raddr == ADDR_SCORE_BITS_CTRL)
            int_score_bits_ap_vld <= 1'b0; // clear on read
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

// int_preview_read_beats
always @(posedge ACLK) begin
    if (ARESET)
        int_preview_read_beats <= 0;
    else if (ACLK_EN) begin
        if (preview_read_beats_ap_vld)
            int_preview_read_beats <= preview_read_beats;
    end
end

// int_preview_read_beats_ap_vld
always @(posedge ACLK) begin
    if (ARESET)
        int_preview_read_beats_ap_vld <= 1'b0;
    else if (ACLK_EN) begin
        if (preview_read_beats_ap_vld)
            int_preview_read_beats_ap_vld <= 1'b1;
        else if (ar_hs && raddr == ADDR_PREVIEW_READ_BEATS_CTRL)
            int_preview_read_beats_ap_vld <= 1'b0; // clear on read
    end
end

//synthesis translate_off
always @(posedge ACLK) begin
    if (ACLK_EN) begin
        if (int_gie & ~int_isr[0] & int_ier[0] & ap_done)
            $display ("// Interrupt Monitor : interrupt for ap_done detected @ \"%0t\"", $time);
        if (int_gie & ~int_isr[1] & int_ier[1] & ap_ready)
            $display ("// Interrupt Monitor : interrupt for ap_ready detected @ \"%0t\"", $time);
    end
end
//synthesis translate_on

//------------------------Memory logic-------------------

endmodule
