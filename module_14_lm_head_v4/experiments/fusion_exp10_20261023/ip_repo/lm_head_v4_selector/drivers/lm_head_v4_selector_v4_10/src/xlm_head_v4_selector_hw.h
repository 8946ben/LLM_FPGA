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

#define XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_AP_CTRL                 0x00
#define XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_GIE                     0x04
#define XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_IER                     0x08
#define XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_ISR                     0x0c
#define XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_PL_DDR_DATA             0x10
#define XLM_HEAD_V4_SELECTOR_CONTROL_BITS_PL_DDR_DATA             64
#define XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_HISTORY_BITMAP_DATA     0x1c
#define XLM_HEAD_V4_SELECTOR_CONTROL_BITS_HISTORY_BITMAP_DATA     64
#define XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_ARENA_BYTES_DATA        0x28
#define XLM_HEAD_V4_SELECTOR_CONTROL_BITS_ARENA_BYTES_DATA        64
#define XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_DESCRIPTOR_OFFSET_DATA  0x34
#define XLM_HEAD_V4_SELECTOR_CONTROL_BITS_DESCRIPTOR_OFFSET_DATA  64
#define XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_COMMAND_DATA            0x40
#define XLM_HEAD_V4_SELECTOR_CONTROL_BITS_COMMAND_DATA            32
#define XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_STATUS_DATA             0x48
#define XLM_HEAD_V4_SELECTOR_CONTROL_BITS_STATUS_DATA             32
#define XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_STATUS_CTRL             0x4c
#define XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_STAGE_DATA              0x58
#define XLM_HEAD_V4_SELECTOR_CONTROL_BITS_STAGE_DATA              32
#define XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_STAGE_CTRL              0x5c
#define XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_CHILD_STATUS_DATA       0x68
#define XLM_HEAD_V4_SELECTOR_CONTROL_BITS_CHILD_STATUS_DATA       32
#define XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_CHILD_STATUS_CTRL       0x6c
#define XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_ROUTE_COUNT_DATA        0x78
#define XLM_HEAD_V4_SELECTOR_CONTROL_BITS_ROUTE_COUNT_DATA        32
#define XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_ROUTE_COUNT_CTRL        0x7c
#define XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_CANDIDATE_COUNT_DATA    0x88
#define XLM_HEAD_V4_SELECTOR_CONTROL_BITS_CANDIDATE_COUNT_DATA    32
#define XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_CANDIDATE_COUNT_CTRL    0x8c
#define XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_DENSE_FALLBACK_DATA     0x98
#define XLM_HEAD_V4_SELECTOR_CONTROL_BITS_DENSE_FALLBACK_DATA     32
#define XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_DENSE_FALLBACK_CTRL     0x9c
#define XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_SELECTED_TOKEN_OUT_DATA 0xa8
#define XLM_HEAD_V4_SELECTOR_CONTROL_BITS_SELECTED_TOKEN_OUT_DATA 32
#define XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_SELECTED_TOKEN_OUT_CTRL 0xac
#define XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_SCORE_DATA              0xb8
#define XLM_HEAD_V4_SELECTOR_CONTROL_BITS_SCORE_DATA              32
#define XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_SCORE_CTRL              0xbc
#define XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_OUTPUT_CRC_DATA         0xc8
#define XLM_HEAD_V4_SELECTOR_CONTROL_BITS_OUTPUT_CRC_DATA         32
#define XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_OUTPUT_CRC_CTRL         0xcc

