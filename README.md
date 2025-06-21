# 智能数据库分析系统 (DataAnalyzer)

一个基于Python Flask和Anthropic Claude AI的智能数据库分析系统，支持CSV数据导入、AI智能分析、多轮对话和历史记录管理。

## 🌟 核心功能

- 📊 **智能数据分析**：基于Anthropic Claude AI的智能数据分析和洞察
- 📁 **CSV数据导入**：支持CSV文件上传并自动导入SQLite数据库
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
# 必需配置
ANTHROPIC_API_KEY=sk-your-api-key-here

# 可选配置
ANTHROPIC_BASE_URL=https://api.anthropic.com  # 可选，自定义API地址
HOST=0.0.0.0                                  # 服务器主机地址
PORT=5000                                     # 服务器端口
```

### 4. 启动系统

```bash
python start.py
```

启动后会自动：
- 启动Flask后端服务（http://localhost:5000）
- 打开Web测试界面（test_frontend.html）

## 📡 API 接口文档

### 基础信息

- **基础URL**: `http://localhost:5000/api`
- **认证方式**: 用户ID和用户名（通过请求头或参数传递）
- **数据格式**: JSON
- **CORS**: 支持跨域请求

### 用户认证

所有API接口都需要用户身份识别，支持以下方式：

#### 1. 请求头方式（推荐）
```http
X-User-ID: your_user_id
X-Username: your_username
```

#### 2. URL参数方式
```http
GET /api/status?userId=your_user_id&username=your_username
```

#### 3. 请求体方式
```json
{
  "userId": "your_user_id",
  "username": "your_username",
  "query": "your_query"
}
```

### 系统状态接口

#### GET /api/health
健康检查接口（无需认证）

**响应示例：**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### GET /api/status
获取系统状态（需要认证）

**响应示例：**
```json
{
  "system_ready": true,
  "database_connected": true,
  "database_path": "/path/to/user_db.db",
  "table_name": "data_table",
  "record_count": 1000,
  "api_status": "connected",
  "user_info": {
    "user_id": "user123",
    "username": "张三",
    "is_guest": false
  }
}
```

### 数据管理接口

#### POST /api/upload
上传CSV文件并导入数据库

**请求格式：** `multipart/form-data`

**参数：**
- `file`: CSV文件（必需）
- `tableName`: 表名（可选，默认为"data_table"）
- `userId`: 用户ID（必需）
- `username`: 用户名（可选）

**响应示例：**
```json
{
  "success": true,
  "message": "成功导入 1000 行数据到表 'data_table'",
  "data": {
    "rows_imported": 1000,
    "columns": ["id", "name", "age", "city"],
    "table_name": "data_table",
    "database_path": "/path/to/user_db.db"
  }
}
```

### 数据分析接口

#### POST /api/analyze-stream
流式AI数据分析

**请求体：**
```json
{
  "userId": "user123",
  "username": "张三",
  "query": "分析用户年龄分布情况"
}
```

**响应格式：** `text/plain` (Server-Sent Events)

**响应示例：**
```
data: {"type": "status", "message": "开始分析..."}

data: {"type": "progress", "step": "数据查询", "message": "正在查询数据库..."}

data: {"type": "content", "content": "根据数据分析，用户年龄分布如下："}

data: {"type": "complete", "conversation_id": "conv_20240101_120000_001"}
```

### 对话管理接口

#### POST /api/conversations/create
创建新对话

**请求体：**
```json
{
  "userId": "user123",
  "username": "张三",
  "conversation_name": "数据分析对话",
  "description": "关于用户数据的分析对话"
}
```

#### GET /api/conversations/list
获取用户对话列表

**响应示例：**
```json
{
  "success": true,
  "conversations": [
    {
      "conversation_id": "conv_20240101_120000_001",
      "conversation_name": "数据分析对话",
      "description": "关于用户数据的分析对话",
      "created_time": "2024-01-01T12:00:00Z",
      "last_activity": "2024-01-01T12:30:00Z",
      "status": "active",
      "message_count": 5,
      "user_id": "user123",
      "username": "张三"
    }
  ]
}
```

#### POST /api/conversations/switch
切换当前对话

**请求体：**
```json
{
  "userId": "user123",
  "conversation_id": "conv_20240101_120000_001"
}
```

#### GET /api/conversations/current
获取当前对话信息

#### GET /api/conversations
获取对话历史（支持分页）

**参数：**
- `limit`: 每页数量（默认10）
- `offset`: 偏移量（默认0）

#### GET /api/conversations/{conversation_id}
获取特定对话详情

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
- **作者**：山志强 (szqshan)

## 📄 开源协议

本项目采用 MIT 协议 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [Anthropic](https://www.anthropic.com/) - 提供强大的Claude AI API
- [Flask](https://flask.palletsprojects.com/) - 优秀的Python Web框架
- [Pandas](https://pandas.pydata.org/) - 强大的数据处理库

---

**版本信息**：v1.1.2
**最后更新**：2024年1月
**兼容性**：Python 3.7+ 