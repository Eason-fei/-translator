import json
import os
import sys
import threading
import time
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory
import requests


app = Flask(__name__)
BASE_DIR = Path(__file__).parent


def data_dir():
    """数据目录：开发模式用项目 data/，打包后用 ~/Library/Application Support"""
    if getattr(sys, "frozen", False):
        p = Path.home() / "Library" / "Application Support" / "Translator"
    else:
        p = BASE_DIR / "data"
    p.mkdir(parents=True, exist_ok=True)
    return p


DATA_DIR = data_dir()

# 加载同步配置
_sync_config_path = BASE_DIR / "sync.json"
GITHUB_REPO = ""
GITHUB_BRANCH = "main"
if _sync_config_path.exists():
    try:
        _sc = json.loads(_sync_config_path.read_text(encoding="utf-8"))
        GITHUB_REPO = _sc.get("github_repo", "")
        GITHUB_BRANCH = _sc.get("branch", "main")
    except Exception:
        pass


def _load_prompts():
    """加载 prompt：优先使用从 GitHub 同步来的版本"""
    synced = DATA_DIR / "prompts.py"
    if synced.exists():
        import importlib.util
        spec = importlib.util.spec_from_file_location("_prompts_synced", synced)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.SYSTEM_PROMPT, mod.build_translate_prompt

    # 兜底：尝试导入项目自带的
    try:
        from prompts import SYSTEM_PROMPT as sp, build_translate_prompt as btp
        return sp, btp
    except ImportError:
        return "", lambda s, t: ""


def sync_prompts():
    """启动时从 GitHub 拉取最新 prompts.py（静默失败）"""
    if not GITHUB_REPO:
        return
    try:
        url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/prompts.py"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            dest = DATA_DIR / "prompts.py"
            dest.write_text(r.text, encoding="utf-8")
    except Exception:
        pass


def check_and_update():
    """启动时检查 GitHub 是否有新版本，有则更新 app.py / index.html 并重启"""
    if not GITHUB_REPO:
        return
    updated = False
    for filename in ("app.py", "index.html"):
        url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{filename}"
        try:
            r = requests.get(url, timeout=15)
            if r.status_code != 200:
                continue
            local = BASE_DIR / filename
            if not local.exists():
                continue
            if r.text.strip() == local.read_text(encoding="utf-8").strip():
                continue
            # 备份 → 写新版 → 标记重启
            backup = local.with_suffix(local.suffix + ".bak")
            local.rename(backup)
            local.write_text(r.text, encoding="utf-8")
            # 语法校验（只对 Python 文件）
            if filename.endswith(".py"):
                try:
                    import ast
                    ast.parse(r.text)
                except SyntaxError:
                    # 语法错误，回滚
                    backup.rename(local)
                    continue
            updated = True
        except Exception:
            pass
    if updated:
        print("[Hermes-Linguist] 代码已更新，正在重启...")
        os.execv(sys.executable, [sys.executable] + sys.argv)


def log_translation(source_lang, target_lang, input_text, output_text, provider_name, is_image=False):
    """记录翻译历史到 data/translations.jsonl（保留 3 个月）"""
    entry = {
        "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "source_lang": source_lang,
        "target_lang": target_lang,
        "input": input_text[:500] if is_image else input_text,
        "output": output_text[:2000],
        "provider": provider_name,
        "is_image": is_image,
    }
    try:
        log_path = DATA_DIR / "translations.jsonl"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        # 清理 3 个月前的数据
        _prune_translations(log_path)
    except OSError:
        pass


def _prune_translations(filepath):
    """删除 3 个月前的数据（概率触发，避免每次都扫）"""
    if time.time() % 50 > 1:  # ~2% 概率
        return
    cutoff = time.time() - 90 * 24 * 3600
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        kept = []
        for line in lines:
            try:
                t = json.loads(line).get("time", "")
                if t >= time.strftime("%Y-%m-%d", time.localtime(cutoff)):
                    kept.append(line)
            except Exception:
                kept.append(line)
        if len(kept) < len(lines):
            with open(filepath, "w", encoding="utf-8") as f:
                f.writelines(kept)
    except Exception:
        pass


