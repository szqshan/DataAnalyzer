# 智能数据库分析系统 (DataAnalyzer)

一个基于Python和Flask的智能数据库分析系统，提供直观的Web界面和强大的数据分析能力。

## 🌟 功能特点

- 📊 智能数据分析：支持多种数据格式的导入和分析
- 🔍 交互式查询：提供友好的用户界面进行数据查询
- 📈 可视化展示：自动生成数据分析和可视化报告
- 🔐 用户认证：支持多用户管理和权限控制
- 🌐 Web界面：基于Flask的现代化Web应用

## 🚀 快速开始

### 系统要求

- Python 3.7+
- 现代浏览器（Chrome、Firefox、Edge等）

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/szqshan/DataAnalyzer.git
cd DataAnalyzer
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量
创建 `.env` 文件并添加以下内容：
```
ANTHROPIC_API_KEY=your_api_key_here
HOST=0.0.0.0
PORT=5000
```

4. 启动系统
```bash
python start.py
```

5. 访问系统
- 前端界面：http://localhost:8080
- 后端API：http://localhost:5000/api

## 📁 项目结构

```
DataAnalyzer/
├── backend/           # 后端服务
├── frontend/          # 前端界面
├── data/             # 数据存储
├── docs/             # 文档
├── logs/             # 日志文件
├── reports/          # 分析报告
├── uploads/          # 上传文件
├── users/            # 用户数据
├── start.py          # 启动脚本
└── requirements.txt  # 依赖列表
```

## 🔧 配置说明

### 环境变量

- `ANTHROPIC_API_KEY`: Anthropic API密钥
- `HOST`: 服务器主机地址
- `PORT`: 服务器端口

### 目录说明

- `data/`: 存储分析数据
- `logs/`: 系统运行日志
- `reports/`: 生成的分析报告
- `uploads/`: 用户上传的文件
- `users/`: 用户相关数据

## 📝 使用说明

1. 启动系统后，通过浏览器访问前端界面
2. 登录系统（默认管理员账号）
3. 上传数据文件或连接数据库
4. 使用分析工具进行数据处理
5. 查看生成的分析报告

## 🤝 贡献指南

欢迎提交Issue和Pull Request来帮助改进项目！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 📄 开源协议

本项目采用 MIT 协议 - 详见 [LICENSE](LICENSE) 文件

## 👥 作者

- 山志强 (szqshan) - [GitHub](https://github.com/szqshan)

## 🙏 致谢

感谢所有为本项目做出贡献的开发者！ 