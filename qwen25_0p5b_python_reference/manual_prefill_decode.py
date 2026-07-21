"""Explicit Qwen2.5-0.5B prefill/decode inference loop.

Unlike run_full_generate_trace.py, this script does not call model.generate().
It shows the exact autoregressive flow that FPGA runtime needs to reproduce:

  prompt -> tokenizer/chat template -> prefill forward -> argmax next token
  -> decode forward with past_key_values -> argmax -> repeat

When used with the instrumented Transformers source and QWEN2_FPGA_RECORD=1,
each model forward call creates one trace step:

  step_0000 = prefill full prompt
  step_0001 = decode generated token 01
  ...
"""
# ===== 以下中文注释由 AI 助手添加，用于辅助理解，非原始代码 =====

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


# 默认用户提示词（中文）："你好，请用一句话介绍你自己。"
DEFAULT_PROMPT = "\u4f60\u597d\uff0c\u8bf7\u7528\u4e00\u53e5\u8bdd\u4ecb\u7ecd\u4f60\u81ea\u5df1\u3002"
# 默认系统提示词，Qwen 模型的标准 system prompt
DEFAULT_SYSTEM = "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."


def parse_args() -> argparse.Namespace:
    """[Qwen] 解析命令行参数，配置模型路径、输出目录、生成参数等。"""
    parser = argparse.ArgumentParser(description="Run explicit Qwen2.5 prefill/decode loop.")
    parser.add_argument("--model-path", default="/data3/models/Qwen2.5-0.5B-Instruct")  # 本地模型权重路径
    parser.add_argument("--record-dir", default=None)  # trace 输出目录，设置后开启插桩记录
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)  # 用户输入提示词
    parser.add_argument("--system", default=DEFAULT_SYSTEM)  # 系统提示词
    parser.add_argument("--max-new-tokens", type=int, default=8)  # 最大生成 token 数
    parser.add_argument("--device", default="cuda:0")  # 推理设备
    parser.add_argument("--dtype", choices=["float16", "bfloat16", "float32"], default="float16")  # 计算精度
    parser.add_argument("--save-scores", action="store_true")  # 是否保存每步的 vocab logits
    return parser.parse_args()


def resolve_dtype(name: str) -> torch.dtype:
    """[Qwen] 将字符串精度名称映射为 PyTorch dtype 对象。"""
    if name == "float16":
        return torch.float16
    if name == "bfloat16":
        return torch.bfloat16
    if name == "float32":
        return torch.float32
    raise ValueError(f"Unsupported dtype: {name}")


def save_score(record_dir: Path, step_index: int, logits: torch.Tensor) -> list[int]:
    """[Qwen] 保存当前步最后一个位置的 vocab logits（转为 FP32），用于后续 FPGA 对齐验证。"""
    score_dir = record_dir / "generation_token_vocab_logits"
    score_dir.mkdir(parents=True, exist_ok=True)
    # 取 logits 的最后一个位置（即下一个待预测 token 的分数），转为 float32 numpy
    score = logits[:, -1, :].detach().cpu().to(torch.float32).numpy()
    # prefill 步和 decode 步使用不同的文件命名
    if step_index == 0:
        name = "prefill_next_token_vocab_logits.npy"
    else:
        name = f"decode_step_{step_index:04d}_next_token_vocab_logits.npy"
    np.save(score_dir / name, score)
    return list(score.shape)


