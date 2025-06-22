# 记忆管理功能文档

## 📖 功能概述

记忆管理模块是DataAnalyzer的独立功能组件，专门用于分析和优化对话历史记忆，减少token消耗，提高分析效率。

## 🏗️ 架构设计

### 核心组件

1. **MemoryManager** (`backend/memory_manager.py`)
   - 独立的记忆分析器
   - 使用LLM分析对话历史
   - 提供记忆操作工具集

2. **Memory API** (`backend/memory_api.py`)
   - 独立的Flask API服务
   - 提供HTTP接口访问记忆管理功能
   - 完全独立于主程序运行

3. **启动脚本** (`start_memory_service.py`)
   - 独立启动记忆管理服务
   - 可配置服务参数

## 🚀 快速开始

### 1. 启动记忆管理服务

```bash
# 方式1：使用启动脚本
python start_memory_service.py

# 方式2：直接运行API
cd backend
python memory_api.py
```

### 2. 配置环境变量

```bash
# 必需配置
export ANTHROPIC_API_KEY=sk-your-api-key-here

# 可选配置
export MEMORY_HOST=localhost
export MEMORY_PORT=5002
export MEMORY_DEBUG=False
```

### 3. 测试功能

```bash
# 运行测试脚本
python test_memory_manager.py

# 查看使用说明
python test_memory_manager.py --help
```

## 🔧 API接口

### 基础信息
- **服务地址**: `http://localhost:5002`
- **认证方式**: 请求头传递用户信息和API密钥

### 请求头格式
```http
Content-Type: application/json
X-User-ID: user_id
X-Username: username
X-API-Key: sk-your-api-key
```

### 接口列表

#### 1. 健康检查
```http
GET /memory/health
```

**响应示例**:
```json
{
    "success": true,
    "service": "Memory Management API",
    "status": "running",
    "version": "1.0.0"
}
```

#### 2. 获取对话列表
```http
POST /memory/conversations
```

**响应示例**:
```json
{
    "success": true,
    "conversations": [
        {
            "conversation_id": "conv_123",
            "conversation_name": "数据分析会话",
            "description": "CSV数据分析",
            "created_time": "2025-06-21T10:00:00",
            "last_activity": "2025-06-21T15:30:00",
            "message_count": 25,
            "status": "active"
        }
    ]
}
```

#### 3. 获取记忆统计
```http
POST /memory/stats
```

**请求体**:
```json
{
    "conversation_id": "conv_123"
}
```

**响应示例**:
```json
{
    "success": true,
    "total_messages": 25,
    "active_messages": 20,
    "deleted_messages": 3,
    "important_messages": 5,
    "memory_summaries": 2,
    "estimated_tokens": 1500
}
```

#### 4. 分析对话记忆
```http
POST /memory/analyze
```

**请求体**:
```json
{
    "conversation_id": "conv_123"
}
```

**响应示例**:
```json
{
    "success": true,
    "analysis_steps": ["获取消息", "分析重要性", "执行优化"],
    "operations_performed": [
        {
            "tool": "delete_message",
            "input": {"message_id": "msg_456", "reason": "重复确认"},
            "result": {"success": true, "message": "消息已删除"}
        }
    ],
    "statistics": {
        "messages_deleted": 3,
        "summaries_added": 1,
        "tokens_saved": 200
    },
    "summary": "已优化对话记忆，删除3条冗余消息，添加1条记忆总结"
}
```

## 🧠 记忆分析逻辑

### 分析原则
1. **保留核心业务逻辑和重要结论**
2. **删除冗余和无价值的交互**
3. **生成简洁但完整的记忆总结**
4. **确保优化后的对话仍然有完整的上下文**

### 删除策略
- 重复的询问或确认
- 简单的"好的"、"明白"等回复
- 错误的尝试或无效的查询
- 冗余的中间步骤

### 保留策略
- 重要的数据分析结果
- 关键的业务结论
- 用户的核心需求
- 有价值的洞察和发现

## 🛠️ 记忆操作工具

### 1. get_conversation_messages
- **功能**: 获取对话中的所有消息
- **参数**: conversation_id

