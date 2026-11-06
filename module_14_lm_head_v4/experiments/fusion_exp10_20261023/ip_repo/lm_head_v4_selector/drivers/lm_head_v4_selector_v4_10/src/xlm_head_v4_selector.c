// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2021.1 (64-bit)
// Copyright 1986-2021 Xilinx, Inc. All Rights Reserved.
// ==============================================================
/***************************** Include Files *********************************/
#include "xlm_head_v4_selector.h"

/************************** Function Implementation *************************/
#ifndef __linux__
int XLm_head_v4_selector_CfgInitialize(XLm_head_v4_selector *InstancePtr, XLm_head_v4_selector_Config *ConfigPtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(ConfigPtr != NULL);

    InstancePtr->Control_BaseAddress = ConfigPtr->Control_BaseAddress;
    InstancePtr->IsReady = XIL_COMPONENT_IS_READY;

    return XST_SUCCESS;
}
#endif

void XLm_head_v4_selector_Start(XLm_head_v4_selector *InstancePtr) {
    u32 Data;

    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_AP_CTRL) & 0x80;
    XLm_head_v4_selector_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_AP_CTRL, Data | 0x01);
}

u32 XLm_head_v4_selector_IsDone(XLm_head_v4_selector *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_AP_CTRL);
    return (Data >> 1) & 0x1;
}

u32 XLm_head_v4_selector_IsIdle(XLm_head_v4_selector *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_AP_CTRL);
    return (Data >> 2) & 0x1;
}

u32 XLm_head_v4_selector_IsReady(XLm_head_v4_selector *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_AP_CTRL);
    // check ap_start to see if the pcore is ready for next input
    return !(Data & 0x1);
}

void XLm_head_v4_selector_EnableAutoRestart(XLm_head_v4_selector *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XLm_head_v4_selector_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_AP_CTRL, 0x80);
}

void XLm_head_v4_selector_DisableAutoRestart(XLm_head_v4_selector *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XLm_head_v4_selector_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_AP_CTRL, 0);
}

void XLm_head_v4_selector_Set_pl_ddr(XLm_head_v4_selector *InstancePtr, u64 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XLm_head_v4_selector_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_PL_DDR_DATA, (u32)(Data));
    XLm_head_v4_selector_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_PL_DDR_DATA + 4, (u32)(Data >> 32));
}

u64 XLm_head_v4_selector_Get_pl_ddr(XLm_head_v4_selector *InstancePtr) {
    u64 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_PL_DDR_DATA);
    Data += (u64)XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_PL_DDR_DATA + 4) << 32;
    return Data;
}

void XLm_head_v4_selector_Set_history_bitmap(XLm_head_v4_selector *InstancePtr, u64 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XLm_head_v4_selector_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_HISTORY_BITMAP_DATA, (u32)(Data));
    XLm_head_v4_selector_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_HISTORY_BITMAP_DATA + 4, (u32)(Data >> 32));
}

u64 XLm_head_v4_selector_Get_history_bitmap(XLm_head_v4_selector *InstancePtr) {
    u64 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_HISTORY_BITMAP_DATA);
    Data += (u64)XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_HISTORY_BITMAP_DATA + 4) << 32;
    return Data;
}

void XLm_head_v4_selector_Set_arena_bytes(XLm_head_v4_selector *InstancePtr, u64 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XLm_head_v4_selector_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_ARENA_BYTES_DATA, (u32)(Data));
    XLm_head_v4_selector_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_ARENA_BYTES_DATA + 4, (u32)(Data >> 32));
}

u64 XLm_head_v4_selector_Get_arena_bytes(XLm_head_v4_selector *InstancePtr) {
    u64 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_ARENA_BYTES_DATA);
    Data += (u64)XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_ARENA_BYTES_DATA + 4) << 32;
    return Data;
}

void XLm_head_v4_selector_Set_descriptor_offset(XLm_head_v4_selector *InstancePtr, u64 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XLm_head_v4_selector_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_DESCRIPTOR_OFFSET_DATA, (u32)(Data));
    XLm_head_v4_selector_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_DESCRIPTOR_OFFSET_DATA + 4, (u32)(Data >> 32));
}

u64 XLm_head_v4_selector_Get_descriptor_offset(XLm_head_v4_selector *InstancePtr) {
    u64 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_DESCRIPTOR_OFFSET_DATA);
    Data += (u64)XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_DESCRIPTOR_OFFSET_DATA + 4) << 32;
    return Data;
}