def resource_path(relative_path):
    """获取资源路径（开发模式 / PyInstaller 打包后）"""
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(BASE_DIR, relative_path)


# 加载配置 & prompt（启动时从 GitHub 同步最新版）
SYSTEM_PROMPT, build_translate_prompt = _load_prompts()
sync_prompts()  # 异步拉取最新 prompts.py

with open(resource_path("languages.json"), encoding="utf-8") as f:
    LANGUAGES = json.load(f)

with open(resource_path("providers.json"), encoding="utf-8") as f:
    PROVIDERS = json.load(f)


@app.route("/")
def index():
    return send_from_directory(resource_path("."), "index.html")


@app.route("/api/languages")
def get_languages():
    return jsonify(LANGUAGES)


@app.route("/api/providers")
def get_providers():
    """返回 provider 元数据（不暴露 api_key_header 等内部字段）"""
    safe = {}
    for pid, p in PROVIDERS.items():
        safe[pid] = {
            "name": p["name"],
            "model": p["model"],
            "supports_vision": p["supports_vision"],
            "region": p["region"],
            "recommended_for": p["recommended_for"],
        }
    return jsonify(safe)


@app.route("/api/translate", methods=["POST"])
def translate():
    data = request.json or {}
    provider_id = data.get("provider")
    api_key = data.get("api_key", "").strip()
    text = data.get("text", "").strip()
    image_b64 = data.get("image")  # base64
    source_lang_code = data.get("source_lang", "zh")
    target_lang_code = data.get("target_lang", "en-US")

    if not provider_id or provider_id not in PROVIDERS:
        return jsonify({"error": f"未知 Provider: {provider_id}"}), 400
    if not api_key:
        return jsonify({"error": "未提供 API Key"}), 400
    if not text and not image_b64:
        return jsonify({"error": "请输入文本或上传图片"}), 400

    provider = PROVIDERS[provider_id]
    source_name = LANGUAGES.get(source_lang_code, {}).get("name", source_lang_code)
    target_name = LANGUAGES.get(target_lang_code, {}).get("name", target_lang_code)

    # 构建 messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if image_b64:
        if not provider["supports_vision"]:
            return jsonify({"error": f"{provider['name']} 不支持图片翻译"}), 400

        if provider_id == "gemini":
            return _translate_gemini(provider, api_key, image_b64, source_name, target_name)
        elif provider_id == "claude":
            return _translate_claude(provider, api_key, image_b64, source_name, target_name)
        else:
            # OpenAI 兼容格式（DeepSeek 无 vision，不会走到这里）
            user_content = [
                {"type": "text", "text": build_translate_prompt(source_name, target_name)},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
            ]
            messages.append({"role": "user", "content": user_content})
    else:
        user_prompt = build_translate_prompt(source_name, target_name) + f"\n\n{text}"
        messages.append({"role": "user", "content": user_prompt})

    return _translate_openai_compatible(provider, api_key, messages, source_name, target_name,
                                        text, is_image=bool(image_b64))


@app.route("/api/feedback", methods=["POST"])
def save_feedback():
    """收集翻译质量反馈，一行一条 JSON，写入 feedback/ 目录"""
    data = request.json or {}
    rating = data.get("rating")  # "good" | "bad"
    source_lang = data.get("source_lang", "")
    target_lang = data.get("target_lang", "")
    input_text = data.get("input", "")
    output_text = data.get("output", "")
    device_id = data.get("device_id", "unknown")
    provider = data.get("provider", "")
    note = data.get("note", "")

    if rating not in ("good", "bad"):
        return jsonify({"error": "rating 必须是 good 或 bad"}), 400

    entry = {
        "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "rating": rating,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "input": input_text,
        "output": output_text,
        "provider": provider,
        "note": note,
    }

    # 写入 data/feedback/<device_id>.jsonl
    feedback_dir = DATA_DIR / "feedback"
    feedback_dir.mkdir(exist_ok=True)
    filepath = feedback_dir / f"{device_id}.jsonl"

    try:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return jsonify({"ok": True})
    except OSError as e:
        return jsonify({"error": f"写入失败: {e}"}), 500


