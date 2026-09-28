// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2021.1 (64-bit)
// Copyright 1986-2021 Xilinx, Inc. All Rights Reserved.
// ==============================================================
`timescale 1ns/1ps
module lm_head_argmax_control_s_axi
#(parameter
    C_S_AXI_ADDR_WIDTH = 7,
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
    output wire [63:0]                   hidden,
    output wire [63:0]                   weight,
    output wire [63:0]                   history_bitmap,
    output wire [63:0]                   raw_logits,
    output wire [31:0]                   hidden_size,
    output wire [31:0]                   vocab_size,
    output wire [31:0]                   write_logits,
    output wire [31:0]                   enable_repetition_penalty,
    output wire [31:0]                   repetition_penalty,
    input  wire [31:0]                   selected_token,
    input  wire                          selected_token_ap_vld,
    input  wire [31:0]                   selected_score,
    input  wire                          selected_score_ap_vld,
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
// 0x10 : Data signal of hidden
//        bit 31~0 - hidden[31:0] (Read/Write)
// 0x14 : Data signal of hidden
//        bit 31~0 - hidden[63:32] (Read/Write)
// 0x18 : reserved
// 0x1c : Data signal of weight
//        bit 31~0 - weight[31:0] (Read/Write)
// 0x20 : Data signal of weight
//        bit 31~0 - weight[63:32] (Read/Write)
// 0x24 : reserved
// 0x28 : Data signal of history_bitmap
//        bit 31~0 - history_bitmap[31:0] (Read/Write)
// 0x2c : Data signal of history_bitmap
//        bit 31~0 - history_bitmap[63:32] (Read/Write)
// 0x30 : reserved
// 0x34 : Data signal of raw_logits
//        bit 31~0 - raw_logits[31:0] (Read/Write)
// 0x38 : Data signal of raw_logits
//        bit 31~0 - raw_logits[63:32] (Read/Write)
// 0x3c : reserved
// 0x40 : Data signal of hidden_size
//        bit 31~0 - hidden_size[31:0] (Read/Write)
// 0x44 : reserved
// 0x48 : Data signal of vocab_size
//        bit 31~0 - vocab_size[31:0] (Read/Write)
// 0x4c : reserved
// 0x50 : Data signal of write_logits
//        bit 31~0 - write_logits[31:0] (Read/Write)
// 0x54 : reserved
// 0x58 : Data signal of enable_repetition_penalty
//        bit 31~0 - enable_repetition_penalty[31:0] (Read/Write)
// 0x5c : reserved
// 0x60 : Data signal of repetition_penalty
//        bit 31~0 - repetition_penalty[31:0] (Read/Write)
// 0x64 : reserved
// 0x68 : Data signal of selected_token
//        bit 31~0 - selected_token[31:0] (Read)
// 0x6c : Control signal of selected_token
//        bit 0  - selected_token_ap_vld (Read/COR)
//        others - reserved
// 0x78 : Data signal of selected_score
//        bit 31~0 - selected_score[31:0] (Read)
// 0x7c : Control signal of selected_score
//        bit 0  - selected_score_ap_vld (Read/COR)
//        others - reserved
// (SC = Self Clear, COR = Clear on Read, TOW = Toggle on Write, COH = Clear on Handshake)

//------------------------Parameter----------------------
localparam
    ADDR_AP_CTRL                          = 7'h00,
    ADDR_GIE                              = 7'h04,
    ADDR_IER                              = 7'h08,
    ADDR_ISR                              = 7'h0c,
    ADDR_HIDDEN_DATA_0                    = 7'h10,
    ADDR_HIDDEN_DATA_1                    = 7'h14,
    ADDR_HIDDEN_CTRL                      = 7'h18,
    ADDR_WEIGHT_DATA_0                    = 7'h1c,
    ADDR_WEIGHT_DATA_1                    = 7'h20,
    ADDR_WEIGHT_CTRL                      = 7'h24,
    ADDR_HISTORY_BITMAP_DATA_0            = 7'h28,
    ADDR_HISTORY_BITMAP_DATA_1            = 7'h2c,
    ADDR_HISTORY_BITMAP_CTRL              = 7'h30,
    ADDR_RAW_LOGITS_DATA_0                = 7'h34,
    ADDR_RAW_LOGITS_DATA_1                = 7'h38,
    ADDR_RAW_LOGITS_CTRL                  = 7'h3c,
    ADDR_HIDDEN_SIZE_DATA_0               = 7'h40,
    ADDR_HIDDEN_SIZE_CTRL                 = 7'h44,
    ADDR_VOCAB_SIZE_DATA_0                = 7'h48,
    ADDR_VOCAB_SIZE_CTRL                  = 7'h4c,
    ADDR_WRITE_LOGITS_DATA_0              = 7'h50,
    ADDR_WRITE_LOGITS_CTRL                = 7'h54,
    ADDR_ENABLE_REPETITION_PENALTY_DATA_0 = 7'h58,
    ADDR_ENABLE_REPETITION_PENALTY_CTRL   = 7'h5c,
    ADDR_REPETITION_PENALTY_DATA_0        = 7'h60,
    ADDR_REPETITION_PENALTY_CTRL          = 7'h64,
    ADDR_SELECTED_TOKEN_DATA_0            = 7'h68,
    ADDR_SELECTED_TOKEN_CTRL              = 7'h6c,
    ADDR_SELECTED_SCORE_DATA_0            = 7'h78,
    ADDR_SELECTED_SCORE_CTRL              = 7'h7c,
    WRIDLE                                = 2'd0,
    WRDATA                                = 2'd1,
    WRRESP                                = 2'd2,
    WRRESET                               = 2'd3,
    RDIDLE                                = 2'd0,
    RDDATA                                = 2'd1,
    RDRESET                               = 2'd2,
    ADDR_BITS                = 7;

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
    reg  [63:0]                   int_hidden = 'b0;
    reg  [63:0]                   int_weight = 'b0;
    reg  [63:0]                   int_history_bitmap = 'b0;
    reg  [63:0]                   int_raw_logits = 'b0;
    reg  [31:0]                   int_hidden_size = 'b0;
    reg  [31:0]                   int_vocab_size = 'b0;
    reg  [31:0]                   int_write_logits = 'b0;
    reg  [31:0]                   int_enable_repetition_penalty = 'b0;
    reg  [31:0]                   int_repetition_penalty = 'b0;
    reg                           int_selected_token_ap_vld;
    reg  [31:0]                   int_selected_token = 'b0;
    reg                           int_selected_score_ap_vld;
    reg  [31:0]                   int_selected_score = 'b0;

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
                ADDR_HIDDEN_DATA_0: begin
                    rdata <= int_hidden[31:0];
                end
                ADDR_HIDDEN_DATA_1: begin
                    rdata <= int_hidden[63:32];
                end
                ADDR_WEIGHT_DATA_0: begin
                    rdata <= int_weight[31:0];
                end
                ADDR_WEIGHT_DATA_1: begin
                    rdata <= int_weight[63:32];
                end
                ADDR_HISTORY_BITMAP_DATA_0: begin
                    rdata <= int_history_bitmap[31:0];
                end
                ADDR_HISTORY_BITMAP_DATA_1: begin
                    rdata <= int_history_bitmap[63:32];
                end
                ADDR_RAW_LOGITS_DATA_0: begin
                    rdata <= int_raw_logits[31:0];
                end
                ADDR_RAW_LOGITS_DATA_1: begin
                    rdata <= int_raw_logits[63:32];
                end
                ADDR_HIDDEN_SIZE_DATA_0: begin
                    rdata <= int_hidden_size[31:0];
                end
                ADDR_VOCAB_SIZE_DATA_0: begin
                    rdata <= int_vocab_size[31:0];
                end
                ADDR_WRITE_LOGITS_DATA_0: begin
                    rdata <= int_write_logits[31:0];
                end
                ADDR_ENABLE_REPETITION_PENALTY_DATA_0: begin
                    rdata <= int_enable_repetition_penalty[31:0];
                end
                ADDR_REPETITION_PENALTY_DATA_0: begin
                    rdata <= int_repetition_penalty[31:0];
                end
                ADDR_SELECTED_TOKEN_DATA_0: begin
                    rdata <= int_selected_token[31:0];
                end
                ADDR_SELECTED_TOKEN_CTRL: begin
                    rdata[0] <= int_selected_token_ap_vld;
                end
                ADDR_SELECTED_SCORE_DATA_0: begin
                    rdata <= int_selected_score[31:0];
                end
                ADDR_SELECTED_SCORE_CTRL: begin
                    rdata[0] <= int_selected_score_ap_vld;
                end
            endcase
        end
    end
end


//------------------------Register logic-----------------
assign interrupt                 = int_gie & (|int_isr);
assign ap_start                  = int_ap_start;
assign task_ap_done              = (ap_done && !auto_restart_status) || auto_restart_done;
assign task_ap_ready             = ap_ready && !int_auto_restart;
assign auto_restart_done         = auto_restart_status && (ap_idle && !int_ap_idle);
assign hidden                    = int_hidden;
assign weight                    = int_weight;
assign history_bitmap            = int_history_bitmap;
assign raw_logits                = int_raw_logits;
assign hidden_size               = int_hidden_size;
assign vocab_size                = int_vocab_size;
assign write_logits              = int_write_logits;
assign enable_repetition_penalty = int_enable_repetition_penalty;
assign repetition_penalty        = int_repetition_penalty;
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

// int_hidden[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_hidden[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_HIDDEN_DATA_0)
            int_hidden[31:0] <= (WDATA[31:0] & wmask) | (int_hidden[31:0] & ~wmask);
    end
end

// int_hidden[63:32]
always @(posedge ACLK) begin
    if (ARESET)
        int_hidden[63:32] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_HIDDEN_DATA_1)
            int_hidden[63:32] <= (WDATA[31:0] & wmask) | (int_hidden[63:32] & ~wmask);
    end
end

// int_weight[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_weight[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_WEIGHT_DATA_0)
            int_weight[31:0] <= (WDATA[31:0] & wmask) | (int_weight[31:0] & ~wmask);
    end
end

// int_weight[63:32]
always @(posedge ACLK) begin
    if (ARESET)
        int_weight[63:32] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_WEIGHT_DATA_1)
            int_weight[63:32] <= (WDATA[31:0] & wmask) | (int_weight[63:32] & ~wmask);
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

// int_raw_logits[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_raw_logits[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_RAW_LOGITS_DATA_0)
            int_raw_logits[31:0] <= (WDATA[31:0] & wmask) | (int_raw_logits[31:0] & ~wmask);
    end
end

// int_raw_logits[63:32]
always @(posedge ACLK) begin
    if (ARESET)
        int_raw_logits[63:32] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_RAW_LOGITS_DATA_1)
            int_raw_logits[63:32] <= (WDATA[31:0] & wmask) | (int_raw_logits[63:32] & ~wmask);
    end
end

// int_hidden_size[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_hidden_size[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_HIDDEN_SIZE_DATA_0)
            int_hidden_size[31:0] <= (WDATA[31:0] & wmask) | (int_hidden_size[31:0] & ~wmask);
    end
end

// int_vocab_size[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_vocab_size[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_VOCAB_SIZE_DATA_0)
            int_vocab_size[31:0] <= (WDATA[31:0] & wmask) | (int_vocab_size[31:0] & ~wmask);
    end
end

// int_write_logits[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_write_logits[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_WRITE_LOGITS_DATA_0)
            int_write_logits[31:0] <= (WDATA[31:0] & wmask) | (int_write_logits[31:0] & ~wmask);
    end
end

// int_enable_repetition_penalty[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_enable_repetition_penalty[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_ENABLE_REPETITION_PENALTY_DATA_0)
            int_enable_repetition_penalty[31:0] <= (WDATA[31:0] & wmask) | (int_enable_repetition_penalty[31:0] & ~wmask);
    end
end

// int_repetition_penalty[31:0]
always @(posedge ACLK) begin
    if (ARESET)
        int_repetition_penalty[31:0] <= 0;
    else if (ACLK_EN) begin
        if (w_hs && waddr == ADDR_REPETITION_PENALTY_DATA_0)
            int_repetition_penalty[31:0] <= (WDATA[31:0] & wmask) | (int_repetition_penalty[31:0] & ~wmask);
    end
end

// int_selected_token
always @(posedge ACLK) begin
    if (ARESET)
        int_selected_token <= 0;
    else if (ACLK_EN) begin
        if (selected_token_ap_vld)
            int_selected_token <= selected_token;
    end
end

// int_selected_token_ap_vld
always @(posedge ACLK) begin
    if (ARESET)
        int_selected_token_ap_vld <= 1'b0;
    else if (ACLK_EN) begin
        if (selected_token_ap_vld)
            int_selected_token_ap_vld <= 1'b1;
        else if (ar_hs && raddr == ADDR_SELECTED_TOKEN_CTRL)
            int_selected_token_ap_vld <= 1'b0; // clear on read
    end
end

// int_selected_score
always @(posedge ACLK) begin
    if (ARESET)
        int_selected_score <= 0;
    else if (ACLK_EN) begin
        if (selected_score_ap_vld)
            int_selected_score <= selected_score;
    end
end

// int_selected_score_ap_vld
always @(posedge ACLK) begin
    if (ARESET)
        int_selected_score_ap_vld <= 1'b0;
    else if (ACLK_EN) begin
        if (selected_score_ap_vld)
            int_selected_score_ap_vld <= 1'b1;
        else if (ar_hs && raddr == ADDR_SELECTED_SCORE_CTRL)
            int_selected_score_ap_vld <= 1'b0; // clear on read
    end
end


//------------------------Memory logic-------------------

endmodule
