# 翻译网站 实现计划

> **面向 AI 代理的工作者：** 使用 subagent-driven-development 或 executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法跟踪进度。

**目标：** 构建一个本地运行的 Web 翻译工具，支持 10 个 LLM Provider + 10+ 语种的文本和图片翻译。

**架构：** Flask 单文件后端内嵌前端，后端做 API 代理转发到各 LLM API，前端纯 HTML/CSS/JS。Provider/语种通过 JSON 配置文件管理。

**技术栈：** Python 3 + Flask + requests + Pillow，前端零框架。

---

### 任务 1：项目脚手架

**文件：**
- 创建：`translator/requirements.txt`
- 创建：`translator/.gitignore`

- [ ] **步骤 1：创建 requirements.txt**

```
flask>=3.0
requests>=2.31
Pillow>=10.0
pyinstaller>=6.0
```

- [ ] **步骤 2：创建 .gitignore**

```
__pycache__/
*.pyc
dist/
build/
*.spec
.superpowers/
*.app
.DS_Store
```

- [ ] **步骤 3：安装依赖**

```bash
cd /Users/eason/translator && pip install -r requirements.txt
```
预期：所有包安装成功。

---

### 任务 2：配置文件

**文件：**
- 创建：`translator/languages.json`
- 创建：`translator/providers.json`

- [ ] **步骤 1：创建 languages.json**

```json
{
  "zh": {"name": "中文", "name_en": "Chinese"},
  "en-US": {"name": "English (US)", "name_en": "English (US)"},
  "en-GB": {"name": "English (UK)", "name_en": "English (UK)"},
  "de": {"name": "Deutsch", "name_en": "German"},
  "fr": {"name": "Français", "name_en": "French"},
  "es": {"name": "Español", "name_en": "Spanish"},
  "pt": {"name": "Português", "name_en": "Portuguese"},
  "pl": {"name": "Polski", "name_en": "Polish"},
  "ja": {"name": "日本語", "name_en": "Japanese"},
  "ko": {"name": "한국어", "name_en": "Korean"},
  "yue": {"name": "粵語", "name_en": "Cantonese"}
}
```

- [ ] **步骤 2：创建 providers.json**

```json
{
  "deepseek": {
    "name": "DeepSeek",
    "model": "deepseek-chat",
    "api_base": "https://api.deepseek.com/v1/chat/completions",
    "api_key_header": "Authorization",
    "api_key_prefix": "Bearer ",
    "supports_vision": false,
    "region": "china",
    "recommended_for": "text"
  },
  "zhipu": {
    "name": "智谱 GLM",
    "model": "glm-4v-flash",
    "api_base": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
    "api_key_header": "Authorization",
    "api_key_prefix": "Bearer ",
    "supports_vision": true,
    "region": "china",
    "recommended_for": "image"
  },
  "qwen": {
    "name": "通义千问",
    "model": "qwen-vl-plus",
    "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    "api_key_header": "Authorization",
    "api_key_prefix": "Bearer ",
    "supports_vision": true,
    "region": "china",
    "recommended_for": null
  },
  "kimi": {
    "name": "月之暗面 Kimi",
    "model": "moonshot-v1-8k",
    "api_base": "https://api.moonshot.cn/v1/chat/completions",
    "api_key_header": "Authorization",
    "api_key_prefix": "Bearer ",
    "supports_vision": true,
    "region": "china",
    "recommended_for": null
  },
  "doubao": {
    "name": "字节豆包",
    "model": "doubao-1.5-vision-pro-32k",
    "api_base": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
    "api_key_header": "Authorization",
    "api_key_prefix": "Bearer ",
    "supports_vision": true,
    "region": "china",
    "recommended_for": null
  },
  "openai": {
    "name": "OpenAI",
    "model": "gpt-4o",
    "api_base": "https://api.openai.com/v1/chat/completions",
    "api_key_header": "Authorization",
    "api_key_prefix": "Bearer ",
    "supports_vision": true,
    "region": "overseas",
    "recommended_for": null
  },
  "claude": {
    "name": "Anthropic Claude",
    "model": "claude-3-5-sonnet-20241022",
    "api_base": "https://api.anthropic.com/v1/messages",
    "api_key_header": "x-api-key",
    "api_key_prefix": "",
    "supports_vision": true,
    "region": "overseas",
    "recommended_for": null
  },
  "gemini": {
    "name": "Google Gemini",
    "model": "gemini-2.5-flash",
    "api_base": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
    "api_key_header": "",
    "api_key_prefix": "",
    "supports_vision": true,
    "region": "overseas",
    "recommended_for": null
  },
  "grok": {
    "name": "xAI Grok",
    "model": "grok-2-vision-1212",
    "api_base": "https://api.x.ai/v1/chat/completions",
    "api_key_header": "Authorization",
    "api_key_prefix": "Bearer ",
    "supports_vision": true,
    "region": "overseas",
    "recommended_for": null
  },
  "mistral": {
    "name": "Mistral",
    "model": "pixtral-12b-2409",
    "api_base": "https://api.mistral.ai/v1/chat/completions",
    "api_key_header": "Authorization",
    "api_key_prefix": "Bearer ",
    "supports_vision": true,
    "region": "overseas",
    "recommended_for": null
  }
}
```