### 2. delete_message
- **功能**: 标记删除指定消息（软删除）
- **参数**: message_id, reason

### 3. add_memory_summary
- **功能**: 添加记忆总结到对话中
- **参数**: summary_content, summary_type

### 4. mark_important_message
- **功能**: 标记重要消息（确保不被删除）
- **参数**: message_id, importance_level, reason

### 5. get_memory_stats
- **功能**: 获取记忆统计信息
- **参数**: conversation_id

## 📊 数据结构

### 消息标记字段
```json
{
    "id": "message_id",
    "content": "消息内容",
    "role": "user|assistant|system",
    
    // 删除标记
    "deleted": true,
    "deleted_at": "2025-06-21T15:30:00",
    "deleted_reason": "重复确认",
    
    // 重要性标记
    "important": true,
    "importance_level": "critical|important|normal",
    "importance_reason": "关键业务结论",
    "marked_important_at": "2025-06-21T15:30:00",
    
    // 记忆总结标记
    "is_memory_summary": true,
    "summary_type": "key_points|data_insights|conclusions",
    "type": "memory_summary"
}
```

## 🔒 安全考虑

1. **API密钥保护**: 所有LLM调用都需要有效的API密钥
2. **用户隔离**: 每个用户只能访问自己的对话记录
3. **软删除**: 使用标记删除，数据可恢复
4. **日志记录**: 所有操作都有详细日志

## 📈 性能优化

1. **独立服务**: 记忆管理作为独立服务运行，不影响主程序性能
2. **按需分析**: 只有用户主动触发才进行记忆分析
3. **批量操作**: 支持批量处理多个记忆操作
4. **缓存机制**: 统计信息可以缓存以提高响应速度

## 🚨 故障处理

### 常见问题

1. **API密钥无效**
   - 检查ANTHROPIC_API_KEY环境变量
   - 确认API密钥有效且有足够额度

2. **数据库文件不存在**
   - 确认用户有对话记录
   - 检查数据目录权限

3. **服务连接失败**
   - 确认记忆管理服务已启动
   - 检查端口是否被占用

### 错误代码
- **400**: 请求参数错误
- **404**: 对话记录不存在
- **500**: 服务器内部错误

## 🔄 工作流程

1. **用户触发** → 用户点击"优化对话记忆"
2. **读取历史** → 从history.db读取对话消息
3. **LLM分析** → 使用独立LLM分析记忆价值
4. **展示结果** → 向用户展示分析结果和建议操作
5. **用户确认** → 用户确认或修改优化方案
6. **执行优化** → 标记删除、添加总结、标记重要消息
7. **完成反馈** → 返回优化结果和统计信息

## 📝 使用示例

### Python客户端示例
```python
import requests

# 配置
base_url = "http://localhost:5002"
headers = {
    'Content-Type': 'application/json',
    'X-User-ID': 'your_user_id',
    'X-API-Key': 'sk-your-api-key'
}

# 获取对话列表
response = requests.post(f"{base_url}/memory/conversations", 
                        headers=headers, json={})
conversations = response.json()['conversations']

# 分析记忆
conversation_id = conversations[0]['conversation_id']
response = requests.post(f"{base_url}/memory/analyze",
                        headers=headers,
                        json={"conversation_id": conversation_id})
result = response.json()
print(f"优化结果: {result['summary']}")
```

### JavaScript客户端示例
```javascript
const baseUrl = 'http://localhost:5002';
const headers = {
    'Content-Type': 'application/json',
    'X-User-ID': 'your_user_id',
    'X-API-Key': 'sk-your-api-key'
};

// 分析记忆
async function analyzeMemory(conversationId) {
    const response = await fetch(`${baseUrl}/memory/analyze`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
            conversation_id: conversationId
        })
    });
    
    const result = await response.json();
    console.log('优化结果:', result.summary);
    return result;
}
```

## 🎯 未来扩展

1. **批量分析**: 支持同时分析多个对话
2. **自动优化**: 定期自动执行记忆优化
3. **智能建议**: 基于历史数据提供优化建议
4. **可视化界面**: 提供Web界面进行记忆管理
5. **导出功能**: 支持导出优化报告和统计数据 