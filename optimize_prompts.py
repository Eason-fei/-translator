#!/usr/bin/env python3
"""
Hermes-Linguist 每周自动优化大脑
运行时：每周日凌晨 3:00（由 cron 触发）
功能：
  1. 读取所有设备的反馈数据
  2. 筛选最近一周的差评样本
  3. 调用 LLM 分析差评规律，优化 SYSTEM_PROMPT
  4. 备份旧版 → 写入新版 → git commit + push → 所有设备下次启动自动同步
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import requests

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
FEEDBACK_DIR = DATA_DIR / "feedback"
PROMPTS_FILE = BASE_DIR / "prompts.py"
BACKUP_DIR = DATA_DIR / "prompt_backups"
OPTIMIZATION_LOG = DATA_DIR / "optimizations.jsonl"

MIN_BAD_SAMPLES = 5  # 最少差评数才触发优化
SYNC_CONFIG_PATH = BASE_DIR / "sync.json"


def load_sync_config():
    if SYNC_CONFIG_PATH.exists():
        try:
            return json.loads(SYNC_CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def load_env_api_key():
    """从 .env 加载 API Key"""
    env_paths = [
        BASE_DIR / ".env",
        Path.home() / ".hermes" / ".env",
        Path.home() / ".hermes" / "profiles" / "fanyi" / ".env",
    ]
    for env_path in env_paths:
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("DASHSCOPE_API_KEY="):
                    return line.split("=", 1)[1]
                if line.startswith("DEEPSEEK_API_KEY="):
                    return line.split("=", 1)[1]
    return None


def load_feedback_this_week():
    """加载最近一周所有设备的差评反馈"""
    feedbacks = []
    cutoff = datetime.now() - timedelta(days=7)
    if not FEEDBACK_DIR.exists():
        return feedbacks
    for f in sorted(FEEDBACK_DIR.glob("*.jsonl")):
        device_id = f.stem
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                t = datetime.strptime(entry.get("time", "")[:19], "%Y-%m-%dT%H:%M:%S")
                if t >= cutoff and entry.get("rating") == "bad":
                    entry["device_id"] = device_id
                    feedbacks.append(entry)
            except (ValueError, KeyError):
                continue
    return feedbacks


def build_optimization_prompt(feedbacks, current_prompt):
    """构建发送给 LLM 的优化 prompt"""
    samples_text = ""
    for i, fb in enumerate(feedbacks[:20]):
        samples_text += (
            f"\n--- 差评 #{i+1} ---\n"
            f"语种: {fb.get('source_lang', '?')} -> {fb.get('target_lang', '?')}\n"
            f"原文: {fb.get('input', '')[:300]}\n"
            f"译文: {fb.get('output', '')[:500]}\n"
            f"备注: {fb.get('note', '无')}\n"
        )
    return f"""你是翻译系统优化专家。以下是用户最近一周对翻译结果的差评样本和当前翻译 prompt。

## 当前翻译 Prompt
```
{current_prompt}
```

## 差评样本（共 {len(feedbacks)} 条）
{samples_text}

## 任务
分析这些差评的规律和模式，找出当前 prompt 的不足，然后输出优化后的完整 SYSTEM_PROMPT。

规则：
1. 不要改动 ROOT DIRECTIVE 的核心框架
2. 不要改动「保护规则」（代码/HTML/SKU 保护）
3. 重点优化「翻译执行流程」7步管线和「关键规则」的细则
4. 如果差评集中在某个语种对，可在关键规则中增加针对性指令
5. 每次优化控制在 2-3 处改动，不要大改
6. 输出格式：只输出优化后的 SYSTEM_PROMPT 全文，用 ```python 包裹

只输出代码，不要解释。"""


def call_llm(prompt_text):
    """调用 LLM 生成优化后的 prompt"""
    api_key = load_env_api_key()
    if not api_key:
        print("[ERROR] 未找到 API Key")
        return None
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {
        "model": "qwen-plus",
        "messages": [
            {"role": "system", "content": "你是翻译系统优化专家。只输出代码，不输出解释。"},
            {"role": "user", "content": prompt_text},
        ],
        "temperature": 0.3,
        "max_tokens": 4096,
    }
    try:
        r = requests.post(url, headers=headers, json=body, timeout=120)
        if r.status_code == 200:
            content = r.json()["choices"][0]["message"]["content"]
            return extract_python_code(content)
        else:
            print(f"[ERROR] LLM 调用失败: {r.status_code} {r.text[:300]}")
            return None
    except Exception as e:
        print(f"[ERROR] LLM 网络错误: {e}")
        return None


def extract_python_code(text):
    """从 LLM 回复中提取 Python 代码"""
    if "```python" in text:
        parts = text.split("```python", 1)[1].split("```", 1)
        return parts[0].strip()
    if "```" in text:
        parts = text.split("```", 1)[1].split("```", 1)
        return parts[0].strip()
    if "SYSTEM_PROMPT" in text and '"""' in text:
        return text.strip()
    return None


