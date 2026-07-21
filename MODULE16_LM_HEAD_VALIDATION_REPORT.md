# 模块 16 阶段 1 完整验证报告

## 验证对象

```text
模型：Qwen/Qwen2.5-0.5B-Instruct
来源：ModelScope Qwen 官方仓库
原始文件：artifacts/Qwen2.5-0.5B-Instruct/model.safetensors
原始文件大小：988097824 bytes
SHA-256：fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe
```

该 SHA-256 与 Hugging Face Qwen 官方文件一致。

从原模型中导出的模块 16 共享权重：

```text
tensor：model.embed_tokens.weight
shape：[151936, 896]
原始 dtype：BF16
验证使用 dtype：FP16
```

## 验证链路

```text
lm_head_input.npy
  -> 选择最后一个序列位置
  -> model.embed_tokens.weight 分块矩阵乘
  -> FP32 accumulator
  -> 转换为 FP16 LM Head logits
  -> repetition penalty = 1.1
  -> greedy argmax
  -> metadata.json generated_ids
```

Argmax 在 FP16 LM Head 输出上执行，而不是在 FP32 accumulator 上执行。这一点对
step 7 是必要的：token 100013 和 100048 转换为 FP16 后同为 20.203125，必须按
`torch.argmax` 的规则选择位置较前的 token 100013。

## 真实权重验证结果

| Step | 类型 | 期望 token | LM Head top-1 | 最大绝对误差 | Cosine | Top-5 overlap |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 0 | Prefill | 104198 | 104198 | 0.00390625 | 1.000000000 | 5/5 |
| 1 | Decode | 48 | 48 | 0.00390625 | 1.000000000 | 5/5 |
| 2 | Decode | 16948 | 16948 | 0.00390625 | 1.000000000 | 5/5 |
| 3 | Decode | 3837 | 3837 | 0.0078125 | 1.000000000 | 5/5 |
| 4 | Decode | 67071 | 67071 | 0.0078125 | 1.000000000 | 5/5 |
| 5 | Decode | 102661 | 102661 | 0.0078125 | 1.000000000 | 5/5 |
| 6 | Decode | 99718 | 99718 | 0.0078125 | 1.000000000 | 5/5 |
| 7 | Decode | 100013 | 100013 | 0.0078125 | 1.000000000 | 5/5 |

生成策略 scores 最大绝对误差为 `1.90735e-06`，8 步 token 均与
`metadata.json/generated_ids` 一致。

## 最终结论

```text
单元测试：6/6 PASS
真实 LM Head 矩阵乘：8/8 PASS
生成策略 scores：8/8 PASS
Token 选择：8/8 PASS
overall=PASS
```

阶段 1 已形成完整闭环，不再依赖预先保存的 logits 来宣称 LM Head 计算通过。
