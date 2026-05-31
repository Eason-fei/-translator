# 🌐 翻译器 · Translator

本地运行的智能翻译工具，支持 11 种语言、10 个 LLM Provider 自由切换。
翻译质量基于 Hermes-Linguist 7 步管线，比 Google Translate 更自然。

## 功能

- 📝 **文本翻译**：中文、英语、波兰语、日语、韩语、德语、法语等 11 种语言
- 🖼️ **图片翻译**：拖拽 / 粘贴 / 上传图片，自动识别并翻译
- 🤖 **多模型可选**：DeepSeek、智谱 GLM、OpenAI、Claude、Gemini、Grok 等 10 个 Provider
- 🎯 **高质量**：内置 7 步翻译管线（语义解析 → 语境判断 → 文化识别 → 本地重构 → 沟通优化 → AI腔清除 → 母语校验）
- 📦 **零安装**：打包为独立 .app 文件，双击即用

## 安装与运行

### 方式一：双击运行（推荐）

1. 下载 `Translator.app`
2. 双击打开
3. 在 ⚙️ 设置页填入 API Key
4. 开始翻译

### 方式二：源码运行

```bash
pip install -r requirements.txt
python app.py
# 浏览器自动打开 http://127.0.0.1:58958
```

### 方式三：自行打包

```bash
bash build.sh
open dist/Translator.app
```

## API Key 获取

| Provider | 获取地址 | 用途 |
|----------|---------|------|
| DeepSeek | platform.deepseek.com | 文本翻译（推荐·中文场景） |
| 智谱 GLM | open.bigmodel.cn | 文本+图片（有免费额度） |
| 通义千问 | dashscope.aliyun.com | 文本+图片 |
| OpenAI | platform.openai.com | 文本+图片 |
| xAI Grok | x.ai | 文本+图片 |

## 快捷键

| 操作 | 快捷键 |
|------|--------|
| 翻译 | Cmd+Enter |
| 粘贴图片 | Cmd+V |
| 交换语言 | 点击 ⇄ |

## 技术栈

Python + Flask + 纯 HTML/CSS/JS（零前端框架依赖）
