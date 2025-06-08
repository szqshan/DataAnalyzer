# 智能数据库分析系统 (DataAnalyzer)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

一个基于Claude API的智能数据库分析系统，支持多用户协作和实时数据分析。

## 🌟 功能特点

### 核心功能
- 🔍 智能数据分析
  - 自动识别数据类型和结构
  - 智能生成分析报告
  - 支持多种数据源分析
  
- 📊 数据可视化
  - 自动生成图表
  - 交互式数据展示
  - 支持多种图表类型

- 👥 多用户支持
  - 独立的用户空间
  - 数据访问控制
  - 协作分析功能

### 技术特性
- 🔒 安全性
  - 用户认证系统
  - API密钥管理
  - 数据加密存储

- 🚀 性能
  - 异步处理
  - 缓存优化
  - 分布式支持

## 🛠️ 安装说明

### 环境要求
- Python 3.8+
- SQLite 3
- 现代浏览器（Chrome/Firefox/Safari）

### 快速开始

1. 克隆仓库
```bash
git clone https://github.com/szqshan/DataAnalyzer.git
cd DataAnalyzer
```

2. 创建虚拟环境
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 设置环境变量
```bash
# Windows
set ANTHROPIC_API_KEY=你的API密钥

# Linux/Mac
export ANTHROPIC_API_KEY=你的API密钥
```

5. 启动服务
```bash
python run_server.py
```

## 📖 使用指南

### 基本使用流程

1. **数据导入**
   - 支持CSV文件导入
   - 支持数据库直连
   - 支持API数据源

2. **数据分析**
   - 选择分析模板
   - 设置分析参数
   - 执行分析任务

3. **结果查看**
   - 查看分析报告
   - 导出分析结果
   - 分享分析见解

### 高级功能

- **自定义分析模板**
- **批量数据处理**
- **定时分析任务**
- **协作分析项目**

## 🤝 参与贡献

我们欢迎各种形式的贡献，包括但不限于：

- 提交bug报告
- 新功能建议
- 代码贡献
- 文档改进

请查看[贡献指南](CONTRIBUTING.md)了解详细信息。

## 📝 文档

- [API文档](docs/API.md)
- [用户指南](docs/UserGuide.md)
- [开发指南](docs/DevelopGuide.md)
- [更新日志](CHANGELOG.md)

## 🔗 相关链接

- [项目主页](https://github.com/szqshan/DataAnalyzer)
- [问题反馈](https://github.com/szqshan/DataAnalyzer/issues)
- [开发计划](https://github.com/szqshan/DataAnalyzer/projects)

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详细信息。

## 👥 团队

- 项目负责人：szqshan
- 开发团队：[团队成员列表]
- 贡献者：[贡献者列表]

## 📞 联系方式

- 电子邮件：[项目邮箱]
- 讨论组：[讨论组链接]
- 社交媒体：[社交媒体链接]

## 🙏 鸣谢

感谢所有为本项目做出贡献的开发者和用户。特别感谢：

- Anthropic提供的Claude API支持
- 所有开源依赖项目的贡献者