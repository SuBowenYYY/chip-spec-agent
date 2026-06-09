# 芯片规格书智能转换Agent

基于 LangGraph + FastAPI + React 的 Web 应用，将芯片 PDF 规格书智能转换为 Markdown 文档和结构化参数。

## 功能特性

- **PDF → Markdown 自动转换**：上传 PDF 后，系统一次性将所有页面转为图片并传给多模态大模型生成完整 Markdown，自动保存为 `data/md/{id}.md`
- **参数手动提取**：从已有 Markdown 文件中选择或手动输入 ID，输入芯片型号（可选），选择模型后提取技术参数，保存为 `data/extracted/{id}_extracted.md`
- **参数映射查询**：通过转换 ID 查询已提取的参数，AI 智能映射参数值
- **自定义转换ID**：上传 PDF 时可手动输入芯片型号作为 ID（如 `STM32F103C8T6`），便于后续管理和查询
- **文件列表查询**：参数提取时支持从已有 MD 文件中下拉选择，上传后自动填充 ID
- **提示词管理**：转换和提取逻辑由后端 `prompts/` 目录下的 `.md` 文件控制，直接编辑即可生效
- **多模型切换**：支持通义千问、DeepSeek、Kimi 等多种模型
- **多模态模型标记**：自动识别并标记支持多模态的模型（用于 PDF 图片转换）
- **安全 Markdown 渲染**：前端使用 react-markdown 渲染 Markdown，避免 XSS 风险

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 前端 | React 18 + Ant Design 5 + Vite |
| 后端 | Python 3.10+ + FastAPI |
| Agent框架 | LangGraph + LangChain |
| 大模型调用 | LangChain OpenAI SDK（兼容所有 OpenAI 格式 API） |
| PDF处理 | PyPDF2 + pdf2image + Poppler |
| Markdown渲染 | react-markdown + remark-gfm |

## 项目结构

```text
chip-spec-agent/
├── frontend/                # React 前端
│   ├── src/
│   │   ├── components/      # UI 组件
│   │   │   ├── FileUpload.jsx      # 文件上传（拖拽+自定义ID）
│   │   │   ├── ModelSelector.jsx   # 模型选择器（含多模态标记）
│   │   │   ├── QueryPanel.jsx      # 参数查询面板
│   │   │   └── ResultDisplay.jsx   # 结果展示（Markdown渲染+提取结果预览）
│   │   ├── pages/           # 页面组件
│   │   │   └── MainPage.jsx        # 主页面（三栏布局+状态管理）
│   │   ├── services/        # API 服务
│   │   │   └── api.js              # Axios 封装的所有后端接口
│   │   ├── App.jsx          # 根组件（ConfigProvider + Layout）
│   │   ├── main.jsx         # 入口文件
│   │   └── index.css        # 全局样式 + Markdown 渲染样式
│   ├── index.html
│   ├── package.json
│   └── vite.config.js       # Vite 配置（含 API 代理）
├── backend/                 # Python 后端
│   ├── main.py              # FastAPI 入口（API 端点 + 后台任务）
│   ├── config.py            # 配置管理（pydantic-settings）
│   ├── prompt_loader.py     # 提示词加载工具（每次从磁盘读取，支持热更新）
│   ├── diagnostic.py        # 诊断脚本（测试PDF转换和模型API）
│   ├── prompts/             # 提示词文件（.md 格式，直接编辑即生效）
│   │   ├── md_system.md     # PDF转Markdown系统提示词
│   │   ├── md_user.md       # PDF转Markdown用户提示词（含 {total_pages} 占位符）
│   │   ├── extract_system.md # 参数提取系统提示词
│   │   ├── extract_user.md  # 参数提取用户提示词（含 {chip_model}、{full_markdown_content}）
│   │   ├── query_system.md  # 参数查询系统提示词
│   │   └── query_user.md    # 参数查询用户提示词（含 {chip_model}、{parameter_name}、{extract_content}）
│   ├── .env.example         # 环境变量示例
│   ├── .env                 # 环境变量（不提交到 git）
│   ├── requirements.txt     # Python 依赖
│   ├── graphs/              # LangGraph 工作流定义
│   │   └── query_graph.py   # 参数查询工作流
│   ├── nodes/               # 工作流节点实现
│   │   ├── convert_nodes.py # PDF拆分、多模态转换、Markdown保存、清理
│   │   ├── extract_nodes.py # 读取MD、LLM提取参数、保存结果
│   │   └── query_nodes.py   # 读取提取结果、LLM映射参数值
│   ├── utils/               # 工具函数
│   │   ├── file_utils.py    # 文件操作（读写、目录管理、路径生成）
│   │   └── model_utils.py   # 大模型调用（LangChain封装，支持多模态）
│   └── data/                # 数据存储（运行时自动创建）
│       ├── md/              # PDF 转 Markdown 结果（.md）
│       ├── extracted/       # 参数提取结果（.md）
│       └── temp/            # 临时文件（转换完成后自动清理）
```

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- Poppler（pdf2image 依赖）

