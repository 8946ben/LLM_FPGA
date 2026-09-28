// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2021.1 (64-bit)
// Copyright 1986-2021 Xilinx, Inc. All Rights Reserved.
// ==============================================================
/***************************** Include Files *********************************/
#include "xlm_head_argmax.h"

/************************** Function Implementation *************************/
#ifndef __linux__
int XLm_head_argmax_CfgInitialize(XLm_head_argmax *InstancePtr, XLm_head_argmax_Config *ConfigPtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(ConfigPtr != NULL);

    InstancePtr->Control_BaseAddress = ConfigPtr->Control_BaseAddress;
    InstancePtr->IsReady = XIL_COMPONENT_IS_READY;

    return XST_SUCCESS;
}
#endif

void XLm_head_argmax_Start(XLm_head_argmax *InstancePtr) {
    u32 Data;

    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_argmax_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_AP_CTRL) & 0x80;
    XLm_head_argmax_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_AP_CTRL, Data | 0x01);
}

u32 XLm_head_argmax_IsDone(XLm_head_argmax *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_argmax_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_AP_CTRL);
    return (Data >> 1) & 0x1;
}

u32 XLm_head_argmax_IsIdle(XLm_head_argmax *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_argmax_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_AP_CTRL);
    return (Data >> 2) & 0x1;
}

u32 XLm_head_argmax_IsReady(XLm_head_argmax *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_argmax_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_AP_CTRL);
    // check ap_start to see if the pcore is ready for next input
    return !(Data & 0x1);
}

void XLm_head_argmax_EnableAutoRestart(XLm_head_argmax *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XLm_head_argmax_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_AP_CTRL, 0x80);
}

void XLm_head_argmax_DisableAutoRestart(XLm_head_argmax *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XLm_head_argmax_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_AP_CTRL, 0);
}

void XLm_head_argmax_Set_hidden(XLm_head_argmax *InstancePtr, u64 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XLm_head_argmax_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_HIDDEN_DATA, (u32)(Data));
    XLm_head_argmax_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_HIDDEN_DATA + 4, (u32)(Data >> 32));
}

u64 XLm_head_argmax_Get_hidden(XLm_head_argmax *InstancePtr) {
    u64 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_argmax_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_HIDDEN_DATA);
    Data += (u64)XLm_head_argmax_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_HIDDEN_DATA + 4) << 32;
    return Data;
}

void XLm_head_argmax_Set_weight(XLm_head_argmax *InstancePtr, u64 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XLm_head_argmax_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_WEIGHT_DATA, (u32)(Data));
    XLm_head_argmax_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_WEIGHT_DATA + 4, (u32)(Data >> 32));
}

u64 XLm_head_argmax_Get_weight(XLm_head_argmax *InstancePtr) {
    u64 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_argmax_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_WEIGHT_DATA);
    Data += (u64)XLm_head_argmax_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_WEIGHT_DATA + 4) << 32;
    return Data;
}

void XLm_head_argmax_Set_history_bitmap(XLm_head_argmax *InstancePtr, u64 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XLm_head_argmax_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_HISTORY_BITMAP_DATA, (u32)(Data));
    XLm_head_argmax_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_HISTORY_BITMAP_DATA + 4, (u32)(Data >> 32));
}

u64 XLm_head_argmax_Get_history_bitmap(XLm_head_argmax *InstancePtr) {
    u64 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_argmax_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_HISTORY_BITMAP_DATA);
    Data += (u64)XLm_head_argmax_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_HISTORY_BITMAP_DATA + 4) << 32;
    return Data;
}

void XLm_head_argmax_Set_raw_logits(XLm_head_argmax *InstancePtr, u64 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XLm_head_argmax_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_RAW_LOGITS_DATA, (u32)(Data));
    XLm_head_argmax_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_RAW_LOGITS_DATA + 4, (u32)(Data >> 32));
}

