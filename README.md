# 🚀 智能数据库分析系统 (DataAnalyzer)

一个基于 Python Flask 和 Anthropic Claude AI 的智能数据库分析系统，支持 CSV 数据导入、AI 智能分析、多轮对话和历史记录管理。

## 🚨 最新版本更新

### 🎯 **v1.2.0 重大更新：性能与架构升级**

**🚀 核心引擎升级：**
- **⚡ 并行工具调用 (Parallel Tool Use)**：全面支持 Claude 3.5/3.7 模型的并发工具执行能力。现在 AI 可以一次性发出多个查询指令（如同时查询两张表），系统会自动批量执行并统一返回，分析效率提升 50% 以上。
- **🔄 架构重构**：实现了业务逻辑与 API 层的完全解耦。`database_analyzer.py` 现在专注于核心分析逻辑，而 `app.py` 专注于路由分发，代码结构更加清晰，易于维护。
- **🌊 优化流式响应**：重写了 SSE (Server-Sent Events) 事件流生成器，支持更平滑的打字机效果和实时的工具执行状态反馈。

**🖥️ 前端与交互：**
- **⚛️ React 现代化前端**：移除了旧版 HTML 测试页面，全面拥抱 React + Vite 前端架构（位于 `frontend/` 目录）。
- **🎨 极简项目结构**：清理了所有历史遗留脚本（如 `start_services.bat` 等），统一使用 `start.py` 作为唯一入口。

---

### 📋 必需字段说明
所有用户**必须**提供以下三个字段才能使用系统：
1. **用户ID** - 您的唯一标识符
2. **用户名** - 您的显示名称  
3. **API密钥** - 有效的 Anthropic Claude API Key

---

## 📚 文档导航

- [🌟 核心功能](#-核心功能)
- [📁 项目结构](#-项目结构)
- [⚡ 快速开始](#-快速开始)
- [🚀 使用指南](#-使用指南)
- [📡 API 接口文档](#-api-接口文档)
- [💻 开发指南](#-开发指南)
- [🤝 贡献指南](#-贡献指南)
- [📄 许可证](#-许可证)

## 🌟 核心功能

- 📊 **智能数据分析**：基于 Anthropic Claude AI 的智能数据分析和洞察
- ⚡ **并行工具执行**：支持 AI 并发调用多个数据库查询工具，大幅提升复杂问题的响应速度
- 🤖 **AI 标题生成**：用户发送第一条消息时 AI 自动生成对话标题，支持智能降级机制
- 📁 **多格式文件支持**：支持 CSV、Excel、JSON、TSV、TXT 等多种文件格式
- 🔍 **数据质量评估**：智能检测数据质量问题，提供 0-100 分的综合评分
- 🧹 **自动数据清洗**：智能处理缺失值、重复数据、异常值等问题
- 🔗 **多表支持**：单次会话中可分析多个数据表，支持跨表查询
- 📋 **表结构查看**：直接获取表的详细结构信息，包含列定义、样本数据、统计信息
- 💬 **多轮对话**：支持与 AI 进行多轮对话，保持上下文连续性
- 📚 **对话历史管理**：完整的对话历史记录和管理功能
- 👥 **多用户支持**：支持多用户隔离，每个用户有独立的数据空间
- 🔄 **流式响应**：支持 AI 响应的流式输出，提升用户体验
- 📄 **报告模板**：支持将分析结果保存为 Vue+JSON 模板，实现标准化报告复用

## 📁 项目结构

```
DataAnalyzer1.2/
├── backend/                    # 后端服务 (Python Flask)
│   ├── app.py                 # API 路由与入口
│   ├── database_analyzer.py   # 核心分析引擎 (含并行工具逻辑)
│   ├── conversation_history.py # 对话历史管理
│   ├── template_manager.py    # 报告模板管理
│   ├── user_middleware.py     # 用户鉴权中间件
│   ├── prompts.py             # 提示词管理
│   └── config.py              # 配置文件
├── frontend/                   # 前端应用 (React + Vite)
│   ├── src/                   # 源代码
│   ├── public/                # 静态资源
│   └── package.json           # 依赖配置
├── start.py                    # 统一启动脚本 (环境检查 + 服务启动)
├── requirements.txt            # Python 依赖
├── .gitignore                  # Git 忽略配置
└── README.md                   # 项目文档
```

## ⚡ 快速开始

### 1. 环境要求

- Python 3.8+
- Node.js 16+ (用于前端)
- Anthropic API Key

### 2. 安装依赖

```bash
# 安装后端依赖
pip install -r requirements.txt

# 安装前端依赖 (进入 frontend 目录)
cd frontend
npm install
```

### 3. 环境配置

在根目录创建 `.env` 文件：

```env
ANTHROPIC_BASE_URL=https://api.anthropic.com  # 可选
HOST=0.0.0.0
PORT=5000
```

### 4. 启动系统

使用统一启动脚本：

```bash
python start.py
```

该脚本会自动：
1. 检查 Python 环境与依赖
2. 启动 Flask 后端 (http://localhost:5000)
3. 启动 React 前端 (http://localhost:5173)

## 📡 API 接口文档

主要 API 端点：

- `POST /api/chat` - 发送对话消息 (流式响应)
- `POST /api/upload` - 上传数据文件
- `GET /api/conversations` - 获取对话列表
- `GET /api/tables` - 获取当前会话的数据表信息

> 详细 API 文档请参考后端代码注释。

## 📄 许可证

MIT License