def backup_current_prompt():
    """备份当前 prompts.py"""
    if not PROMPTS_FILE.exists():
        return None
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"prompts_{ts}.py"
    backup_path.write_text(PROMPTS_FILE.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def write_optimized_prompt(new_prompt):
    """写入优化后的 prompts.py"""
    current = PROMPTS_FILE.read_text(encoding="utf-8")
    # 替换 SYSTEM_PROMPT = """ ... """ 之间的内容
    marker = 'SYSTEM_PROMPT = """'
    if marker in current:
        start = current.index(marker) + len(marker)
        # 找闭合的 """
        end = current.index('"""', start)
        new_content = current[:start] + "\n" + new_prompt + "\n" + current[end:]
        PROMPTS_FILE.write_text(new_content, encoding="utf-8")
        return True
    print("[WARN] 未找到 SYSTEM_PROMPT 定义")
    return False


def git_commit_and_push(sync_config):
    """Git commit + push"""
    import subprocess
    repo = sync_config.get("github_repo", "")
    branch = sync_config.get("branch", "main")
    if not repo:
        print("[SKIP] 未配置 github_repo")
        return False
    try:
        subprocess.run(["git", "add", "prompts.py"], cwd=BASE_DIR, capture_output=True, timeout=10)
        subprocess.run(["git", "add", "data/optimizations.jsonl"], cwd=BASE_DIR, capture_output=True, timeout=10)
        msg = f"auto: optimize prompts ({len(load_feedback_this_week())} bad samples this week)"
        subprocess.run(["git", "commit", "-m", msg], cwd=BASE_DIR, capture_output=True, timeout=10)
        subprocess.run(["git", "push", "origin", branch], cwd=BASE_DIR, capture_output=True, timeout=30)
        return True
    except Exception as e:
        print(f"[ERROR] Git 操作失败: {e}")
        return False


def log_optimization(sample_count, backup_path, success):
    """记录优化日志"""
    OPTIMIZATION_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "time": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "bad_samples": sample_count,
        "backup": str(backup_path) if backup_path else None,
        "success": success,
    }
    with open(OPTIMIZATION_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main():
    print(f"[{datetime.now():%Y-%m-%d %H:%M}] 优化大脑启动")
    feedbacks = load_feedback_this_week()
    print(f"  本周差评: {len(feedbacks)} 条")
    if len(feedbacks) < MIN_BAD_SAMPLES:
        print(f"  不足 {MIN_BAD_SAMPLES} 条，跳过")
        return
    current_prompt = PROMPTS_FILE.read_text(encoding="utf-8")
    print(f"  当前 prompt: {len(current_prompt)} 字符")
    print("  正在分析差评规律...")
    optimization_prompt = build_optimization_prompt(feedbacks, current_prompt)
    new_prompt = call_llm(optimization_prompt)
    if not new_prompt:
        print("[ERROR] LLM 未返回有效结果")
        log_optimization(len(feedbacks), None, False)
        return
    print(f"  优化后 prompt: {len(new_prompt)} 字符")
    backup_path = backup_current_prompt()
    print(f"  已备份: {backup_path}")
    if write_optimized_prompt(new_prompt):
        print("  已写入新版 prompts.py")
    else:
        log_optimization(len(feedbacks), backup_path, False)
        return
    sync_config = load_sync_config()
    if git_commit_and_push(sync_config):
        print("  已推送 -> 所有设备下次启动自动同步")
    else:
        print("  本地已更新，请手动 git push")
    log_optimization(len(feedbacks), backup_path, True)
    print("[DONE]")


if __name__ == "__main__":
    main()