### 1. 安装 Poppler（Windows）

```powershell
# 使用 winget 安装（推荐）
winget install poppler

# 安装完成后验证
pdfinfo -v
```

### 2. 后端设置

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv .venv
.venv\Scripts\activate   # Windows

# 安装依赖（使用 uv）
uv pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
```

编辑 `.env` 文件：

```env
# 通义千问配置（必填）
DASHSCOPE_API_KEY=sk-your-actual-key-here

# Poppler 路径（Windows 需要，自动检测不到时填写）
# POPPLER_PATH=C:\Users\xxx\AppData\Local\Microsoft\WinGet\Packages\...poppler-xxx\Library\bin

# 系统配置
MAX_FILE_SIZE=104857600
MAX_PDF_PAGES=100
TEMP_DIR=./data/temp
MD_DIR=./data/md
EXTRACT_DIR=./data/extracted
```

### 3. 前端设置

```bash
cd frontend
npm install
```

### 4. 启动服务

```bash
# 终端1：启动后端（端口 8000）
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 终端2：启动前端（端口 3000）
cd frontend
npm run dev
```

访问 <http://localhost:3000> 即可使用。

## 使用说明

### 工作流程

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                              前端界面（三栏布局）                               │
├────────────────────────┬────────────────────────┬─────────────────────────────┤
│       左栏             │        中栏            │          右栏              │
│    PDF 转换            │     转换结果          │       参数映射查询          │
│   ├ 选择模型           │     ├ Markdown 预览   │       ├ 选择/输入 ID       │
│   ├ 上传 PDF           │     ├ 提取结果预览    │       ├ 输入芯片型号        │
│   └ 开始转换            │     └ 上下滑动查看    │       ├ 输入参数名称        │
│                        │                        │       └ 查询参数           │
├────────────────────────┼────────────────────────┼─────────────────────────────┤
│    参数提取            │                        │                            │
│   ├ 选择 MD 文件       │                        │                            │
│   ├ 输入芯片型号（可选）│                        │                            │
│   ├ 选择提取模型       │                        │                            │
│   └ 开始提取            │                        │                            │
├────────────────────────┼────────────────────────┼─────────────────────────────┤
│    下载文件 / 进度      │                        │                            │
└────────────────────────┴────────────────────────┴─────────────────────────────┘
```

### 自定义转换ID

上传 PDF 时，可以：

- **留空**：系统自动生成 UUID（如 `408fab90-3598-4549-b73b-cb942f50e42d`）
- **手动输入**：使用芯片型号作为 ID（如 `STM32F103C8T6`）

> 使用芯片型号作为 ID 更便于后续管理和查询。上传后 ID 会自动填充到「参数提取」区域。

### 模型选择建议

| 模型 | 多模态 | 用途建议 |
| --- | --- | --- |
| Kimi-K2.6 | ✅ | **PDF 转 Markdown**（处理图片） |
| Qwen3.7-Max | ❌ | 参数提取、参数查询（纯文本） |
| DeepSeek-V4-Pro | ❌ | 参数提取、参数查询（纯文本） |

> **注意**：PDF 转 Markdown 必须使用多模态模型（如 Kimi-K2.6），因为需要将 PDF 每页转为图片后输入模型。

### 文件列表选择

在「参数提取」区域，Conversion ID 支持两种方式：

- **下拉选择**：从已转换的 Markdown 文件中选择（自动列出 `data/md/` 目录中的所有文件）
- **手动输入**：直接输入 Conversion ID

**芯片型号（可选）**：输入芯片型号（如 `STM32F103C8T6`），会拼接到提示词尾部，帮助模型更精准地识别参数。

> 上传 PDF 后，ID 会自动填充到「参数提取」区域。也可以从下拉列表中选择之前转换过的文件进行参数提取。

### 提取结果文件

参数提取结果存储在 `data/extracted/` 目录下，文件格式为 `.md`：