void XLm_head_v4_selector_Set_command(XLm_head_v4_selector *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XLm_head_v4_selector_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_COMMAND_DATA, Data);
}

u32 XLm_head_v4_selector_Get_command(XLm_head_v4_selector *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_COMMAND_DATA);
    return Data;
}

u32 XLm_head_v4_selector_Get_status(XLm_head_v4_selector *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_STATUS_DATA);
    return Data;
}

u32 XLm_head_v4_selector_Get_status_vld(XLm_head_v4_selector *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_STATUS_CTRL);
    return Data & 0x1;
}

u32 XLm_head_v4_selector_Get_stage(XLm_head_v4_selector *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_STAGE_DATA);
    return Data;
}

u32 XLm_head_v4_selector_Get_stage_vld(XLm_head_v4_selector *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_STAGE_CTRL);
    return Data & 0x1;
}

u32 XLm_head_v4_selector_Get_child_status(XLm_head_v4_selector *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_CHILD_STATUS_DATA);
    return Data;
}

u32 XLm_head_v4_selector_Get_child_status_vld(XLm_head_v4_selector *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_CHILD_STATUS_CTRL);
    return Data & 0x1;
}

u32 XLm_head_v4_selector_Get_route_count(XLm_head_v4_selector *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_ROUTE_COUNT_DATA);
    return Data;
}

u32 XLm_head_v4_selector_Get_route_count_vld(XLm_head_v4_selector *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_ROUTE_COUNT_CTRL);
    return Data & 0x1;
}

u32 XLm_head_v4_selector_Get_candidate_count(XLm_head_v4_selector *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_CANDIDATE_COUNT_DATA);
    return Data;
}

u32 XLm_head_v4_selector_Get_candidate_count_vld(XLm_head_v4_selector *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_CANDIDATE_COUNT_CTRL);
    return Data & 0x1;
}

u32 XLm_head_v4_selector_Get_dense_fallback(XLm_head_v4_selector *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_DENSE_FALLBACK_DATA);
    return Data;
}

u32 XLm_head_v4_selector_Get_dense_fallback_vld(XLm_head_v4_selector *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_DENSE_FALLBACK_CTRL);
    return Data & 0x1;
}

u32 XLm_head_v4_selector_Get_selected_token_out(XLm_head_v4_selector *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_SELECTED_TOKEN_OUT_DATA);
    return Data;
}

u32 XLm_head_v4_selector_Get_selected_token_out_vld(XLm_head_v4_selector *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_SELECTED_TOKEN_OUT_CTRL);
    return Data & 0x1;
}

u32 XLm_head_v4_selector_Get_score(XLm_head_v4_selector *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_SCORE_DATA);
    return Data;
}

u32 XLm_head_v4_selector_Get_score_vld(XLm_head_v4_selector *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_SCORE_CTRL);
    return Data & 0x1;
}

u32 XLm_head_v4_selector_Get_output_crc(XLm_head_v4_selector *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_OUTPUT_CRC_DATA);
    return Data;
}

u32 XLm_head_v4_selector_Get_output_crc_vld(XLm_head_v4_selector *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_OUTPUT_CRC_CTRL);
    return Data & 0x1;
}

void XLm_head_v4_selector_InterruptGlobalEnable(XLm_head_v4_selector *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XLm_head_v4_selector_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_GIE, 1);
}

void XLm_head_v4_selector_InterruptGlobalDisable(XLm_head_v4_selector *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XLm_head_v4_selector_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_GIE, 0);
}

void XLm_head_v4_selector_InterruptEnable(XLm_head_v4_selector *InstancePtr, u32 Mask) {
    u32 Register;

    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Register =  XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_IER);
    XLm_head_v4_selector_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_IER, Register | Mask);
}

void XLm_head_v4_selector_InterruptDisable(XLm_head_v4_selector *InstancePtr, u32 Mask) {
    u32 Register;

    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Register =  XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_IER);
    XLm_head_v4_selector_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_IER, Register & (~Mask));
}

void XLm_head_v4_selector_InterruptClear(XLm_head_v4_selector *InstancePtr, u32 Mask) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XLm_head_v4_selector_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_ISR, Mask);
}

u32 XLm_head_v4_selector_InterruptGetEnabled(XLm_head_v4_selector *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_IER);
}

u32 XLm_head_v4_selector_InterruptGetStatus(XLm_head_v4_selector *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return XLm_head_v4_selector_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_V4_SELECTOR_CONTROL_ADDR_ISR);
}