u64 XLm_head_argmax_Get_raw_logits(XLm_head_argmax *InstancePtr) {
    u64 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_argmax_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_RAW_LOGITS_DATA);
    Data += (u64)XLm_head_argmax_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_RAW_LOGITS_DATA + 4) << 32;
    return Data;
}

void XLm_head_argmax_Set_hidden_size(XLm_head_argmax *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XLm_head_argmax_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_HIDDEN_SIZE_DATA, Data);
}

u32 XLm_head_argmax_Get_hidden_size(XLm_head_argmax *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_argmax_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_HIDDEN_SIZE_DATA);
    return Data;
}

void XLm_head_argmax_Set_vocab_size(XLm_head_argmax *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XLm_head_argmax_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_VOCAB_SIZE_DATA, Data);
}

u32 XLm_head_argmax_Get_vocab_size(XLm_head_argmax *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_argmax_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_VOCAB_SIZE_DATA);
    return Data;
}

void XLm_head_argmax_Set_write_logits(XLm_head_argmax *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XLm_head_argmax_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_WRITE_LOGITS_DATA, Data);
}

u32 XLm_head_argmax_Get_write_logits(XLm_head_argmax *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_argmax_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_WRITE_LOGITS_DATA);
    return Data;
}

void XLm_head_argmax_Set_enable_repetition_penalty(XLm_head_argmax *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XLm_head_argmax_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_ENABLE_REPETITION_PENALTY_DATA, Data);
}

u32 XLm_head_argmax_Get_enable_repetition_penalty(XLm_head_argmax *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_argmax_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_ENABLE_REPETITION_PENALTY_DATA);
    return Data;
}

void XLm_head_argmax_Set_repetition_penalty(XLm_head_argmax *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XLm_head_argmax_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_REPETITION_PENALTY_DATA, Data);
}

u32 XLm_head_argmax_Get_repetition_penalty(XLm_head_argmax *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_argmax_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_REPETITION_PENALTY_DATA);
    return Data;
}

u32 XLm_head_argmax_Get_selected_token(XLm_head_argmax *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_argmax_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_SELECTED_TOKEN_DATA);
    return Data;
}

u32 XLm_head_argmax_Get_selected_token_vld(XLm_head_argmax *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_argmax_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_SELECTED_TOKEN_CTRL);
    return Data & 0x1;
}

u32 XLm_head_argmax_Get_selected_score(XLm_head_argmax *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_argmax_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_SELECTED_SCORE_DATA);
    return Data;
}

u32 XLm_head_argmax_Get_selected_score_vld(XLm_head_argmax *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XLm_head_argmax_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_SELECTED_SCORE_CTRL);
    return Data & 0x1;
}

void XLm_head_argmax_InterruptGlobalEnable(XLm_head_argmax *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XLm_head_argmax_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_GIE, 1);
}

void XLm_head_argmax_InterruptGlobalDisable(XLm_head_argmax *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XLm_head_argmax_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_GIE, 0);
}

void XLm_head_argmax_InterruptEnable(XLm_head_argmax *InstancePtr, u32 Mask) {
    u32 Register;

    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Register =  XLm_head_argmax_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_IER);
    XLm_head_argmax_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_IER, Register | Mask);
}

void XLm_head_argmax_InterruptDisable(XLm_head_argmax *InstancePtr, u32 Mask) {
    u32 Register;

    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Register =  XLm_head_argmax_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_IER);
    XLm_head_argmax_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_IER, Register & (~Mask));
}

void XLm_head_argmax_InterruptClear(XLm_head_argmax *InstancePtr, u32 Mask) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XLm_head_argmax_WriteReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_ISR, Mask);
}

u32 XLm_head_argmax_InterruptGetEnabled(XLm_head_argmax *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return XLm_head_argmax_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_IER);
}

u32 XLm_head_argmax_InterruptGetStatus(XLm_head_argmax *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return XLm_head_argmax_ReadReg(InstancePtr->Control_BaseAddress, XLM_HEAD_ARGMAX_CONTROL_ADDR_ISR);
}

