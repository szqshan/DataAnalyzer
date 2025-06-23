# 🚀 智能数据库分析系统 (DataAnalyzer)

一个基于Python Flask和Anthropic Claude AI的智能数据库分析系统，支持CSV数据导入、AI智能分析、多轮对话和历史记录管理。

## 🚨 重要版本更新 (v1.1.1)

### ⚠️ **重大变更：删除访客模式**

**从此版本开始，系统仅支持付费用户访问！**

#### 📋 必需字段
现在所有用户**必须**提供以下三个字段才能使用系统：
1. **用户ID** - 您的唯一标识符
2. **用户名** - 您的显示名称  
3. **API密钥** - 有效的Anthropic Claude API Key

#### 🔒 安全改进
- ✅ 删除了基于IP和User-Agent的临时访客ID生成
- ✅ 强制要求每个请求都提供API Key
- ✅ 添加了更严格的用户认证验证
- ✅ 提供了清晰的错误代码和消息

#### 💰 成本控制
- ✅ 每个API调用都有明确的成本归属
- ✅ 不再有"免费试用"或"访客模式"
- ✅ 确保所有API使用都可追溯到具体用户

#### 🖥️ 前端界面变更
- ✅ 添加了醒目的付费用户提醒横幅
- ✅ 所有输入框都标明"必需"
- ✅ 加强了API Key验证逻辑
- ✅ 统一了请求头构建方式

**⚠️ 迁移提醒：** 如果您之前使用访客模式，现在需要获取Anthropic API Key才能继续使用系统。

## 📚 文档导航