---

### 任务 3：翻译 Prompt 模板

**文件：**
- 创建：`translator/prompts.py`

- [ ] **步骤 1：创建 prompts.py**

```python
"""soul.md 翻译 prompt 模板"""

SYSTEM_PROMPT = """你是一个高级跨语言翻译引擎——Hermes-Linguist。

## ROOT DIRECTIVE（最高优先级）
你的核心目标不是"翻译文字"，而是生成"目标语言母语者真实会使用的自然表达"。
在保持真实语义、语气与文化意图的前提下，动态平衡：准确性、自然度、本地化、可读性、沟通效率。

绝不能：
- 为流畅牺牲关键语义
- 为准确变成机械翻译
- 为礼貌变成 AI 腔
- 为直译破坏文化语境

## 翻译执行流程
每次翻译按以下步骤执行：
1. 解析真实语义、潜台词与说话者意图
2. 判断行业语境、双方关系、礼貌等级与社交距离
3. 识别文化负载词（成语、梗、双关、隐喻、网络流行语等）
4. 重构目标语言中的本地化、自然表达
5. 优化 Human-to-Human 沟通感、简洁性与可读性
6. 彻底清除 AI腔、翻译腔、中式逻辑残留
7. 执行 Native Authenticity Test（母语者真实性最终校验）

## 关键规则
- 社交适配：动态识别正式/半正式/客服/朋友/社交媒体等关系，自动调整礼貌度和正式度
- 文化负载词：禁止机械直译，使用本地等效表达
- 电商黑话禁止直译：爆款→best seller，亲/宝贝→根据关系转为自然称呼
- AI腔过滤器：严禁"Hope this email finds you well"、utilize、delve 等表达
- 金融/法律/医疗：先确保术语 100% 准确合规，再优化自然度
- 防过度润色：原文已自然清晰时，禁止无意义改写

## 保护规则
- 代码、HTML、JSON、SKU、占位符：完全保护，不翻译不改写
- 专有名词：优先官方译名或当地通用名称

## 输出规则
仅输出译文。不要任何解释、不要 Markdown 格式、不要客套文字。"""


def build_translate_prompt(source_lang, target_lang):
    """构建 user prompt"""
    return f"将以下文本从{source_lang}翻译成{target_lang}："
```

---

### 任务 4：Flask 主程序

**文件：**
- 创建：`translator/app.py`

- [ ] **步骤 1：创建 app.py — 基础结构和路由**

