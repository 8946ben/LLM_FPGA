# LMH1 TCP 协议

所有整数和浮点字段均为 little-endian。每帧 24-byte header：

```text
magic[4]       "LMH1"
version u16    1
opcode  u16
request_id u32
flags u32
payload_bytes u32
crc32 u32      IEEE CRC32 of payload
```

opcodes：

```text
1 LOAD_WEIGHT
2 RUN_TOKEN
3 PING
成功响应 = request opcode | 0x8000
错误响应 = 0xffff，payload 为 UTF-8 错误信息
```

flags：

```text
bit 0 ENABLE_REPETITION_PENALTY
bit 1 WANT_LOGITS
bit 2 FIRST_CHUNK
bit 3 LAST_CHUNK
```

## LOAD_WEIGHT

payload prefix：

```text
total_bytes u64
hidden_size u32
vocab_size  u32
offset      u64
chunk_data
```

权重为 `[vocab][hidden]` FP16 little-endian。首末块通过 flags 标记；offset
必须连续。全尺寸权重为 272269312 bytes，板卡重启后上传一次即可。

## RUN_TOKEN

payload：

```text
hidden_size u32
vocab_size u32
repetition_penalty f32
history_words u32
hidden[hidden_size] FP16
history_bitmap[history_words] u32
```

正常响应 prefix：

```text
status u32
selected_token u32
selected_score f32
logits_bytes u32
```

设置 `WANT_LOGITS` 后追加 FP16 `raw_logits[vocab_size]`。

## PING

请求 payload 为空。响应包含 status、当前已加载的 hidden/vocab shape 和
weight bytes，用于确认板端权重是否仍在 DDR 中。

