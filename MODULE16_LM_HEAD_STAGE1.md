# 模块 16：阶段 1 CPU Reference

阶段 1 已将 LM Head 数值计算和生成策略验证拆成两个独立部分：

```text
lm_head_input.npy 最后一个位置
  -> model.embed_tokens.weight 矩阵乘
  -> 原始 logits
  -> repetition penalty
  -> greedy argmax
```

## 文件

- `qwen25_0p5b_python_reference/lm_head_cpu_reference.py`：分块 CPU LM Head、重复惩罚、argmax 和 8 步 trace 验证。
- `tools/export_lm_head_weight.py`：不依赖 PyTorch/safetensors 包，直接从模型 safetensors 导出绑定的 embedding/LM Head 权重。
- `tests/test_lm_head_cpu_reference.py`：公式、prefill 最后位置、重复惩罚、argmax tie-break 和 BF16 权重读取单元测试。

## 1. 立即运行 trace 与 token 策略验证

该模式不需要模型权重，使用仓库已有的原始 logits 验证重复惩罚及最终 token：

```powershell
python qwen25_0p5b_python_reference/lm_head_cpu_reference.py
```

成功标准为 8 步生成策略全部显示 `PASS`。由于没有执行权重矩阵乘，最后明确显示：

```text
lm_head_matmul=NOT_RUN
overall=PARTIAL_PASS
```

## 2. 导出绑定的 LM Head 权重

Qwen2.5-0.5B-Instruct 设置了 `tie_word_embeddings=True`，所以应导出
`model.embed_tokens.weight`，而不是查找独立的 `lm_head.weight`：

```powershell
python tools/export_lm_head_weight.py `
  D:\models\Qwen2.5-0.5B-Instruct `
  artifacts\model.embed_tokens.weight.fp16.npy
```

输入既可以是模型目录，也可以是单个 `.safetensors` 文件。默认要求 shape 为
`[151936, 896]` 并导出 FP16，与当前 trace 的模型执行 dtype 一致。

## 3. 完整矩阵乘验证

```powershell
python qwen25_0p5b_python_reference/lm_head_cpu_reference.py `
  --weight artifacts\model.embed_tokens.weight.fp16.npy `
  --output-dir artifacts\module16_cpu_logits
```

默认按 4096 个词表项分块、FP32 累加。可先只验证 prefill：

```powershell
python qwen25_0p5b_python_reference/lm_head_cpu_reference.py `
  --weight artifacts\model.embed_tokens.weight.fp16.npy `
  --step 0
```

CUDA FP16 GEMM 和 CPU FP32 累加顺序不同，因此完整矩阵乘以 top-1、top-5、余弦相似度和最大绝对误差共同判断，不要求逐 bit 相等。

## 4. 单元测试

```powershell
python -m unittest tests/test_lm_head_cpu_reference.py -v
```

模型权重和计算结果保存在被 Git 忽略的 `artifacts/` 目录，不会提交到仓库。执行第 2、3 项可以完成权重矩阵乘的最终闭环；本项目当前的实测结果见 `MODULE16_LM_HEAD_VALIDATION_REPORT.md`。