```python
import json
import base64
import io
import os
import webbrowser
import threading
import time
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory
from PIL import Image
import requests

from prompts import SYSTEM_PROMPT, build_translate_prompt

app = Flask(__name__, static_folder="static", template_folder="templates")

BASE_DIR = Path(__file__).parent

# 加载配置
with open(BASE_DIR / "languages.json") as f:
    LANGUAGES = json.load(f)

with open(BASE_DIR / "providers.json") as f:
    PROVIDERS = json.load(f)


@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/api/languages")
def get_languages():
    return jsonify(LANGUAGES)


@app.route("/api/providers")
def get_providers():
    # 返回 provider 列表，但不暴露 api_key_header 细节
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
    data = request.json
    provider_id = data.get("provider")
    api_key = data.get("api_key")
    text = data.get("text", "")
    image_b64 = data.get("image")  # base64 encoded image
    source_lang_code = data.get("source_lang", "zh")
    target_lang_code = data.get("target_lang", "en-US")

    if provider_id not in PROVIDERS:
        return jsonify({"error": f"Unknown provider: {provider_id}"}), 400

    provider = PROVIDERS[provider_id]
    source_name = LANGUAGES.get(source_lang_code, {}).get("name", source_lang_code)
    target_name = LANGUAGES.get(target_lang_code, {}).get("name", target_lang_code)

    # 构建 messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if image_b64:
        # 图片翻译：使用 vision
        if not provider["supports_vision"]:
            return jsonify({"error": f"{provider['name']} does not support vision"}), 400

        if provider_id == "gemini":
            return _translate_gemini(provider, api_key, image_b64, source_name, target_name)
        elif provider_id == "claude":
            return _translate_claude(provider, api_key, image_b64, source_name, target_name, messages)
        else:
            # OpenAI 兼容格式
            user_content = [
                {"type": "text", "text": build_translate_prompt(source_name, target_name)},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
            ]
            messages.append({"role": "user", "content": user_content})
    else:
        # 纯文本翻译
        user_prompt = build_translate_prompt(source_name, target_name) + f"\n\n{text}"
        messages.append({"role": "user", "content": user_prompt})

    return _translate_openai_compatible(provider, api_key, messages)


def _translate_openai_compatible(provider, api_key, messages):
    """OpenAI 兼容 API（DeepSeek, 智谱, 通义千问, Kimi, 豆包, OpenAI, Grok, Mistral）"""
    headers = {}
    if provider["api_key_header"]:
        headers[provider["api_key_header"]] = f"{provider['api_key_prefix']}{api_key}"
    headers["Content-Type"] = "application/json"

    body = {
        "model": provider["model"],
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 4096,
    }

    resp = requests.post(provider["api_base"], headers=headers, json=body, timeout=60)
    if resp.status_code != 200:
        return jsonify({"error": f"API error: {resp.status_code}", "detail": resp.text[:500]}), 502

    result = resp.json()
    translation = result["choices"][0]["message"]["content"].strip()
    return jsonify({"translation": translation, "provider": provider["name"], "model": provider["model"]})


def _translate_gemini(provider, api_key, image_b64, source_name, target_name):
    """Gemini 专有 API"""
    url = f"{provider['api_base']}?key={api_key}"
    body = {
        "contents": [{
            "parts": [
                {"text": f"{SYSTEM_PROMPT}\n\n{build_translate_prompt(source_name, target_name)}"},
                {"inline_data": {"mime_type": "image/png", "data": image_b64}}
            ]
        }]
    }
    resp = requests.post(url, json=body, timeout=60)
    if resp.status_code != 200:
        return jsonify({"error": f"Gemini API error: {resp.status_code}", "detail": resp.text[:500]}), 502

    result = resp.json()
    translation = result["candidates"][0]["content"]["parts"][0]["text"].strip()
    return jsonify({"translation": translation, "provider": provider["name"], "model": provider["model"]})


def _translate_claude(provider, api_key, image_b64, source_name, target_name, messages):
    """Anthropic Claude 专有 API（Messages API，vision 用不同格式）"""
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
    }

    user_content = [
        {"type": "text", "text": build_translate_prompt(source_name, target_name)},
        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_b64}}
    ]

    body = {
        "model": provider["model"],
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_content}],
        "max_tokens": 4096,
    }

    resp = requests.post(provider["api_base"], headers=headers, json=body, timeout=60)
    if resp.status_code != 200:
        return jsonify({"error": f"Claude API error: {resp.status_code}", "detail": resp.text[:500]}), 502

    result = resp.json()
    translation = result["content"][0]["text"].strip()
    return jsonify({"translation": translation, "provider": provider["name"], "model": provider["model"]})


def open_browser():
    """延迟打开浏览器"""
    time.sleep(1)
    webbrowser.open("http://127.0.0.1:58958")


if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host="127.0.0.1", port=58958, debug=False)
```

---

### 任务 5：前端 index.html

**文件：**
- 创建：`translator/index.html`

