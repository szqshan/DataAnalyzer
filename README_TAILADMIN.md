# TailAdmin React 数据分析系统

基于 TailAdmin React 模板构建的智能数据分析前端界面，与现有 Flask 后端完美集成。

## 🚀 快速启动

### 方法一：使用启动脚本（推荐）

```bash
# PowerShell 脚本
.\start_services.ps1

# 或使用批处理文件
.\start_services.bat
```

### 方法二：手动启动

1. **启动后端服务**
```bash
cd backend
python app.py
```

2. **启动前端服务**
```bash
cd frontend
npm run dev
```

## 📋 功能特性

### ✅ 已完成功能

- **🔐 用户认证系统**
  - 用户ID、用户名、API密钥登录
  - 持久化登录状态
  - 路由保护

- **📊 数据分析界面**
  - CSV 文件拖拽上传
  - 实时流式数据分析
  - 智能对话交互
  - 分析结果展示

- **💬 对话管理**
  - 对话历史记录
  - 创建新对话
  - 切换对话
  - 删除对话

- **📈 系统监控**
  - 系统状态显示
  - 数据库连接状态
  - AI API 状态监控
  - 数据统计信息

- **🎨 现代化UI**
  - 基于 TailAdmin React 模板
  - Tailwind CSS 样式
  - 响应式设计
  - 深色/浅色主题支持

## 🌐 访问地址

- **前端界面**: http://localhost:5173
- **后端API**: http://localhost:5000
- **API文档**: http://localhost:5000/api/health

## 📁 项目结构

```
DataAnalyzer1.2_TRAE/
├── backend/                 # Flask 后端
│   ├── app.py              # 主应用文件
│   ├── requirements.txt    # Python 依赖
│   └── ...
├── frontend/               # TailAdmin React 前端
│   ├── src/
│   │   ├── components/     # 自定义组件
│   │   │   ├── FileUpload.tsx
│   │   │   ├── DataAnalysis.tsx
│   │   │   ├── ConversationManager.tsx
│   │   │   └── SystemStatusCard.tsx
│   │   ├── context/        # React Context
│   │   │   └── AuthContext.tsx
│   │   ├── pages/          # 页面组件
│   │   │   ├── Authentication/
│   │   │   │   └── SignIn.tsx
│   │   │   └── Dashboard/
│   │   │       └── Dashboard.tsx
│   │   ├── services/       # API 服务
│   │   │   └── api.ts
│   │   └── App.tsx         # 主应用组件
│   ├── package.json
│   └── ...
├── start_services.ps1      # PowerShell 启动脚本
├── start_services.bat      # 批处理启动脚本
└── README_TAILADMIN.md     # 本文档
```

## 🔧 技术栈

### 前端
- **React 19** - 用户界面框架
- **TypeScript** - 类型安全
- **Tailwind CSS** - 样式框架
- **React Router** - 路由管理
- **Vite** - 构建工具

### 后端
- **Flask** - Web 框架
- **SQLite** - 数据库
- **CORS** - 跨域支持
- **流式响应** - 实时数据传输

## 🛠️ 开发说明

### 环境要求
- Node.js 16+
- Python 3.8+
- npm 或 yarn

### 开发模式
```bash
# 前端开发
cd frontend
npm run dev

# 后端开发
cd backend
python app.py
```

### 构建生产版本
```bash
cd frontend
npm run build
```

## 🔒 安全特性

- API 密钥验证
- 用户数据隔离
- CORS 安全配置
- 路由访问控制

## 📝 使用说明

1. **登录系统**
   - 输入用户ID、用户名和API密钥
   - 系统会验证并保存登录状态

2. **上传数据**
   - 拖拽 CSV 文件到上传区域
   - 系统自动解析并导入数据

3. **数据分析**
   - 在分析界面输入问题
   - 系统提供智能分析结果
   - 支持多轮对话

4. **管理对话**
   - 查看历史对话
   - 创建新的分析会话
   - 删除不需要的对话

## 🚨 注意事项

- 确保后端服务先启动，前端才能正常工作
- CSV 文件大小限制为 100MB
- 需要有效的 API 密钥才能使用分析功能
- 建议使用现代浏览器以获得最佳体验

## 🔄 兼容性说明

- ✅ 完全兼容现有后端 API
- ✅ 保留原有 `test_frontend.html` 作为备用
- ✅ 支持渐进式迁移
- ✅ 无需修改后端代码

## 📞 技术支持

如遇到问题，请检查：
1. 后端服务是否正常启动
2. 前端依赖是否正确安装
3. 浏览器控制台是否有错误信息
4. API 密钥是否有效