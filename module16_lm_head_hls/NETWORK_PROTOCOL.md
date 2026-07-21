# 模块 16 CPU↔FPGA 网口协议草案

计算核与网口传输层解耦。当前 HLS 仿真直接使用内存文件；真实开发板阶段由网口服务端接收数据、写 DDR/HBM、启动 `lm_head_argmax`，接口语义不变。

## 生命周期

```text
连接建立
  -> LOAD_WEIGHT（启动时一次，约 260 MiB）
  -> 多次 RUN_TOKEN（每个 token 一次）
  -> 可选 READ_LOGITS（debug）
  -> 连接关闭
```

不应在每个 token 请求中重复发送 LM Head 权重。

## 帧头（24 bytes）

所有整数暂定为 little-endian：

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| magic | 4 bytes | ASCII `LMH1` |
| version | uint16 | 当前为 1 |
| opcode | uint16 | 命令类型 |
| request_id | uint32 | 请求与响应关联 |
| flags | uint32 | debug、重复惩罚等开关 |
| payload_bytes | uint32 | payload 长度 |
| crc32 | uint32 | payload CRC32（IEEE） |

当前 flags：

| bit | 名称 | 含义 |
| --- | --- | --- |
| 0 | ENABLE_REPETITION_PENALTY | 启用重复惩罚 |
| 1 | WANT_LOGITS | 响应附带原始 FP16 logits |
| 2 | FIRST_CHUNK | 权重传输首块 |
| 3 | LAST_CHUNK | 权重传输末块 |

成功响应的 opcode 为 `请求 opcode | 0x8000`；错误响应 opcode 为 `0xffff`，payload 为 UTF-8 错误信息。`request_id` 必须原样返回。

## 命令

### LOAD_WEIGHT = 1

权重按 `[token][hidden]`、FP16、小端顺序传输。每个分块 payload 前缀为：

```text
total_bytes               uint64
hidden_size               uint32
vocab_size                uint32
offset                    uint64
chunk_data                FP16 bytes
```

分块必须从 offset 0 连续递增。服务端收到 `LAST_CHUNK`、确认末块结束位置等于 `total_bytes` 后才切换为 READY。

### RUN_TOKEN = 2

payload 前缀及数据：

```text
hidden_size               uint32
vocab_size                uint32
repetition_penalty        FP32
history_words             uint32
hidden[896]              FP16，1792 bytes
history_bitmap[4748]     uint32，18992 bytes（启用重复惩罚时）
```

正常响应：

```text
status                   uint32
selected_token           uint32
selected_score           FP32
logits_bytes              uint32
```

debug 响应可追加 `raw_logits[151936]`，FP16，共 303872 bytes。

### PING = 3

用于检查连接、协议版本和权重 READY 状态。

## 传输建议

第一版使用 TCP，优先保证完整性和可调试性。帧级 CRC32 用于发现内存、文件或协议处理错误；后续如需要更低延迟，再评估 UDP、自定义重传或 FPGA 侧 TCP/IP 栈。

## 当前仿真实现

- `net/cpu_client.py`：CPU 端固定协议客户端。
- `net/fpga_server_emulator.py`：板端网络与调度服务模拟器；计算后端暂为 NumPy。
- `tools/run_module16_tcp_loopback.py`：真实 Qwen trace 的 TCP 回环检查。

这里验证的是 TCP 报文与模块语义的集成；HLS 硬件正确性由全尺寸 C 仿真和 RTL co-simulation 独立验证。真实板卡阶段以驱动/HBM/HLS kernel 替换模拟器的 NumPy 后端，线上的 CPU 客户端与帧格式保持不变。