- [ ] **步骤 1：创建 index.html（完整页面结构）**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>翻译器 · Translator · Tłumacz</title>
<style>
/* CSS 将在 任务 5 中内联写入 */
</style>
</head>
<body>
  <div class="app">
    <!-- 顶部栏 -->
    <header class="header">
      <h1 class="logo">🌐 翻译器</h1>
      <button id="settingsBtn" class="icon-btn" title="设置 API Key">⚙️</button>
    </header>

    <!-- 翻译区域 -->
    <main class="main">
      <!-- 语言和模型选择 -->
      <div class="selectors">
        <div class="selector-group">
          <label>源语言</label>
          <select id="sourceLang"></select>
        </div>
        <button id="swapBtn" class="swap-btn" title="交换语言">⇄</button>
        <div class="selector-group">
          <label>目标语言</label>
          <select id="targetLang"></select>
        </div>
        <div class="selector-group">
          <label>模型</label>
          <select id="modelSelect"></select>
        </div>
      </div>

      <!-- 输入输出区域 -->
      <div class="panels">
        <div class="panel panel-input" id="inputPanel">
          <textarea id="inputText" placeholder="输入文本 · 拖拽图片 · Cmd+V 粘贴"></textarea>
          <div class="image-preview" id="imagePreview" style="display:none">
            <img id="previewImg" src="" alt="预览">
            <button id="removeImage" class="remove-btn">✕</button>
          </div>
        </div>
        <div class="panel panel-output">
          <div class="output-header">
            <span class="output-label">翻译结果</span>
            <button id="copyBtn" class="copy-btn" title="复制">📋</button>
          </div>
          <div id="outputText" class="output-content" contenteditable="true">翻译结果将显示在这里...</div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="actions">
        <button id="translateBtn" class="primary-btn">翻译</button>
        <span class="or-text">或</span>
        <label class="upload-label">
          📎 上传图片
          <input type="file" id="imageInput" accept="image/*" hidden>
        </label>
      </div>
    </main>

    <!-- 设置弹窗 -->
    <div id="settingsModal" class="modal" style="display:none">
      <div class="modal-content">
        <div class="modal-header">
          <h2>⚙️ API 设置</h2>
          <button id="closeSettings" class="close-btn">✕</button>
        </div>
        <div class="modal-body" id="settingsBody">
          <!-- 动态生成 -->
        </div>
        <div class="modal-footer">
          <button id="saveSettings" class="primary-btn">保存</button>
        </div>
      </div>
    </div>
  </div>