# ─── Provider 适配器 ───────────────────────────────────────────


def _translate_openai_compatible(provider, api_key, messages, source_name="", target_name="", input_text="", is_image=False):
    """OpenAI 兼容 API：DeepSeek / 智谱 / 通义千问 / Kimi / 豆包 / OpenAI / Grok / Mistral"""
    headers = {"Content-Type": "application/json"}
    if provider["api_key_header"]:
        headers[provider["api_key_header"]] = f"{provider['api_key_prefix']}{api_key}"

    body = {
        "model": provider["model"],
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 4096,
    }

    try:
        resp = requests.post(provider["api_base"], headers=headers, json=body, timeout=60)
    except requests.RequestException as e:
        return jsonify({"error": f"网络错误: {e}"}), 502

    if resp.status_code != 200:
        return jsonify({"error": f"API 错误 ({resp.status_code})", "detail": resp.text[:500]}), 502

    result = resp.json()
    translation = result["choices"][0]["message"]["content"].strip()
    log_translation(source_name, target_name, input_text, translation, provider["name"], is_image)
    return jsonify({"translation": translation, "provider": provider["name"], "model": provider["model"]})


def _translate_gemini(provider, api_key, image_b64, source_name, target_name):
    """Gemini 专有 API"""
    url = f"{provider['api_base']}?key={api_key}"
    body = {
        "contents": [
            {
                "parts": [
                    {"text": f"{SYSTEM_PROMPT}\n\n{build_translate_prompt(source_name, target_name)}"},
                    {"inline_data": {"mime_type": "image/png", "data": image_b64}},
                ]
            }
        ]
    }
    try:
        resp = requests.post(url, json=body, timeout=60)
    except requests.RequestException as e:
        return jsonify({"error": f"网络错误: {e}"}), 502

    if resp.status_code != 200:
        return jsonify({"error": f"Gemini API 错误 ({resp.status_code})", "detail": resp.text[:500]}), 502

    result = resp.json()
    translation = result["candidates"][0]["content"]["parts"][0]["text"].strip()
    log_translation(source_name, target_name, "[图片]", translation, provider["name"], is_image=True)
    return jsonify({"translation": translation, "provider": provider["name"], "model": provider["model"]})


def _translate_claude(provider, api_key, image_b64, source_name, target_name):
    """Anthropic Claude Messages API"""
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
    }
    user_content = [
        {"type": "text", "text": build_translate_prompt(source_name, target_name)},
        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_b64}},
    ]
    body = {
        "model": provider["model"],
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_content}],
        "max_tokens": 4096,
    }
    try:
        resp = requests.post(provider["api_base"], headers=headers, json=body, timeout=60)
    except requests.RequestException as e:
        return jsonify({"error": f"网络错误: {e}"}), 502

    if resp.status_code != 200:
        return jsonify({"error": f"Claude API 错误 ({resp.status_code})", "detail": resp.text[:500]}), 502

    result = resp.json()
    translation = result["content"][0]["text"].strip()
    log_translation(source_name, target_name, "[图片]", translation, provider["name"], is_image=True)
    return jsonify({"translation": translation, "provider": provider["name"], "model": provider["model"]})


# ─── 启动 ──────────────────────────────────────────────────────


def open_browser():
    time.sleep(1)
    import webbrowser
    webbrowser.open("http://127.0.0.1:58958")


if __name__ == "__main__":
    check_and_update()  # 先检查代码更新，有新版则自动重启
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host="127.0.0.1", port=58958, debug=False)