def main() -> None:
    """[Qwen] 主函数：执行完整的 prefill + decode 自回归生成流程，可选导出 golden trace。"""
    args = parse_args()
    # 若指定了 record-dir，则设置环境变量启用插桩版 Transformers 的 tensor 记录功能
    if args.record_dir:
        record_dir = Path(args.record_dir)
        record_dir.mkdir(parents=True, exist_ok=True)
        os.environ["QWEN2_FPGA_RECORD"] = "1"  # 开启 FPGA recorder 开关
        os.environ["QWEN2_FPGA_RECORD_DIR"] = str(record_dir)  # 指定 .npy 输出目录
    else:
        record_dir = None

    # ---------- 输入准备：tokenizer + chat template ----------
    tokenizer = AutoTokenizer.from_pretrained(args.model_path, local_files_only=True)
    messages = [
        {"role": "system", "content": args.system},
        {"role": "user", "content": args.prompt},
    ]
    # 应用 Qwen 的 chat template，拼接 system/user/assistant 标记
    chat_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    model_inputs = tokenizer([chat_text], return_tensors="pt")
    input_ids = model_inputs.input_ids.to(args.device)  # shape: (1, seq_len)
    attention_mask = model_inputs.attention_mask.to(args.device)

    # ---------- 加载模型 ----------
    model = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        local_files_only=True,
        torch_dtype=resolve_dtype(args.dtype),
        attn_implementation="eager",  # 使用 eager attention，确保中间量可导出（非 FlashAttention）
    ).to(args.device)
    model.eval()  # 推理模式，确保 training=False（本模型 attention_dropout=0.0 实际无 dropout，但保证确定性输出）

    generated_ids: list[int] = []  # 存储所有生成的 token id
    score_shapes: list[list[int]] = []  # 记录每步 logits 的 shape
    past_key_values = None  # KV cache，prefill 后开始累积

    with torch.no_grad():  # 推理无需计算梯度，节省显存
        # ========== Prefill 阶段 ==========
        # [Qwen] 完整 prompt 一次性输入模型，生成 KV cache 并预测第一个 token
        outputs = model(input_ids=input_ids, attention_mask=attention_mask, use_cache=True)
        past_key_values = outputs.past_key_values  # 保存 KV cache 供后续 decode 使用
        # 贪心解码：取最后一个位置 logits 的 argmax 作为下一个 token
        next_token = torch.argmax(outputs.logits[:, -1, :], dim=-1, keepdim=True)
        generated_ids.append(int(next_token.item()))
        if args.save_scores and record_dir is not None:
            score_shapes.append(save_score(record_dir, 0, outputs.logits))

        # ========== Decode 阶段 ==========
        # [Qwen] 每步只输入上一步生成的单个 token，利用 KV cache 避免重复计算
        for step_index in range(1, args.max_new_tokens):
            # 扩展 attention_mask：每生成一个 token，序列长度 +1
            attention_mask = torch.cat(
                [attention_mask, torch.ones((attention_mask.shape[0], 1), device=args.device, dtype=attention_mask.dtype)],
                dim=-1,
            )
            # 带 KV cache 的单 token 前向推理
            outputs = model(
                input_ids=next_token,  # 仅输入上一步生成的 token，shape: (1, 1)
                attention_mask=attention_mask,
                past_key_values=past_key_values,  # 传入历史 KV cache
                use_cache=True,
            )
            past_key_values = outputs.past_key_values  # 更新 KV cache
            next_token = torch.argmax(outputs.logits[:, -1, :], dim=-1, keepdim=True)
            generated_ids.append(int(next_token.item()))
            if args.save_scores and record_dir is not None:
                score_shapes.append(save_score(record_dir, step_index, outputs.logits))

    # ---------- 输出结果与元数据 ----------
    # [Qwen] 将生成的 token id 解码为文本，并保存完整元数据供 FPGA 验证对照
    response = tokenizer.decode(generated_ids, skip_special_tokens=True)
    generated_tokens = tokenizer.convert_ids_to_tokens(generated_ids)
    metadata = {
        "model_path": args.model_path,
        "record_dir": str(record_dir) if record_dir else None,
        "prompt": args.prompt,
        "messages": messages,
        "chat_text": chat_text,
        "input_token_count": int(input_ids.shape[1]),  # 输入 prompt 的 token 数
        "input_ids": input_ids[0].detach().cpu().tolist(),  # 完整输入 token id 列表
        "generated_token_count": len(generated_ids),  # 生成的 token 数
        "generated_ids": generated_ids,  # 生成的 token id 列表
        "generated_tokens": generated_tokens,  # 生成的 token 文本
        "response": response,  # 最终解码的回复文本
        "score_shapes": score_shapes,  # 每步 logits shape 记录
        "decode_mode": f"manual greedy argmax max_new_tokens={args.max_new_tokens} use_cache=True",
    }
    # 将元数据写入 JSON 文件
    if record_dir is not None:
        (record_dir / "manual_prefill_decode_metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