<script>
// JavaScript 将在 任务 6 中内联写入
</script>
</body>
</html>
```

---

### 任务 6：前端 CSS

**文件：**
- 修改：`translator/index.html` — 在 `<style>` 标签内写入完整 CSS

- [ ] **步骤 1：写入 CSS**

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #0d1117;
  --bg-panel: #161b22;
  --border: #30363d;
  --text: #c9d1d9;
  --text-muted: #8b949e;
  --accent: #58a6ff;
  --accent-hover: #79c0ff;
  --gold: #f0c040;
  --green: #3fb950;
  --red: #f85149;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  display: flex;
  justify-content: center;
}

.app { width: 100%; max-width: 1000px; padding: 20px; }

.header {
  display: flex; justify-content: space-between; align-items: center;
  padding-bottom: 16px; border-bottom: 1px solid var(--border); margin-bottom: 20px;
}
.logo { font-size: 20px; font-weight: 600; }
.icon-btn {
  background: none; border: 1px solid var(--border); color: var(--text);
  font-size: 18px; padding: 6px 10px; border-radius: 6px; cursor: pointer;
}
.icon-btn:hover { background: var(--bg-panel); }

.selectors {
  display: flex; gap: 10px; align-items: flex-end; margin-bottom: 16px; flex-wrap: wrap;
}
.selector-group { flex: 1; min-width: 120px; }
.selector-group label {
  display: block; font-size: 11px; color: var(--text-muted);
  text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;
}
.selector-group select, .selector-group select:focus {
  width: 100%; padding: 8px 10px; background: var(--bg-panel);
  border: 1px solid var(--border); color: var(--text); border-radius: 6px;
  font-size: 14px; outline: none;
}
.selector-group select:focus { border-color: var(--accent); }
.swap-btn {
  background: var(--bg-panel); border: 1px solid var(--border);
  color: var(--text); font-size: 18px; padding: 7px 10px;
  border-radius: 6px; cursor: pointer; margin-bottom: 0; height: 38px;
}
.swap-btn:hover { border-color: var(--accent); }

.panels { display: flex; gap: 12px; margin-bottom: 14px; }
.panel { flex: 1; min-height: 200px; }
.panel-input {
  background: var(--bg-panel); border: 1px solid var(--border);
  border-radius: 8px; padding: 12px; position: relative;
}
.panel-input textarea {
  width: 100%; height: 100%; min-height: 180px; background: transparent;
  border: none; color: var(--text); font-size: 15px; resize: vertical;
  outline: none; font-family: inherit; line-height: 1.6;
}
.image-preview { margin-top: 8px; position: relative; display: inline-block; }
.image-preview img { max-width: 100%; max-height: 200px; border-radius: 6px; }
.remove-btn {
  position: absolute; top: -6px; right: -6px;
  width: 22px; height: 22px; border-radius: 50%; border: none;
  background: var(--red); color: white; font-size: 12px; cursor: pointer;
}
.panel-output {
  background: var(--bg-panel); border: 1px solid var(--border);
  border-radius: 8px; padding: 12px; display: flex; flex-direction: column;
}
.output-header {
  display: flex; justify-content: space-between; align-items: center;
  padding-bottom: 8px; border-bottom: 1px solid var(--border); margin-bottom: 8px;
}
.output-label { font-size: 11px; color: var(--text-muted); text-transform: uppercase; }
.copy-btn {
  background: none; border: none; color: var(--text-muted);
  font-size: 16px; cursor: pointer;
}
.copy-btn:hover { color: var(--accent); }
.output-content {
  flex: 1; font-size: 15px; line-height: 1.6; color: var(--text);
  white-space: pre-wrap; word-wrap: break-word; outline: none;
  min-height: 160px;
}
.output-content:empty::before {
  content: attr(data-placeholder); color: var(--text-muted);
}

.actions { display: flex; gap: 10px; align-items: center; }
.primary-btn {
  background: var(--accent); color: #fff; border: none;
  padding: 10px 24px; border-radius: 6px; font-size: 15px;
  cursor: pointer; font-weight: 500;
}
.primary-btn:hover { background: var(--accent-hover); }
.or-text { color: var(--text-muted); font-size: 13px; }
.upload-label {
  color: var(--accent); font-size: 14px; cursor: pointer;
}
.upload-label:hover { color: var(--accent-hover); }

/* Modal / Settings */
.modal {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.7); display: flex;
  justify-content: center; align-items: center; z-index: 100;
}
.modal-content {
  background: var(--bg-panel); border: 1px solid var(--border);
  border-radius: 12px; width: 90%; max-width: 650px; max-height: 80vh;
  overflow-y: auto;
}
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px; border-bottom: 1px solid var(--border);
}
.modal-header h2 { font-size: 18px; }
.close-btn {
  background: none; border: none; color: var(--text-muted);
  font-size: 20px; cursor: pointer;
}
.modal-body { padding: 20px; }
.modal-footer { padding: 12px 20px; border-top: 1px solid var(--border); text-align: right; }

.provider-card {
  border: 1px solid var(--border); border-radius: 8px; padding: 14px;
  margin-bottom: 12px;
}
.provider-card .provider-name {
  font-weight: 600; margin-bottom: 6px; display: flex; gap: 8px; align-items: center;
}
.provider-card .provider-tags { font-size: 11px; }
.provider-card input[type="password"], .provider-card input[type="text"] {
  width: 100%; padding: 8px 10px; background: var(--bg);
  border: 1px solid var(--border); color: var(--text);
  border-radius: 6px; font-size: 13px; margin-top: 8px;
}
.tag {
  font-size: 10px; padding: 2px 8px; border-radius: 10px; font-weight: 500;
}
.tag-vision { background: #1a3a1a; color: var(--green); }
.tag-text { background: #1a1a3a; color: var(--accent); }
.tag-china { background: #3a1a1a; color: #f0883e; }
.tag-free { background: #1a3a1a; color: var(--green); }

/* Toast */
.toast {
  position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
  background: var(--green); color: #fff; padding: 10px 24px;
  border-radius: 8px; font-size: 14px; z-index: 200;
  animation: fadeInOut 2s forwards;
}
@keyframes fadeInOut {
  0% { opacity: 0; transform: translateX(-50%) translateY(10px); }
  15% { opacity: 1; transform: translateX(-50%) translateY(0); }
  75% { opacity: 1; }
  100% { opacity: 0; }
}

/* Loading spinner */
.spinner {
  display: inline-block; width: 16px; height: 16px;
  border: 2px solid var(--border); border-top-color: var(--accent);
  border-radius: 50%; animation: spin 0.6s linear infinite; margin-right: 6px;
}
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 700px) {
  .panels { flex-direction: column; }
  .selectors { flex-direction: column; }
}
```

---

### 任务 7：前端 JavaScript

**文件：**
- 修改：`translator/index.html` — 在 `<script>` 标签内写入完整 JS

- [ ] **步骤 1：写入 JavaScript**

