# tests

完整模型和 trace 不上传 GitHub；本目录提供可重复生成测试输入的脚本。

```text
export_lm_head_weight.py          从 safetensors 导出 tied LM Head FP16 权重
prepare_lm_head_hls_fixture.py    从 qwen trace 生成 8-step raw fixture
stage_h4_board_small_test.py      真实板卡 4x4 手算测试
```

golden trace 预期目录：

```text
integration_tests/golden_traces/qwen25_0p5b_instruct_full_generation_trace
```

关键比较口径：

```text
raw FPGA logits
  <-> 每步 lm_head_vocab_logits.npy

penalty 后 processed scores
  <-> generation_token_vocab_logits/*.npy

selected token
  <-> metadata.json generated_ids
```

raw logits 和 processed scores 的 `atol` 均为 `0.02`。只比较
`generated_ids` 不足以验证 repetition penalty：当前 8-step trace 在 penalty
开/关时 Top-1 恰好相同。`lm_head_tb.cpp` 和 `stage_h4_board_small_test.py`
包含 penalty 确实改变 Top-1 的专门构造用例。

运行板卡小测试前，从模块根目录执行：

```powershell
python tests\stage_h4_board_small_test.py --host 192.168.8.190 --port 19016
```

