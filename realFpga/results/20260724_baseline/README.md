# AXU9EGB 模块 16 上板基线记录

> 记录日期：2026-07-24  
> 操作者：zb  
> 当前阶段：网络基础检查与上板前软件基线

## 网络检查

| 项目 | 结果 |
| --- | --- |
| 上位机有线 IPv4 | `192.168.8.12/24` |
| 板卡 IPv4 | `192.168.8.190/24` |
| 板卡 MAC | `00-0a-35-00-01-02` |
| Ping | 4/4 成功，0% 丢包 |
| 往返延迟 | 0-1 ms |
| TCP 50052 | 当前未监听 |

说明：基础以太网链路正常。TCP 50052 未监听表示板卡当前没有运行 RMSNorm 示例服务或使用了其他端口，不属于连通性失败。

## 软件测试

- Python 单元测试：10/10 PASS。
- HLS C 仿真：`HLS_CSIM_OVERALL=PASS`。
- 真实 Qwen trace：8/8 token 完全匹配。
- 每一步 Top-5：5/5。
- 最大 logits 绝对误差：`0.015625`。
- HLS C 仿真耗时：约 `195.574 s`。

## 关键文件 SHA-256

```text
F4E43CEC9B007816CB7C81940C13CAB0CE644A69236DA97F13F1C4064D65112D  artifacts/model.embed_tokens.weight.fp16.npy
1A3187539B5DE201933F7195B460A8C358C6489495209BC73178A5FB44BC84B3  artifacts/module16_hls_fixtures/step_00/hidden.fp16.bin
F364F5E37109D19C35F42F2FB9B1AE8F6D210B437BC228B3C3F88C9C49C30EF4  artifacts/module16_hls_fixtures/step_00/history_bitmap.u32.bin
ED458EDFDDE7B51024A30F9BC7042B0C8C3B79BC2BCB9123241CD984EED53873  artifacts/module16_hls_fixtures/step_00/golden_logits.fp16.bin
```

这些摘要用于后续确认上传到板卡的权重和测试输入与当前黄金基线一致。