```javascript
// ============ 状态 ============
let imageData = null; // base64 string

// ============ DOM 引用 ============
const sourceLangEl = document.getElementById('sourceLang');
const targetLangEl = document.getElementById('targetLang');
const modelSelectEl = document.getElementById('modelSelect');
const inputTextEl = document.getElementById('inputText');
const outputTextEl = document.getElementById('outputText');
const translateBtn = document.getElementById('translateBtn');
const swapBtn = document.getElementById('swapBtn');
const copyBtn = document.getElementById('copyBtn');
const imageInput = document.getElementById('imageInput');
const imagePreview = document.getElementById('imagePreview');
const previewImg = document.getElementById('previewImg');
const removeImageBtn = document.getElementById('removeImage');
const settingsBtn = document.getElementById('settingsBtn');
const settingsModal = document.getElementById('settingsModal');
const closeSettings = document.getElementById('closeSettings');
const saveSettings = document.getElementById('saveSettings');
const settingsBody = document.getElementById('settingsBody');
const inputPanel = document.getElementById('inputPanel');

// ============ 初始化 ============
async function init() {
  await loadLanguages();
  await loadProviders();
  loadSettings();
  updateModelOptions();
  setupEventListeners();
}

async function loadLanguages() {
  try {
    const resp = await fetch('/api/languages');
    const langs = await resp.json();
    sourceLangEl.innerHTML = '';
    targetLangEl.innerHTML = '';
    for (const [code, info] of Object.entries(langs)) {
      const opt1 = new Option(info.name, code);
      const opt2 = new Option(info.name, code);
      sourceLangEl.add(opt1);
      targetLangEl.add(opt2);
    }
    // 默认：中文 → 波兰语
    sourceLangEl.value = 'zh';
    targetLangEl.value = 'pl';
  } catch (e) {
    console.error('Failed to load languages', e);
  }
}

async function loadProviders() {
  try {
    const resp = await fetch('/api/providers');
    const providers = await resp.json();
    window._providers = providers;
  } catch (e) {
    console.error('Failed to load providers', e);
  }
}

function updateModelOptions() {
  const providers = window._providers || {};
  const keys = getApiKeys();
  const hasImage = !!imageData;

  modelSelectEl.innerHTML = '';
  let hasSelected = false;
  for (const [pid, p] of Object.entries(providers)) {
    if (hasImage && !p.supports_vision) continue; // 图片模式隐藏不支持 vision 的

    const hasKey = !!keys[pid];
    const opt = new Option(
      `${p.name} (${p.model})${hasKey ? '' : ' - 未配置 Key'}`,
      pid
    );
    if (!hasKey) opt.disabled = true;
    modelSelectEl.add(opt);
    if (hasKey && !hasSelected) {
      modelSelectEl.value = pid;
      hasSelected = true;
    }
  }
  if (!hasSelected && modelSelectEl.options.length > 0) {
    // 没配置 key，允许选择但会在翻译时报错
  }
}

function getApiKeys() {
  try {
    return JSON.parse(localStorage.getItem('translator_keys') || '{}');
  } catch { return {}; }
}

function saveApiKeys(keys) {
  localStorage.setItem('translator_keys', JSON.stringify(keys));
}

function loadSettings() {
  const keys = getApiKeys();
  const providers = window._providers || {};

  settingsBody.innerHTML = '';
  for (const [pid, p] of Object.entries(providers)) {
    const card = document.createElement('div');
    card.className = 'provider-card';

    let tags = '';
    if (p.recommended_for === 'text') tags += '<span class="tag tag-text">推荐·文本</span>';
    if (p.recommended_for === 'image') tags += '<span class="tag tag-free">推荐·图片</span>';
    if (p.supports_vision) tags += '<span class="tag tag-vision">图片</span>';
    else tags += '<span class="tag tag-text">仅文本</span>';
    if (p.region === 'china') tags += '<span class="tag tag-china">国内直连</span>';

    card.innerHTML = `
      <div class="provider-name">
        ${p.name}
        <span class="provider-tags">${tags}</span>
      </div>
      <div style="font-size:12px;color:var(--text-muted)">${p.model}</div>
      <input type="password" id="key-${pid}" placeholder="输入 API Key..."
             value="${keys[pid] || ''}">
    `;
    settingsBody.appendChild(card);
  }
}

// ============ 事件 ============
function setupEventListeners() {
  translateBtn.addEventListener('click', doTranslate);
  swapBtn.addEventListener('click', swapLanguages);
  copyBtn.addEventListener('click', copyResult);
  settingsBtn.addEventListener('click', () => { settingsModal.style.display = 'flex'; loadSettings(); });
  closeSettings.addEventListener('click', () => { settingsModal.style.display = 'none'; });
  settingsModal.addEventListener('click', (e) => { if (e.target === settingsModal) settingsModal.style.display = 'none'; });
  saveSettings.addEventListener('click', saveSettingsHandler);
  imageInput.addEventListener('change', handleImageUpload);
  removeImageBtn.addEventListener('click', removeImage);

  // 剪贴板粘贴
  document.addEventListener('paste', handlePaste);

  // 拖拽
  inputPanel.addEventListener('dragover', (e) => { e.preventDefault(); });
  inputPanel.addEventListener('drop', handleDrop);

  // 模型切换时刷新选项
  modelSelectEl.addEventListener('focus', updateModelOptions);
}

function swapLanguages() {
  const tmp = sourceLangEl.value;
  sourceLangEl.value = targetLangEl.value;
  targetLangEl.value = tmp;
}

async function copyResult() {
  const text = outputTextEl.innerText;
  await navigator.clipboard.writeText(text);
  showToast('已复制');
}

function handlePaste(e) {
  const items = e.clipboardData?.items;
  if (!items) return;
  for (const item of items) {
    if (item.type.startsWith('image/')) {
      e.preventDefault();
      const file = item.getAsFile();
      processImageFile(file);
      return;
    }
  }
}

function handleDrop(e) {
  e.preventDefault();
  const file = e.dataTransfer?.files?.[0];
  if (file && file.type.startsWith('image/')) {
    processImageFile(file);
  }
}

function handleImageUpload(e) {
  const file = e.target.files?.[0];
  if (file) processImageFile(file);
}

function processImageFile(file) {
  const reader = new FileReader();
  reader.onload = () => {
    imageData = reader.result.split(',')[1]; // remove data:image/...;base64,
    previewImg.src = reader.result;
    imagePreview.style.display = 'inline-block';
    inputTextEl.style.display = 'none';
    updateModelOptions();
  };
  reader.readAsDataURL(file);
}

function removeImage() {
  imageData = null;
  imagePreview.style.display = 'none';
  previewImg.src = '';
  inputTextEl.style.display = '';
  updateModelOptions();
}

function saveSettingsHandler() {
  const providers = window._providers || {};
  const keys = {};
  for (const pid of Object.keys(providers)) {
    const input = document.getElementById(`key-${pid}`);
    if (input && input.value.trim()) {
      keys[pid] = input.value.trim();
    }
  }
  saveApiKeys(keys);
  settingsModal.style.display = 'none';
  updateModelOptions();
  showToast('设置已保存');
}

async function doTranslate() {
  const providerId = modelSelectEl.value;
  const keys = getApiKeys();
  const apiKey = keys[providerId];

  if (!apiKey) {
    showToast('请先在设置中配置该模型的 API Key', true);
    return;
  }

  const text = inputTextEl.value.trim();
  if (!text && !imageData) {
    showToast('请输入文本或上传图片');
    return;
  }

  // 显示加载状态
  translateBtn.disabled = true;
  const origText = translateBtn.textContent;
  translateBtn.innerHTML = '<span class="spinner"></span>翻译中...';
  outputTextEl.innerHTML = '<span style="color:var(--text-muted)">翻译中...</span>';

  try {
    const body = {
      provider: providerId,
      api_key: apiKey,
      source_lang: sourceLangEl.value,
      target_lang: targetLangEl.value,
    };
    if (imageData) {
      body.image = imageData;
    } else {
      body.text = text;
    }

    const resp = await fetch('/api/translate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    const data = await resp.json();
    if (data.error) {
      outputTextEl.textContent = '错误：' + data.error;
    } else {
      outputTextEl.textContent = data.translation;
    }
  } catch (e) {
    outputTextEl.textContent = '网络错误：' + e.message;
  } finally {
    translateBtn.disabled = false;
    translateBtn.textContent = origText;
  }
}

function showToast(msg, isError = false) {
  const toast = document.createElement('div');
  toast.className = 'toast';
  if (isError) toast.style.background = 'var(--red)';
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 2100);
}

// ============ 启动 ============
init();
```

