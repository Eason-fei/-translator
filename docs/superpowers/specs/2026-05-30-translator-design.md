# 翻译网站 — 设计规格说明 v3

> 日期：2026-05-30 · 状态：已确认 · 下一步：writing-plans

---

## 1. 项目概述

一个本地运行的 Web 翻译工具，支持 10+ 种语言、10 个 LLM Provider 自由切换。文本翻译和图片翻译均使用 LLM API，翻译策略遵循 Hermes-Linguist soul.md 的 7 步管线。

打包为 macOS `.app`，用户双击运行，无需安装 Python 或任何依赖。

---

## 2. 核心需求

### 2.1 功能需求

| 编号 | 功能 | 描述 |
|------|------|------|
| F1 | 文本翻译 | 输入文本 → 选源语言/目标语言/模型 → 输出翻译 |
| F2 | 图片翻译 | 上传/拖拽/Cmd+V 粘贴图片 → 识别并翻译图片中文字 |
| F3 | 多模型支持 | 10 个 Provider 可选，文本和图片翻译均可用 |
| F4 | API Key 管理 | 设置页为每个 Provider 填入 Key，存 localStorage |
| F5 | 语言选择 | 源语言/目标语言下拉框，含 soul.md 全部语种（含粤语） |
| F6 | 模型智能过滤 | 图片模式自动隐藏不支持 vision 的 Provider（如 DeepSeek） |
| F7 | 结果复制 | 一键复制翻译结果 |
| F8 | 打包分发 | PyInstaller 打包为独立 `.app`，双击即用 |

### 2.2 非功能需求

| 编号 | 需求 | 描述 |
|------|------|------|
| NF1 | 零安装 | 交付物为单个可执行文件，无需 Python/Docker/Node |
| NF2 | 跨平台可扩展 | 开发在 macOS，架构不绑定平台；Windows 打包后期补充 |
| NF3 | 多语种扩展 | 新增语种改 languages.json，新增 Provider 改 providers.json |
| NF4 | Provider 扩展 | 新增 Provider 只需在 providers.json 加一条配置 |

---

## 3. 语种范围

基于 soul.md Capability Scope：

| 语种 | 代码 | 
|------|------|
| 中文 | zh |
| 英语（美式） | en-US |
| 英语（英式） | en-GB |
| 德语 | de |
| 法语 | fr |
| 西班牙语 | es |
| 葡萄牙语 | pt |
| 波兰语 | pl |
| 日语 | ja |
| 韩语 | ko |
| 粤语 | yue |

语种列表定义在 `languages.json`，新增只需添加条目。

---

## 4. Provider 模型矩阵

### 4.1 国内 Provider

| Provider | 模型 | 文本 | 图片 | 备注 |
|----------|------|------|------|------|
| DeepSeek | deepseek-chat | ✅ | ❌ | 推荐·文本，国内直连 |
| 智谱 GLM | GLM-4V-Flash | ✅ | ✅ | 推荐·图片，免费额度，国内直连 |
| 通义千问 | Qwen-VL-Plus | ✅ | ✅ | 国内直连 |
| 月之暗面 | moonshot-v1-vision | ✅ | ✅ | 国内直连 |
| 字节豆包 | doubao-vision | ✅ | ✅ | 国内直连 |

### 4.2 海外 Provider

| Provider | 模型 | 文本 | 图片 | 备注 |
|----------|------|------|------|------|
| OpenAI | GPT-4o | ✅ | ✅ | 需梯子 |
| Anthropic | Claude 3.5 Sonnet | ✅ | ✅ | 需梯子 |
| Google | Gemini 2.5 Flash | ✅ | ✅ | 免费 tier，需梯子 |
| xAI | Grok-2-vision | ✅ | ✅ | 需梯子 |
| Mistral | Pixtral | ✅ | ✅ | 需梯子 |

Provider 定义在 `providers.json`，新增只需加一条。

---

## 5. 技术架构

### 5.1 整体架构

```
浏览器 (HTML/CSS/JS)
    │  HTTP localhost:58958
    ▼
Flask 后端 (app.py)
    ├── GET  /                  → 前端页面
    ├── GET  /api/providers     → 返回 providers.json（仅列表，不含 key）
    ├── GET  /api/languages     → 返回 languages.json
    ├── POST /api/translate     → 翻译请求（文本或图片）
    │     └── 路由到 providers[provider_id].adapter()
    └── 无状态，API Key 由前端每次随请求发送
```

### 5.2 翻译请求数据流

```
前端发送：
{
  "provider": "deepseek" | "zhipu" | "openai" | ...,
  "source_lang": "zh",
  "target_lang": "pl",
  "text": "...",           // 文本模式
  "image": "base64...",    // 图片模式（与 text 互斥）
  "api_key": "sk-..."      // 从 localStorage 读取，随请求发送
}

后端处理：
1. 从 providers.json 查找 provider 配置
2. 构建 system prompt（soul.md 7步管线 + Key Rules）
3. 调用对应 API（OpenAI 兼容格式 / 专有格式）
4. 返回 { "translation": "...", "provider": "...", "model": "..." }
```

