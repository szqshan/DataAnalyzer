# GitHub使用指南

本文档提供了如何将本地代码更新推送到GitHub的详细步骤。

## 基本概念

- **仓库(Repository)**: 存储项目代码的地方
- **分支(Branch)**: 代码的不同版本线
- **提交(Commit)**: 代码的一次保存点
- **推送(Push)**: 将本地更改上传到远程仓库
- **拉取(Pull)**: 从远程仓库下载更新
- **合并(Merge)**: 将一个分支的更改应用到另一个分支

## 推送更新到GitHub的步骤

### 1. 确认当前状态

```bash
git status
```

这个命令会显示:
- 当前所在分支
- 有哪些文件被修改
- 有哪些文件已暂存准备提交
- 有哪些文件未被Git跟踪

### 2. 添加修改的文件

将修改的文件添加到暂存区:

```bash
# 添加单个文件
git add 文件名

# 添加多个文件
git add 文件名1 文件名2

# 添加所有修改的文件
git add .
```

### 3. 提交更改

将暂存区的更改提交到本地仓库:

```bash
git commit -m "提交说明"
```

提交说明应简洁明了地描述此次更改的内容，建议遵循以下格式:
- `feat: 添加新功能`
- `fix: 修复问题`
- `docs: 更新文档`
- `style: 代码格式调整`
- `refactor: 代码重构`
- `test: 添加测试`
- `chore: 构建过程或辅助工具的变动`

### 4. 推送到GitHub

将本地提交推送到GitHub:

```bash
# 推送到当前分支
git push origin 当前分支名

# 示例: 推送到master分支
git push origin master

# 示例: 推送到feature分支
git push origin feature/新功能
```

## 分支操作

### 查看分支

```bash
# 查看本地分支
git branch

# 查看远程分支
git branch -r

# 查看所有分支
git branch -a
```

### 创建新分支

```bash
# 创建并切换到新分支
git checkout -b 新分支名

# 示例
git checkout -b feature/user-login
```

### 切换分支

```bash
git checkout 分支名
```

### 合并分支

```bash
# 先切换到目标分支
git checkout master

# 然后合并其他分支的更改
git merge 源分支名

# 示例: 将feature分支合并到master
git checkout master
git merge feature/user-login
```

## 常见问题处理

### 1. 合并冲突

当两个分支修改了同一文件的同一部分时，可能会发生合并冲突。Git会在文件中标记冲突区域:

```
<<<<<<< HEAD
当前分支的代码
=======
要合并的分支的代码
>>>>>>> feature/branch-name
```

解决步骤:
1. 打开有冲突的文件
2. 编辑文件解决冲突(删除标记符号，保留需要的代码)
3. 保存文件
4. 使用`git add`添加解决冲突的文件
5. 使用`git commit`完成合并

### 2. 撤销本地更改

```bash
# 撤销工作区的修改
git checkout -- 文件名

# 撤销已暂存的修改
git reset HEAD 文件名
git checkout -- 文件名

# 撤销最近一次提交
git reset --soft HEAD^
```

### 3. 拉取远程更新

```bash
# 拉取并合并远程更改
git pull origin 分支名

# 或者分两步
git fetch origin
git merge origin/分支名
```

## 身份验证信息

每次推送到GitHub时，系统会要求您提供身份验证信息:

1. **用户名**: 您的GitHub用户名
2. **密码/令牌**: 
   - 如果启用了双重认证，需使用个人访问令牌(PAT)
   - 或者使用SSH密钥认证

### 设置个人访问令牌(PAT)

1. 在GitHub网站上:
   - 点击右上角头像
   - 选择`Settings`
   - 选择`Developer settings`
   - 选择`Personal access tokens`
   - 点击`Generate new token`

2. 配置令牌:
   - 添加令牌描述
   - 选择权限范围(至少需要`repo`权限)
   - 点击`Generate token`
   - 复制生成的令牌(只显示一次!)

3. 使用令牌:
   - 当Git提示输入密码时，输入此令牌

### 设置SSH认证

1. 生成SSH密钥:
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

2. 将公钥添加到GitHub:
   - 复制`~/.ssh/id_ed25519.pub`的内容
   - 在GitHub设置中添加SSH密钥

3. 测试连接:
```bash
ssh -T git@github.com
```

## 工作流建议

1. **定期拉取更新**:
```bash
git pull origin 分支名
```

2. **使用特性分支**:
```bash
git checkout -b feature/新功能
# 开发完成后
git push origin feature/新功能
# 在GitHub上创建Pull Request
```

3. **提交前检查**:
```bash
git diff  # 查看更改
git status  # 确认状态
```

4. **保持提交小而频繁**:
每个提交应该代表一个逻辑上完整的更改。

## 参考资源

- [GitHub官方文档](https://docs.github.com/cn)
- [Git官方文档](https://git-scm.com/doc)
- [GitHub Desktop](https://desktop.github.com/) - 图形界面客户端
- [Visual Studio Code的Git集成](https://code.visualstudio.com/docs/editor/versioncontrol)

---

如有任何问题，请联系项目维护者。 