---

### 任务 8：集成测试

- [ ] **步骤 1：启动服务**

```bash
cd /Users/eason/translator && python app.py
```
预期：服务在 http://127.0.0.1:58958 启动，浏览器自动打开。

- [ ] **步骤 2：测试 API 连通性**

```bash
curl http://127.0.0.1:58958/api/languages | python3 -m json.tool
curl http://127.0.0.1:58958/api/providers | python3 -m json.tool
```
预期：返回 languages.json 和 providers.json 的筛选版本。

- [ ] **步骤 3：前端页面检查**

在浏览器中确认：
- 语言下拉框包含全部 11 个语种
- 模型下拉框显示 10 个 Provider
- 设置页每个 Provider 都有 Key 输入框
- 图片拖拽、粘贴、上传均触发预览
- 切换源/目标语言后 ⇄ 按钮正常工作

- [ ] **步骤 4：文本翻译端到端测试**

填入 DeepSeek API Key → 输入"今天天气真好" → 选择中文→波兰语 → 点击翻译
预期：返回波兰语翻译，非逐字翻译，读起来自然。

- [ ] **步骤 5：图片翻译端到端测试**

填入智谱 API Key → 粘贴包含文字的截图 → 选择模型为智谱 → 点击翻译
预期：返回图片中文字的翻译结果。

