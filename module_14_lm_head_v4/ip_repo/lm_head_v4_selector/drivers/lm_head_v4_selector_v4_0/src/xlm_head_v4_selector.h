// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2021.1 (64-bit)
// Copyright 1986-2021 Xilinx, Inc. All Rights Reserved.
// ==============================================================
#ifndef XLM_HEAD_V4_SELECTOR_H
#define XLM_HEAD_V4_SELECTOR_H

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
#include "xlm_head_v4_selector_hw.h"

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
} XLm_head_v4_selector_Config;
#endif

typedef struct {
    u64 Control_BaseAddress;
    u32 IsReady;
} XLm_head_v4_selector;

typedef u32 word_type;

/***************** Macros (Inline Functions) Definitions *********************/
#ifndef __linux__
#define XLm_head_v4_selector_WriteReg(BaseAddress, RegOffset, Data) \
    Xil_Out32((BaseAddress) + (RegOffset), (u32)(Data))
#define XLm_head_v4_selector_ReadReg(BaseAddress, RegOffset) \
    Xil_In32((BaseAddress) + (RegOffset))
#else
#define XLm_head_v4_selector_WriteReg(BaseAddress, RegOffset, Data) \
    *(volatile u32*)((BaseAddress) + (RegOffset)) = (u32)(Data)
#define XLm_head_v4_selector_ReadReg(BaseAddress, RegOffset) \
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
int XLm_head_v4_selector_Initialize(XLm_head_v4_selector *InstancePtr, u16 DeviceId);
XLm_head_v4_selector_Config* XLm_head_v4_selector_LookupConfig(u16 DeviceId);
int XLm_head_v4_selector_CfgInitialize(XLm_head_v4_selector *InstancePtr, XLm_head_v4_selector_Config *ConfigPtr);
#else
int XLm_head_v4_selector_Initialize(XLm_head_v4_selector *InstancePtr, const char* InstanceName);
int XLm_head_v4_selector_Release(XLm_head_v4_selector *InstancePtr);
#endif

void XLm_head_v4_selector_Start(XLm_head_v4_selector *InstancePtr);
u32 XLm_head_v4_selector_IsDone(XLm_head_v4_selector *InstancePtr);
u32 XLm_head_v4_selector_IsIdle(XLm_head_v4_selector *InstancePtr);
u32 XLm_head_v4_selector_IsReady(XLm_head_v4_selector *InstancePtr);
void XLm_head_v4_selector_EnableAutoRestart(XLm_head_v4_selector *InstancePtr);
void XLm_head_v4_selector_DisableAutoRestart(XLm_head_v4_selector *InstancePtr);

void XLm_head_v4_selector_Set_pl_ddr(XLm_head_v4_selector *InstancePtr, u64 Data);
u64 XLm_head_v4_selector_Get_pl_ddr(XLm_head_v4_selector *InstancePtr);
void XLm_head_v4_selector_Set_history_bitmap(XLm_head_v4_selector *InstancePtr, u64 Data);
u64 XLm_head_v4_selector_Get_history_bitmap(XLm_head_v4_selector *InstancePtr);
void XLm_head_v4_selector_Set_arena_bytes(XLm_head_v4_selector *InstancePtr, u64 Data);
u64 XLm_head_v4_selector_Get_arena_bytes(XLm_head_v4_selector *InstancePtr);
void XLm_head_v4_selector_Set_descriptor_offset(XLm_head_v4_selector *InstancePtr, u64 Data);
u64 XLm_head_v4_selector_Get_descriptor_offset(XLm_head_v4_selector *InstancePtr);
void XLm_head_v4_selector_Set_command(XLm_head_v4_selector *InstancePtr, u32 Data);
u32 XLm_head_v4_selector_Get_command(XLm_head_v4_selector *InstancePtr);
u32 XLm_head_v4_selector_Get_status(XLm_head_v4_selector *InstancePtr);
u32 XLm_head_v4_selector_Get_status_vld(XLm_head_v4_selector *InstancePtr);
u32 XLm_head_v4_selector_Get_stage(XLm_head_v4_selector *InstancePtr);
u32 XLm_head_v4_selector_Get_stage_vld(XLm_head_v4_selector *InstancePtr);
u32 XLm_head_v4_selector_Get_child_status(XLm_head_v4_selector *InstancePtr);
u32 XLm_head_v4_selector_Get_child_status_vld(XLm_head_v4_selector *InstancePtr);
u32 XLm_head_v4_selector_Get_route_count(XLm_head_v4_selector *InstancePtr);
u32 XLm_head_v4_selector_Get_route_count_vld(XLm_head_v4_selector *InstancePtr);
u32 XLm_head_v4_selector_Get_candidate_count(XLm_head_v4_selector *InstancePtr);
u32 XLm_head_v4_selector_Get_candidate_count_vld(XLm_head_v4_selector *InstancePtr);
u32 XLm_head_v4_selector_Get_dense_fallback(XLm_head_v4_selector *InstancePtr);
u32 XLm_head_v4_selector_Get_dense_fallback_vld(XLm_head_v4_selector *InstancePtr);
u32 XLm_head_v4_selector_Get_token(XLm_head_v4_selector *InstancePtr);
u32 XLm_head_v4_selector_Get_token_vld(XLm_head_v4_selector *InstancePtr);
u32 XLm_head_v4_selector_Get_score(XLm_head_v4_selector *InstancePtr);
u32 XLm_head_v4_selector_Get_score_vld(XLm_head_v4_selector *InstancePtr);
u32 XLm_head_v4_selector_Get_output_crc(XLm_head_v4_selector *InstancePtr);
u32 XLm_head_v4_selector_Get_output_crc_vld(XLm_head_v4_selector *InstancePtr);

void XLm_head_v4_selector_InterruptGlobalEnable(XLm_head_v4_selector *InstancePtr);
void XLm_head_v4_selector_InterruptGlobalDisable(XLm_head_v4_selector *InstancePtr);
void XLm_head_v4_selector_InterruptEnable(XLm_head_v4_selector *InstancePtr, u32 Mask);
void XLm_head_v4_selector_InterruptDisable(XLm_head_v4_selector *InstancePtr, u32 Mask);
void XLm_head_v4_selector_InterruptClear(XLm_head_v4_selector *InstancePtr, u32 Mask);
u32 XLm_head_v4_selector_InterruptGetEnabled(XLm_head_v4_selector *InstancePtr);
u32 XLm_head_v4_selector_InterruptGetStatus(XLm_head_v4_selector *InstancePtr);

#ifdef __cplusplus
}
#endif

#endif