- [🌟 核心功能](#-核心功能)
- [📁 项目结构](#-项目结构)
- [⚡ 快速开始](#-快速开始)
- [🚀 使用指南](#-使用指南)
- [📡 API 接口文档](#-api-接口文档)
- [💻 开发指南](#-开发指南)
- [🤝 贡献指南](#-贡献指南)
- [📄 许可证](#-许可证)

**📖 详细文档：**
- **[API调用示例文档](./API_EXAMPLES.md)** - 完整的API调用示例和代码
- **[数据处理功能说明](./DATA_PROCESSING_FEATURE.md)** - 多格式支持和数据清洗功能详解
- **[多表功能说明](./MULTI_TABLE_FEATURE.md)** - 多表支持和跨表查询功能说明
- **[系统架构说明](#-系统架构)** - 技术架构和设计原理

## 🌟 核心功能

- 📊 **智能数据分析**：基于Anthropic Claude AI的智能数据分析和洞察
- 📁 **多格式文件支持**：支持CSV、Excel、JSON、TSV、TXT等多种文件格式
- 🔍 **数据质量评估**：智能检测数据质量问题，提供0-100分的综合评分
- 🧹 **自动数据清洗**：智能处理缺失值、重复数据、异常值等问题
- 🔗 **多表支持**：单次会话中可分析多个数据表，支持跨表查询
- 📋 **表结构查看**：直接获取表的详细结构信息，包含列定义、样本数据、统计信息
- 💬 **多轮对话**：支持与AI进行多轮对话，保持上下文连续性
- 📚 **对话历史管理**：完整的对话历史记录和管理功能
- 👥 **多用户支持**：支持多用户隔离，每个用户有独立的数据空间
- 🔄 **流式响应**：支持AI响应的流式输出，提升用户体验
- 🌐 **Web界面**：提供直观的Web测试界面

## 📁 项目结构

```
DataAnalyzer1.1/
├── backend/                    # 后端服务
│   ├── app.py                 # Flask主应用文件
│   ├── conversation_history.py # 对话历史管理
│   ├── datatest1_7_5.py       # 数据分析核心
│   ├── user_middleware.py     # 用户管理中间件
│   └── data/                  # 后端数据目录
├── data/                      # 用户数据存储目录
├── logs/                      # 系统日志目录
├── test_frontend.html         # Web测试界面
├── start.py                   # 系统启动脚本
├── requirements.txt           # Python依赖
├── .gitignore                # Git忽略文件
└── README.md                 # 项目文档
```

## ⚡ 快速开始

### 1. 环境要求

- Python 3.7+
- 现代浏览器（Chrome、Firefox、Edge等）
- Anthropic API密钥

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 环境配置

创建 `.env` 文件并添加以下配置：

```env
# 服务器配置
ANTHROPIC_BASE_URL=https://api.anthropic.com  # 可选，自定义API地址
HOST=0.0.0.0                                  # 服务器主机地址
PORT=5000                                     # 服务器端口

# 注意：不再支持全局API Key配置
# ANTHROPIC_API_KEY=sk-your-api-key-here  # 已完全移除
```

**🔑 重要变更（v1.1.1）：**
- ❌ **完全移除**全局共享的API Key支持
- ✅ **强制要求**每个用户在前端提供自己的API Key
- ✅ **访客模式已删除**，所有用户必须提供完整认证信息
- ✅ 确保数据隔离和成本控制

### 4. 启动系统

```bash
python start.py
```

启动后会自动：
- 启动Flask后端服务（http://localhost:5000）
- 打开Web测试界面（test_frontend.html）

## 🚀 使用指南

### 📱 Web界面使用

1. 启动系统后，浏览器会自动打开测试页面
2. **⚠️ 重要：** 在"用户信息设置"区域**必须**填写所有三个字段：
   - **用户ID**（必需，如：`user001`）
   - **用户名**（必需，如：`张三`）
   - **API密钥**（必需，如：`sk-ant-api-your-key-here`）
3. 点击"设置用户信息"（系统会验证所有字段是否完整）
4. 上传CSV数据文件
5. 查看表结构信息（自动显示或点击"🔄 刷新表列表"）
6. 开始AI数据分析对话

**🔑 获取API密钥：**
- 访问 [Anthropic Console](https://console.anthropic.com/)
- 创建账户并获取API Key
- API Key格式：`sk-ant-api-xxxxx`

### 💻 API调用示例

```javascript
// 快速开始示例
const response = await fetch('http://localhost:5000/api/analyze-stream', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-User-ID': 'user001',
        'X-Username': '张三',
        'X-API-Key': 'sk-ant-api-your-key-here'
    },
    body: JSON.stringify({
        query: '请分析这个数据集的基本统计信息'
    })
});
```

**👉 [查看完整API调用示例](./API_EXAMPLES.md)**

## 📡 API 接口文档

### 基础信息

- **基础URL**: `http://localhost:5000/api`
- **认证方式**: 用户ID、用户名和API密钥（通过请求头或参数传递）
- **数据格式**: JSON
- **CORS**: 支持跨域请求

### 📚 详细API示例

本项目提供了完整的API调用示例文档，包含JavaScript、Python、curl等多种调用方式：

**👉 [查看完整API示例文档](./API_EXAMPLES.md)**

API示例文档包含以下内容：
- 🔧 基础配置和环境设置
- 🔐 多种用户认证方式
- 🏥 系统状态和健康检查
- 📁 数据上传和管理
- 🤖 AI数据分析调用
- 💬 对话管理和历史记录
- ❌ 错误处理和最佳实践
- 🎯 完整的端到端示例

### 用户认证

**⚠️ v1.1.1重要变更：** 所有API接口都**强制要求**用户身份识别和API密钥，不再支持访客模式。支持以下方式：

#### 1. 请求头方式（推荐）
```http
X-User-ID: your_user_id
X-Username: your_username
X-API-Key: sk-ant-api-your-api-key-here
```

#### 2. URL参数方式
```http
GET /api/status?userId=your_user_id&username=your_username&apiKey=sk-ant-api-your-key
```

#### 3. 请求体方式
```json
{
  "userId": "your_user_id",
  "username": "your_username",
  "apiKey": "sk-ant-api-your-api-key-here",
  "query": "your_query"
}
```

**🔐 API Key 安全说明（v1.1.1更新）：**
- ✅ **强制要求**：每个用户必须使用独立的API Key
- ✅ **安全传输**：API Key通过HTTPS安全传输
- ✅ **不存储**：前端不会存储API Key，每次使用时需要重新输入
- ✅ **成本隔离**：确保每个API调用的成本归属明确
- ❌ **无访客模式**：不再支持临时或匿名访问

### 🔗 主要API端点

| 端点 | 方法 | 描述 | 需要API Key |
|------|------|------|-------------|
| `/api/health` | GET | 系统健康检查 | ❌ |
| `/api/status` | GET | 获取系统状态 | ✅ |
| `/api/preview-file` | POST | 预览文件和数据质量评估 | ✅ |
| `/api/upload` | POST | 上传多格式数据文件（增强版） | ✅ |
| `/api/tables-info` | GET | 获取表结构信息 | ✅ |
| `/api/analyze-stream` | POST | 流式AI数据分析 | ✅ |
| `/api/conversations/create` | POST | 创建新对话 | ❌ |
| `/api/conversations/list` | GET | 获取对话列表 | ❌ |
| `/api/conversations/switch` | POST | 切换当前对话 | ❌ |

### 📋 响应格式

所有API响应都采用JSON格式：

```json
{
  "success": true,
  "message": "操作成功",
  "data": { /* 具体数据 */ }
}
```

流式分析接口采用Server-Sent Events格式：
```
data: {"type": "status", "message": "开始分析..."}
data: {"type": "ai_response", "content": "分析结果..."}
data: {"type": "complete", "conversation_id": "conv_123"}
```

#### GET /api/conversations/{conversation_id}
获取特定对话详情

## 💻 开发指南

### 🏗️ 系统架构

```
┌─────────────────┐    HTTP/WebSocket    ┌─────────────────┐
│   前端界面      │ ◄──────────────────► │   Flask后端     │
│ (HTML/JS)       │                      │   (Python)      │
└─────────────────┘                      └─────────────────┘
                                                   │
                                                   ▼
                                         ┌─────────────────┐
                                         │   用户管理      │
                                         │  (中间件)       │
                                         └─────────────────┘
                                                   │
                                                   ▼
                                         ┌─────────────────┐
                                         │  数据分析器     │
                                         │ (AI + SQLite)   │
                                         └─────────────────┘
                                                   │
                                                   ▼
                                         ┌─────────────────┐
                                         │   Anthropic     │
                                         │   Claude API    │
                                         └─────────────────┘
```

### 🔧 技术栈

**后端：**
- **Flask** - Web框架
- **SQLite** - 数据存储
- **Pandas** - 数据处理
- **Anthropic** - AI服务

**前端：**
- **HTML5/CSS3** - 界面结构和样式
- **JavaScript (ES6+)** - 交互逻辑
- **Server-Sent Events** - 实时通信
- **Marked.js** - Markdown渲染

### 🔄 数据流程

1. **用户认证** → 用户信息验证和API Key检查
2. **数据上传** → CSV解析 → SQLite存储
3. **AI分析** → 构建提示词 → Claude API调用
4. **流式响应** → 实时返回分析结果
5. **对话管理** → 历史记录存储和检索

### 🚀 版本历史

- **v1.1.2** (2024-12) - 表信息接口增强
  - ✅ 新增 `/api/tables-info` 接口，直接获取表结构信息
  - ✅ 前端恢复表信息显示功能，支持详细的卡片式布局
  - ✅ 表信息包含列结构、样本数据、统计信息等
  - ✅ 完善API文档，增加表信息接口调用示例
  - ✅ 优化用户体验，无需通过AI分析即可查看数据结构

- **v1.1.1** (2024-12) - 删除访客模式，强制API Key认证
  - ✅ 完全移除访客模式，强制要求用户API Key
  - ✅ 增强安全性和成本控制
  - ✅ 更新前后端认证逻辑

- **v1.1.0** (2024-12) - 用户专属API Key架构
  - ✅ 废弃全局共享API Key
  - ✅ 实现用户专属API密钥管理
  - ✅ 增强数据隔离和安全性
  
- **v1.0.0** (2024-11) - 初始版本
  - ✅ 基础AI数据分析功能
  - ✅ 多用户支持
  - ✅ 对话历史管理

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 🐛 报告问题

如果您发现了bug或有功能建议，请：
1. 查看 [Issues](https://github.com/szqshan/DataAnalyzer/issues) 是否已存在相关问题
2. 如果没有，请创建新的Issue并提供详细信息

### 💡 功能建议

我们欢迎新功能建议：
- 数据可视化增强
- 更多数据源支持
- 更多AI模型集成
- 性能优化建议

### 🔧 开发贡献

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📞 支持与联系

- **GitHub Issues**: [问题反馈](https://github.com/szqshan/DataAnalyzer/issues)
- **项目主页**: [DataAnalyzer](https://github.com/szqshan/DataAnalyzer)
- **API文档**: [API调用示例](./API_EXAMPLES.md)

## 📄 许可证

本项目基于 MIT 许可证开源 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

<div align="center">

**🌟 如果这个项目对您有帮助，请给我们一个Star！**

[⭐ Star this project](https://github.com/szqshan/DataAnalyzer) | [🐛 Report Bug](https://github.com/szqshan/DataAnalyzer/issues) | [💡 Request Feature](https://github.com/szqshan/DataAnalyzer/issues)

</div>

#### DELETE /api/conversations/{conversation_id}
删除对话

#### GET /api/conversations/recent
获取最近对话列表

**参数：**
- `limit`: 数量限制（默认5）

#### GET /api/conversations/stats
获取对话统计信息

**响应示例：**
```json
{
  "success": true,
  "stats": {
    "total_conversations": 10,
    "active_conversations": 8,
    "total_messages": 150,
    "avg_messages_per_conversation": 15.0,
    "most_active_day": "2024-01-01",
    "recent_activity": "2024-01-01T12:30:00Z"
  }
}
```

### 消息管理接口

#### POST /api/conversations/{conversation_id}/messages/{message_id}/edit
编辑消息

**请求体：**
```json
{
  "userId": "user123",
  "new_content": "修改后的消息内容"
}
```

#### POST /api/conversations/{conversation_id}/messages/{message_id}/delete
删除消息

**请求体：**
```json
{
  "userId": "user123"
}
```

## 🚨 已知问题和限制

### 1. 前端界面问题
- **响应式设计缺失**：前端页面不能自适应不同窗口大小
- **移动端支持不足**：在移动设备上显示效果不佳
- **UI/UX待优化**：界面设计较为简单，用户体验有待提升

### 2. 性能和稳定性
- **大文件处理**：处理超大CSV文件时可能出现内存不足
- **并发限制**：高并发情况下可能出现数据库锁定问题
- **错误恢复**：系统异常后的自动恢复机制不完善

### 3. 功能限制
- **数据格式支持**：目前只支持CSV格式，不支持Excel、JSON等格式
- **数据库类型**：只支持SQLite，不支持MySQL、PostgreSQL等
- **AI模型限制**：依赖Anthropic Claude API，受API限制影响

### 4. 安全性问题
- **用户认证**：用户认证机制较为简单，缺乏严格的权限控制
- **数据隔离**：虽然支持多用户，但数据隔离机制需要加强
- **API安全**：缺乏API速率限制和防护机制

### 5. 多用户系统问题
- **用户ID依赖**：系统正常运行需要提供有效的用户ID
- **访客模式限制**：访客模式功能有限，建议注册正式用户
- **数据持久化**：用户数据依赖本地存储，缺乏云端备份

### 6. AI分析准确性
- **提示词优化**：AI分析的准确性依赖系统提示词，需要持续优化
- **上下文理解**：复杂查询的上下文理解能力有限
- **结果验证**：AI分析结果缺乏自动验证机制

## 🔧 开发指南

### 本地开发

1. **克隆项目**
```bash
git clone https://github.com/szqshan/DataAnalyzer.git
cd DataAnalyzer
```

2. **安装开发依赖**
```bash
pip install -r requirements.txt
```

3. **配置开发环境**
```bash
cp .env.example .env
# 编辑 .env 文件，添加你的API密钥
```

4. **启动开发服务器**
```bash
python start.py
```

### 项目架构

- **前后端分离**：前端使用原生HTML/JS，后端使用Flask
- **用户隔离**：每个用户有独立的数据库和存储空间
- **模块化设计**：功能模块独立，便于维护和扩展

### 添加新功能

1. **后端API**：在 `backend/app.py` 中添加新的路由
2. **数据处理**：在 `backend/datatest1_7_5.py` 中添加新的分析功能
3. **前端界面**：在 `test_frontend.html` 中添加新的UI组件

## 📋 待办事项

### 高优先级
- [ ] 修复前端响应式设计问题
- [ ] 优化大文件处理性能
- [ ] 加强用户认证和权限控制
- [ ] 添加数据格式支持（Excel、JSON等）

### 中优先级
- [ ] 实现云端数据备份
- [ ] 添加API速率限制
- [ ] 优化AI提示词和分析准确性
- [ ] 添加数据可视化功能

### 低优先级
- [ ] 支持更多数据库类型
- [ ] 添加用户管理后台
- [ ] 实现插件系统
- [ ] 添加单元测试和集成测试

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork项目
2. 创建功能分支：`git checkout -b feature/AmazingFeature`
3. 提交更改：`git commit -m 'Add some AmazingFeature'`
4. 推送到分支：`git push origin feature/AmazingFeature`
5. 创建Pull Request

## 📞 技术支持

- **项目地址**：https://github.com/szqshan/DataAnalyzer
- **问题反馈**：https://github.com/szqshan/DataAnalyzer/issues
- **作者**：Shawn
  
## 📄 开源协议

本项目采用 MIT 协议 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [Anthropic](https://www.anthropic.com/) - 提供强大的Claude AI API
- [Flask](https://flask.palletsprojects.com/) - 优秀的Python Web框架
- [Pandas](https://pandas.pydata.org/) - 强大的数据处理库

---

**版本信息**：v1.1.2
**最后更新**：2025年6月21日
**兼容性**：Python 3.7+ 