- [ ] **步骤 6：Provider 切换测试**

切换模型到 OpenAI → 填入 Key → 翻译相同文本
预期：返回翻译结果，prompt 风格一致。

---

### 任务 9：PyInstaller 打包

**文件：**
- 创建：`translator/build.sh`
- 修改：`translator/app.py` — 适配 PyInstaller 打包

- [ ] **步骤 1：修改 app.py 适配打包**

在 `app.py` 中添加 PyInstaller 资源路径处理（在文件开头，import 之后）：

```python
import sys

def resource_path(relative_path):
    """获取打包后的资源文件路径"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = BASE_DIR
    return os.path.join(base_path, relative_path)

# 替换加载配置为：
with open(resource_path("languages.json")) as f:
    LANGUAGES = json.load(f)
with open(resource_path("providers.json")) as f:
    PROVIDERS = json.load(f)

# index.html 路由改为：
@app.route("/")
def index():
    return send_from_directory(resource_path("."), "index.html")
```

- [ ] **步骤 2：创建 build.sh**

```bash
#!/bin/bash
set -e

cd "$(dirname "$0")"

# 清理旧构建
rm -rf build dist *.spec

# PyInstaller 打包
pyinstaller \
  --onefile \
  --windowed \
  --name Translator \
  --add-data "languages.json:." \
  --add-data "providers.json:." \
  --add-data "index.html:." \
  --add-data "prompts.py:." \
  app.py

echo ""
echo "✅ 打包完成: dist/Translator.app"
echo "双击即可运行"
```

- [ ] **步骤 3：执行打包**

```bash
cd /Users/eason/translator && bash build.sh
```
预期：生成 `dist/Translator.app`。

- [ ] **步骤 4：验证打包产物**

```bash
ls -lh /Users/eason/translator/dist/Translator.app
open /Users/eason/translator/dist/Translator.app
```
预期：应用启动 → 浏览器打开 → 页面正常加载 → 翻译功能可用。

---

### 任务 10：README

**文件：**
- 创建：`translator/README.md`

- [ ] **步骤 1：创建 README.md**

```markdown
# 🌐 翻译器 · Translator

本地运行的智能翻译工具，支持 10+ 语种、10 个 LLM Provider 自由切换。

## 功能

- 📝 **文本翻译**：中文、英语、波兰语、日语、韩语等 11 种语言互相翻译
- 🖼️ **图片翻译**：拖拽/粘贴/上传图片，自动识别文字并翻译
- 🤖 **多模型**：DeepSeek、智谱、OpenAI、Claude、Gemini、Grok 等 10 个 Provider 可选
- 🎯 **高质量**：内置 Hermes-Linguist 7 步翻译管线，结果比 Google Translate 更自然
- 📦 **零安装**：打包为独立 .app 文件，双击即用

## 安装

### 方式一：双击运行（推荐）

1. 下载 `Translator.app`
2. 双击打开
3. 在设置页填入你想用的 API Key
4. 开始翻译

### 方式二：源码运行

```bash
pip install -r requirements.txt
python app.py
```

## API Key 获取

| Provider | 获取地址 | 价格 |
|----------|---------|------|
| DeepSeek | platform.deepseek.com | 极低 |
| 智谱 GLM | open.bigmodel.cn | 有免费额度 |
| 通义千问 | dashscope.aliyun.com | 按量 |
| OpenAI | platform.openai.com | 付费 |

## 技术栈

Python + Flask + 纯 HTML/CSS/JS
```
