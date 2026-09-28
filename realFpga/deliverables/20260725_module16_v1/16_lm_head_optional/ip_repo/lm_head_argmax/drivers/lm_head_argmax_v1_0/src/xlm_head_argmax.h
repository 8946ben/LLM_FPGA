// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2021.1 (64-bit)
// Copyright 1986-2021 Xilinx, Inc. All Rights Reserved.
// ==============================================================
#ifndef XLM_HEAD_ARGMAX_H
#define XLM_HEAD_ARGMAX_H

#ifdef __cplusplus
extern "C" {
#endif

/***************************** Include Files *********************************/
#ifndef __linux__
#include "xil_types.h"
#include "xil_assert.h"
#include "xstatus.h"
#include "xil_io.h"
#else
#include <stdint.h>
#include <assert.h>
#include <dirent.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
#include <stddef.h>
#endif
#include "xlm_head_argmax_hw.h"

/**************************** Type Definitions ******************************/
#ifdef __linux__
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;
#else
typedef struct {
    u16 DeviceId;
    u32 Control_BaseAddress;
} XLm_head_argmax_Config;
#endif

typedef struct {
    u64 Control_BaseAddress;
    u32 IsReady;
} XLm_head_argmax;

typedef u32 word_type;

/***************** Macros (Inline Functions) Definitions *********************/
#ifndef __linux__
#define XLm_head_argmax_WriteReg(BaseAddress, RegOffset, Data) \
    Xil_Out32((BaseAddress) + (RegOffset), (u32)(Data))
#define XLm_head_argmax_ReadReg(BaseAddress, RegOffset) \
    Xil_In32((BaseAddress) + (RegOffset))
#else
#define XLm_head_argmax_WriteReg(BaseAddress, RegOffset, Data) \
    *(volatile u32*)((BaseAddress) + (RegOffset)) = (u32)(Data)
#define XLm_head_argmax_ReadReg(BaseAddress, RegOffset) \
    *(volatile u32*)((BaseAddress) + (RegOffset))

#define Xil_AssertVoid(expr)    assert(expr)
#define Xil_AssertNonvoid(expr) assert(expr)

#define XST_SUCCESS             0
#define XST_DEVICE_NOT_FOUND    2
#define XST_OPEN_DEVICE_FAILED  3
#define XIL_COMPONENT_IS_READY  1
#endif

/************************** Function Prototypes *****************************/
#ifndef __linux__
int XLm_head_argmax_Initialize(XLm_head_argmax *InstancePtr, u16 DeviceId);
XLm_head_argmax_Config* XLm_head_argmax_LookupConfig(u16 DeviceId);
int XLm_head_argmax_CfgInitialize(XLm_head_argmax *InstancePtr, XLm_head_argmax_Config *ConfigPtr);
#else
int XLm_head_argmax_Initialize(XLm_head_argmax *InstancePtr, const char* InstanceName);
int XLm_head_argmax_Release(XLm_head_argmax *InstancePtr);
#endif

void XLm_head_argmax_Start(XLm_head_argmax *InstancePtr);
u32 XLm_head_argmax_IsDone(XLm_head_argmax *InstancePtr);
u32 XLm_head_argmax_IsIdle(XLm_head_argmax *InstancePtr);
u32 XLm_head_argmax_IsReady(XLm_head_argmax *InstancePtr);
void XLm_head_argmax_EnableAutoRestart(XLm_head_argmax *InstancePtr);
void XLm_head_argmax_DisableAutoRestart(XLm_head_argmax *InstancePtr);

void XLm_head_argmax_Set_hidden(XLm_head_argmax *InstancePtr, u64 Data);
u64 XLm_head_argmax_Get_hidden(XLm_head_argmax *InstancePtr);
void XLm_head_argmax_Set_weight(XLm_head_argmax *InstancePtr, u64 Data);
u64 XLm_head_argmax_Get_weight(XLm_head_argmax *InstancePtr);
void XLm_head_argmax_Set_history_bitmap(XLm_head_argmax *InstancePtr, u64 Data);
u64 XLm_head_argmax_Get_history_bitmap(XLm_head_argmax *InstancePtr);
void XLm_head_argmax_Set_raw_logits(XLm_head_argmax *InstancePtr, u64 Data);
u64 XLm_head_argmax_Get_raw_logits(XLm_head_argmax *InstancePtr);
void XLm_head_argmax_Set_hidden_size(XLm_head_argmax *InstancePtr, u32 Data);
u32 XLm_head_argmax_Get_hidden_size(XLm_head_argmax *InstancePtr);
void XLm_head_argmax_Set_vocab_size(XLm_head_argmax *InstancePtr, u32 Data);
u32 XLm_head_argmax_Get_vocab_size(XLm_head_argmax *InstancePtr);
void XLm_head_argmax_Set_write_logits(XLm_head_argmax *InstancePtr, u32 Data);
u32 XLm_head_argmax_Get_write_logits(XLm_head_argmax *InstancePtr);
void XLm_head_argmax_Set_enable_repetition_penalty(XLm_head_argmax *InstancePtr, u32 Data);
u32 XLm_head_argmax_Get_enable_repetition_penalty(XLm_head_argmax *InstancePtr);
void XLm_head_argmax_Set_repetition_penalty(XLm_head_argmax *InstancePtr, u32 Data);
u32 XLm_head_argmax_Get_repetition_penalty(XLm_head_argmax *InstancePtr);
u32 XLm_head_argmax_Get_selected_token(XLm_head_argmax *InstancePtr);
u32 XLm_head_argmax_Get_selected_token_vld(XLm_head_argmax *InstancePtr);
u32 XLm_head_argmax_Get_selected_score(XLm_head_argmax *InstancePtr);
u32 XLm_head_argmax_Get_selected_score_vld(XLm_head_argmax *InstancePtr);

void XLm_head_argmax_InterruptGlobalEnable(XLm_head_argmax *InstancePtr);
void XLm_head_argmax_InterruptGlobalDisable(XLm_head_argmax *InstancePtr);
void XLm_head_argmax_InterruptEnable(XLm_head_argmax *InstancePtr, u32 Mask);
void XLm_head_argmax_InterruptDisable(XLm_head_argmax *InstancePtr, u32 Mask);
void XLm_head_argmax_InterruptClear(XLm_head_argmax *InstancePtr, u32 Mask);
u32 XLm_head_argmax_InterruptGetEnabled(XLm_head_argmax *InstancePtr);
u32 XLm_head_argmax_InterruptGetStatus(XLm_head_argmax *InstancePtr);

#ifdef __cplusplus
}
#endif

#endif