- `data/md/{conversion_id}.md` — PDF 转 Markdown 的原始结果
- `data/extracted/{conversion_id}_extracted.md` — 参数提取结果（LLM 原始输出文本）

> **注意**：`data/extracted/` 目录下存储的是 `.md` 格式的文本文件。提取提示词要求 LLM 输出 JSON 格式，但系统直接将 LLM 原始文本保存为 `.md`，不做 JSON 解析。

### API 接口

| 接口 | 方法 | 说明 |
| --- | --- | --- |
| `/api/models` | GET | 获取可用模型列表（含多模态标记） |
| `/api/upload` | POST | 上传 PDF 文件（支持自定义 ID，超页数自动清理） |
| `/api/files` | GET | 获取已有文件列表（MD 文件 / 提取结果文件） |
| `/api/prompts` | GET | 获取所有提示词内容 |
| `/api/convert` | POST | 启动 PDF → Markdown 转换（后台异步，仅转换不提取） |
| `/api/extract` | POST | 启动参数提取（后台异步，从已有 MD 文件提取） |
| `/api/status/{id}` | GET | 查询转换/提取进度（含阶段、百分比、结果数据） |
| `/api/query` | POST | 查询参数值（通过 LangGraph 工作流调用 LLM 映射） |
| `/api/download/{id}/md` | GET | 下载 Markdown 文件 |
| `/api/download/{id}/extract` | GET | 下载提取结果文件（.md 格式） |

### 管理提示词

所有提示词存储在 `backend/prompts/` 目录下的 `.md` 文件中，**每次调用时从磁盘读取**，直接编辑保存后下次请求自动生效，无需重启后端。

| 文件 | 说明 |
| --- | --- |
| `md_system.md` | PDF 转 Markdown 的系统提示词（定义角色和输出模板） |
| `md_user.md` | PDF 转 Markdown 的用户提示词（含 `{total_pages}` 占位符） |
| `extract_system.md` | 参数提取的系统提示词（定义角色和 JSON 输出格式） |
| `extract_user.md` | 参数提取的用户提示词（含 `{chip_model}`、`{full_markdown_content}` 占位符） |
| `query_system.md` | 参数查询的系统提示词（定义角色） |
| `query_user.md` | 参数查询的用户提示词（含 `{chip_model}`、`{parameter_name}`、`{extract_content}` 占位符） |

> **提示**：
>
> - 系统提示词（system prompt）用于定义模型角色和行为模式
> - 用户提示词（user prompt）用于传递具体的任务指令
> - 支持 `{占位符}` 动态替换

### 配置新模型

编辑 `backend/config.py` 中的 `MODELS` 字典：

```python
MODELS = {
    "Kimi-K2.6": {
        "provider": "openai_compatible",
        "model": "kimi-k2.6",
        "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key_env": "DASHSCOPE_API_KEY",
        "max_tokens": 98304,
        "temperature": 0,
        "multimodal": True,  # 标记为多模态
    },
    "Qwen3.7-Max": {
        "provider": "openai_compatible",
        "model": "qwen3.7-max",
        "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key_env": "DASHSCOPE_API_KEY",
        "max_tokens": 65536,
        "temperature": 0,
        "multimodal": False,
    },
    "DeepSeek-V4-Pro": {
        "provider": "openai_compatible",
        "model": "deepseek-v4-pro",
        "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key_env": "DASHSCOPE_API_KEY",
        "max_tokens": 384000,
        "temperature": 0,
        "multimodal": False,
    },
}
```

## 注意事项

- PDF 文件大小限制：100MB
- PDF 页数限制：100 页（超出时自动清理已保存的临时文件）
- **PDF 转 Markdown 必须使用多模态模型**（如 Kimi-K2.6）
- **一次性处理**：所有 PDF 页面图片一次性传给 LLM，相比逐页处理大幅减少时间
- **图片质量**：PDF 转为 150 DPI 的 PNG 图片，平衡了清晰度与传输效率
- 转换过程可能耗时较长（取决于页数和模型速度）
- 临时文件会在转换完成后自动清理
- Markdown 文件自动保存为 `data/md/{conversion_id}.md`
- 参数提取结果保存为 `data/extracted/{conversion_id}_extracted.md`（LLM 原始输出文本）
- 自定义 ID 不能包含特殊字符（建议仅使用字母、数字、下划线、连字符）
- 前端 Markdown 渲染使用 react-markdown，避免 dangerouslySetInnerHTML 带来的 XSS 风险

## License

MIT