### 5.3 API Key 安全

- Key 存浏览器 localStorage，不经过服务器持久化
- 每次请求随 body 发送到后端，用完即弃
- 设置页可管理多个 Provider 的 Key

---

## 6. 翻译 Prompt 工程

### 6.1 System Prompt 结构（来自 soul.md）

```
你是一个高级跨语言翻译引擎。你的核心目标不是"翻译文字"，而是生成
目标语言母语者真实会使用的自然表达。

翻译流程（按顺序执行）：
1. 解析真实语义、潜台词与说话者意图
2. 判断行业语境、双方关系、礼貌等级与社交距离
3. 识别文化负载词（成语、梗、双关、隐喻、网络流行语等）
4. 重构目标语言中的本地化、自然表达
5. 优化 Human-to-Human 沟通感、简洁性与可读性
6. 彻底清除 AI腔、翻译腔、中式逻辑残留
7. 执行 Native Authenticity Test（母语者真实性最终校验）

规则：
- 代码、HTML、JSON、SKU：完全保护，不翻译
- 专有名词：优先官方译名
- 严禁："Hope this email finds you well"、utilize、delve 等 AI 味表达
- 电商：爆款→Best Seller，不是"explosive model"
- 输出：仅译文，无解释
```

### 6.2 User Prompt 模板

```
将以下文本从 {source_lang_name} 翻译成 {target_lang_name}：

{user_text}
```

---

## 7. 前端设计

### 7.1 翻译页面

```
┌──────────────────────────────────────────────────┐
│  🌐 翻译器 · Translator · Tłumacz           ⚙  │
├──────────────────────────────────────────────────┤
│  [源语言 ▼]  →  [目标语言 ▼]  [模型 ▼]         │
│                                                  │
│  ┌─────────────────┐  ┌─────────────────┐       │
│  │ 输入文本        │  │ 翻译结果        │       │
│  │ 拖拽/粘贴图片   │  │ [复制]          │       │
│  └─────────────────┘  └─────────────────┘       │
│                                                  │
│  [翻译]                                          │
└──────────────────────────────────────────────────┘
```

### 7.2 交互细节

- 文本输入：textarea，自动调整高度
- 图片输入：拖拽、点击上传、**剪贴板粘贴（Cmd+V / Ctrl+V）**
- 语言切换：⇄ 按钮一键交换源/目标语言
- 模型下拉：仅显示已配置 Key 的 Provider；图片模式下隐藏 deepseek
- 结果区：可编辑，有复制按钮
- 设置页：弹窗/独立页面，每个 Provider 一个输入框

### 7.3 视觉风格

- 暗色主题
- 纯 CSS，无框架
- 响应式（桌面为主）

---

## 8. 项目结构

```
translator/
├── app.py              # Flask 主程序
├── providers.json      # Provider 注册表（API endpoint、模型名、vision 支持）
├── languages.json      # 语种配置
├── prompts.py          # soul.md 翻译 prompt 模板
├── requirements.txt    # flask, requests, Pillow
├── build.sh            # PyInstaller 打包脚本
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-05-30-translator-design.md
└── README.md
```

### 8.1 providers.json 格式

```json
{
  "deepseek": {
    "name": "DeepSeek",
    "model": "deepseek-chat",
    "api_base": "https://api.deepseek.com/v1",
    "supports_vision": false,
    "region": "china"
  },
  "zhipu": {
    "name": "智谱 GLM",
    "model": "glm-4v-flash",
    "api_base": "https://open.bigmodel.cn/api/paas/v4",
    "supports_vision": true,
    "region": "china"
  }
}
```

---

## 9. 打包与分发

```bash
# macOS
pyinstaller --onefile --windowed --name Translator app.py
# 输出: dist/Translator.app
```

用户体验：
1. 下载 `Translator.app` → 双击打开
2. 自动启动 Flask → 自动打开浏览器
3. 首次使用：设置页填入 API Key
4. 即可使用

---

## 10. 不做什么

- ❌ 用户账户/登录
- ❌ 翻译历史持久化
- ❌ 术语库/翻译记忆
- ❌ 并发/多线程
- ❌ 工具界面国际化（固定中文）
- ❌ Docker
- ❌ 在线托管

---

## 11. 成功标准

1. `python app.py` 启动，完成一次 DeepSeek 文本翻译
2. 完成一次图片翻译（智谱 GLM-4V 或其他 vision provider）
3. 切换 Provider 翻译（从 DeepSeek 切到 OpenAI，验证 prompt 不丢）
4. Cmd+V 粘贴图片触发翻译
5. PyInstaller 打包的 `.app` 在另一台 MacBook 上双击可用
6. 翻译结果比 Google Translate 更自然
