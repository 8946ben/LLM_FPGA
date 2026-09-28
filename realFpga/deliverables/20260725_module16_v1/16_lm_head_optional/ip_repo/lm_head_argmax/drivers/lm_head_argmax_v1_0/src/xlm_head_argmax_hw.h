// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2021.1 (64-bit)
// Copyright 1986-2021 Xilinx, Inc. All Rights Reserved.
// ==============================================================
// control
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

#define XLM_HEAD_ARGMAX_CONTROL_ADDR_AP_CTRL                        0x00
#define XLM_HEAD_ARGMAX_CONTROL_ADDR_GIE                            0x04
#define XLM_HEAD_ARGMAX_CONTROL_ADDR_IER                            0x08
#define XLM_HEAD_ARGMAX_CONTROL_ADDR_ISR                            0x0c
#define XLM_HEAD_ARGMAX_CONTROL_ADDR_HIDDEN_DATA                    0x10
#define XLM_HEAD_ARGMAX_CONTROL_BITS_HIDDEN_DATA                    64
#define XLM_HEAD_ARGMAX_CONTROL_ADDR_WEIGHT_DATA                    0x1c
#define XLM_HEAD_ARGMAX_CONTROL_BITS_WEIGHT_DATA                    64
#define XLM_HEAD_ARGMAX_CONTROL_ADDR_HISTORY_BITMAP_DATA            0x28
#define XLM_HEAD_ARGMAX_CONTROL_BITS_HISTORY_BITMAP_DATA            64
#define XLM_HEAD_ARGMAX_CONTROL_ADDR_RAW_LOGITS_DATA                0x34
#define XLM_HEAD_ARGMAX_CONTROL_BITS_RAW_LOGITS_DATA                64
#define XLM_HEAD_ARGMAX_CONTROL_ADDR_HIDDEN_SIZE_DATA               0x40
#define XLM_HEAD_ARGMAX_CONTROL_BITS_HIDDEN_SIZE_DATA               32
#define XLM_HEAD_ARGMAX_CONTROL_ADDR_VOCAB_SIZE_DATA                0x48
#define XLM_HEAD_ARGMAX_CONTROL_BITS_VOCAB_SIZE_DATA                32
#define XLM_HEAD_ARGMAX_CONTROL_ADDR_WRITE_LOGITS_DATA              0x50
#define XLM_HEAD_ARGMAX_CONTROL_BITS_WRITE_LOGITS_DATA              32
#define XLM_HEAD_ARGMAX_CONTROL_ADDR_ENABLE_REPETITION_PENALTY_DATA 0x58
#define XLM_HEAD_ARGMAX_CONTROL_BITS_ENABLE_REPETITION_PENALTY_DATA 32
#define XLM_HEAD_ARGMAX_CONTROL_ADDR_REPETITION_PENALTY_DATA        0x60
#define XLM_HEAD_ARGMAX_CONTROL_BITS_REPETITION_PENALTY_DATA        32
#define XLM_HEAD_ARGMAX_CONTROL_ADDR_SELECTED_TOKEN_DATA            0x68
#define XLM_HEAD_ARGMAX_CONTROL_BITS_SELECTED_TOKEN_DATA            32
#define XLM_HEAD_ARGMAX_CONTROL_ADDR_SELECTED_TOKEN_CTRL            0x6c
#define XLM_HEAD_ARGMAX_CONTROL_ADDR_SELECTED_SCORE_DATA            0x78
#define XLM_HEAD_ARGMAX_CONTROL_BITS_SELECTED_SCORE_DATA            32
#define XLM_HEAD_ARGMAX_CONTROL_ADDR_SELECTED_SCORE_CTRL            0x7c

