# 协作者指南

欢迎加入智能数据库分析系统的开发团队！本文档将帮助您了解如何参与项目开发。

## 目录

- [开发环境设置](#开发环境设置)
- [分支管理](#分支管理)
- [代码提交规范](#代码提交规范)
- [代码审查流程](#代码审查流程)
- [发布流程](#发布流程)
- [文档维护](#文档维护)

## 开发环境设置

1. **克隆仓库**
```bash
git clone git@github.com:szqshan/DataAnalyzer.git
cd DataAnalyzer
```

2. **安装依赖**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

3. **设置环境变量**
```bash
# Windows
set ANTHROPIC_API_KEY=你的API密钥

# Linux/Mac
export ANTHROPIC_API_KEY=你的API密钥
```

## 分支管理

### 分支说明
- `master`: 生产环境分支，存放稳定版本
- `develop`: 开发主分支，所有特性开发基于此分支
- `feature/*`: 特性开发分支
- `bugfix/*`: 错误修复分支
- `release/*`: 版本发布分支
- `hotfix/*`: 紧急修复分支

### 分支命名规范
- 特性分支：`feature/功能描述`
  - 例：`feature/add-user-authentication`
- 修复分支：`bugfix/问题描述`
  - 例：`bugfix/fix-memory-leak`
- 发布分支：`release/版本号`
  - 例：`release/v1.1.0`
- 热修复分支：`hotfix/问题描述`
  - 例：`hotfix/fix-critical-security-issue`

### 工作流程

1. **开发新功能**
```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
# 开发完成后
git add .
git commit -m "feat: 添加新功能描述"
git push origin feature/your-feature-name
# 在GitHub上创建Pull Request到develop分支
```

2. **修复Bug**
```bash
git checkout develop
git pull origin develop
git checkout -b bugfix/bug-description
# 修复完成后
git add .
git commit -m "fix: 修复问题描述"
git push origin bugfix/bug-description
# 在GitHub上创建Pull Request到develop分支
```

3. **发布版本**
```bash
git checkout develop
git pull origin develop
git checkout -b release/v1.x.x
# 测试和修复完成后
git push origin release/v1.x.x
# 在GitHub上创建Pull Request到master分支
```

## 代码提交规范

### Commit消息格式
```
<类型>: <描述>

[可选的正文]

[可选的脚注]
```

### 类型说明
- `feat`: 新功能
- `fix`: 修复Bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

### 示例
```bash
git commit -m "feat: 添加用户认证功能

添加了基于JWT的用户认证系统，包括：
- 用户登录接口
- Token验证中间件
- 用户信息存储

Closes #123"
```

## 代码审查流程

1. **创建Pull Request**
   - 标题清晰描述变更内容
   - 填写完整的描述信息
   - 关联相关的Issue

2. **审查清单**
   - 代码符合Python PEP 8规范
   - 包含必要的单元测试
   - 文档已更新
   - 无安全漏洞
   - 性能影响在可接受范围内

3. **合并规则**
   - 至少一个审查者批准
   - 所有CI检查通过
   - 无合并冲突

## 发布流程

1. **版本号规范**
   - 主版本号：重大更新，不兼容的API修改
   - 次版本号：向下兼容的功能性新增
   - 修订号：向下兼容的问题修正

2. **发布步骤**
   - 从develop分支创建release分支
   - 更新版本号和更新日志
   - 进行完整测试
   - 合并到master分支
   - 在GitHub创建Release标签

## 文档维护

1. **需要维护的文档**
   - README.md：项目总体说明
   - CONTRIBUTING.md：协作指南
   - API.md：API文档
   - CHANGELOG.md：更新日志

2. **文档更新时机**
   - 添加新功能时
   - 修改现有功能时
   - 修复重要Bug时
   - 发布新版本时

## 其他注意事项

1. **代码风格**
   - 遵循Python PEP 8规范
   - 使用4个空格缩进
   - 最大行长度120字符
   - 使用有意义的变量和函数名

2. **测试要求**
   - 新功能必须包含单元测试
   - 修复bug必须包含相关测试用例
   - 测试覆盖率不低于80%

3. **性能考虑**
   - 大型数据处理需要考虑内存使用
   - 添加适当的日志记录
   - 注意API调用频率限制

4. **安全事项**
   - 不要提交敏感信息
   - 及时更新依赖包
   - 注意数据安全和用户隐私

## 获取帮助

如果您在开发过程中遇到任何问题，可以：
1. 查看项目文档
2. 搜索已有的Issues
3. 创建新的Issue
4. 联系项目维护者

## 联系方式

- 项目维护者：[维护者姓名]
- 邮箱：[邮箱地址]
- 项目讨论组：[讨论组链接]

感谢您的贡献！ 