# 📖 API调用示例代码文档

本文档提供了智能数据库分析系统所有API接口的详细调用示例，包括JavaScript、Python、curl等多种调用方式。

> **🔑 重要更新 (v1.1.0)：** 系统已升级为用户专属API Key架构，每个用户需要使用自己的API密钥。

**📋 快速导航：**
- [🔧 基础配置](#基础配置)
- [🔐 用户认证](#用户认证)  
- [🏥 系统状态接口](#系统状态接口)
- [📁 数据管理接口](#数据管理接口)
- [🤖 数据分析接口](#数据分析接口)
- [💬 对话管理接口](#对话管理接口)
- [✉️ 消息管理接口](#消息管理接口)
- [❌ 错误处理](#错误处理)
- [🎯 完整示例](#完整示例)

## 📋 目录

- [基础配置](#基础配置)
- [用户认证](#用户认证)
- [系统状态接口](#系统状态接口)
- [数据管理接口](#数据管理接口)
- [数据分析接口](#数据分析接口)
- [对话管理接口](#对话管理接口)
- [消息管理接口](#消息管理接口)
- [错误处理](#错误处理)
- [完整示例](#完整示例)

## 🔧 基础配置

### JavaScript 配置

```javascript
// API基础配置
const API_BASE_URL = 'http://localhost:5000/api';

// 用户信息配置
const USER_CONFIG = {
    userId: 'user123',
    username: '张三',
    apiKey: 'sk-ant-api-your-api-key-here'  // 🔑 v1.1.0新增：用户专属API Key
};

// 通用请求头
const getHeaders = (additionalHeaders = {}) => {
    return {
        'Content-Type': 'application/json',
        'X-User-ID': USER_CONFIG.userId,
        'X-Username': encodeURIComponent(USER_CONFIG.username),
        'X-API-Key': USER_CONFIG.apiKey,  // 🔑 v1.1.0新增：API Key认证
        ...additionalHeaders
    };
};

// 通用错误处理
const handleResponse = async (response) => {
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
};
```

### Python 配置

```python
import requests
import json
from urllib.parse import quote

# API基础配置
API_BASE_URL = 'http://localhost:5000/api'

# 用户信息配置
USER_CONFIG = {
    'userId': 'user123',
    'username': '张三',
    'apiKey': 'sk-ant-api-your-api-key-here'  # 🔑 v1.1.0新增：用户专属API Key
}

# 通用请求头
def get_headers(additional_headers=None):
    headers = {
        'Content-Type': 'application/json',
        'X-User-ID': USER_CONFIG['userId'],
        'X-Username': quote(USER_CONFIG['username']),
        'X-API-Key': USER_CONFIG['apiKey']  # 🔑 v1.1.0新增：API Key认证
    }
    if additional_headers:
        headers.update(additional_headers)
    return headers

# 通用错误处理
def handle_response(response):
    if not response.ok:
        try:
            error_data = response.json()
            raise Exception(error_data.get('message', f'HTTP {response.status_code}'))
        except:
            raise Exception(f'HTTP {response.status_code}: {response.reason}')
    return response.json()
```

## 🔐 用户认证

### 方式1：请求头认证（推荐）

```javascript
// JavaScript
const response = await fetch(`${API_BASE_URL}/status`, {
    method: 'GET',
    headers: {
        'X-User-ID': 'user123',
        'X-Username': encodeURIComponent('张三')
    }
});
```

```python
# Python
headers = {
    'X-User-ID': 'user123',
    'X-Username': quote('张三')
}
response = requests.get(f'{API_BASE_URL}/status', headers=headers)
```

```bash
# curl
curl -X GET "http://localhost:5000/api/status" \
  -H "X-User-ID: user123" \
  -H "X-Username: %E5%BC%A0%E4%B8%89" \
  -H "X-API-Key: sk-ant-api-your-api-key-here"
```

### 方式2：URL参数认证

```javascript
// JavaScript
const params = new URLSearchParams({
    userId: 'user123',
    username: '张三'
});
const response = await fetch(`${API_BASE_URL}/status?${params}`);
```

```python
# Python
params = {'userId': 'user123', 'username': '张三'}
response = requests.get(f'{API_BASE_URL}/status', params=params)
```

```bash
# curl
curl -X GET "http://localhost:5000/api/status?userId=user123&username=%E5%BC%A0%E4%B8%89"
```

### 方式3：请求体认证

```javascript
// JavaScript
const response = await fetch(`${API_BASE_URL}/analyze-stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        userId: 'user123',
        username: '张三',
        query: '分析数据'
    })
});
```

## 🏥 系统状态接口

### GET /api/health - 健康检查

```javascript
// JavaScript
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await handleResponse(response);
        console.log('系统状态:', data);
        return data;
    } catch (error) {
        console.error('健康检查失败:', error);
        throw error;
    }
}

// 调用示例
checkHealth().then(data => {
    console.log('系统正常:', data.status === 'healthy');
});
```

```python
# Python
def check_health():
    try:
        response = requests.get(f'{API_BASE_URL}/health')
        data = handle_response(response)
        print('系统状态:', data)
        return data
    except Exception as error:
        print('健康检查失败:', error)
        raise

# 调用示例
health_data = check_health()
print('系统正常:', health_data.get('status') == 'healthy')
```

```bash
# curl
curl -X GET "http://localhost:5000/api/health"
```

### GET /api/status - 系统状态

```javascript
// JavaScript
async function getSystemStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/status`, {
            headers: getHeaders()
        });
        const data = await handleResponse(response);
        console.log('系统状态详情:', data);
        return data;
    } catch (error) {
        console.error('获取系统状态失败:', error);
        throw error;
    }
}

// 调用示例
getSystemStatus().then(data => {
    console.log('数据库已连接:', data.database_connected);
    console.log('记录数量:', data.record_count);
});
```

```python
# Python
def get_system_status():
    try:
        response = requests.get(f'{API_BASE_URL}/status', headers=get_headers())
        data = handle_response(response)
        print('系统状态详情:', data)
        return data
    except Exception as error:
        print('获取系统状态失败:', error)
        raise

# 调用示例
status_data = get_system_status()
print('数据库已连接:', status_data.get('database_connected'))
print('记录数量:', status_data.get('record_count'))
```

## 📁 数据管理接口

### POST /api/upload - 上传CSV文件

```javascript
// JavaScript
async function uploadCSV(file, tableName = 'data_table') {
    try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('tableName', tableName);
        formData.append('userId', USER_CONFIG.userId);
        formData.append('username', USER_CONFIG.username);

        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        });

        const data = await handleResponse(response);
        console.log('上传成功:', data);
        return data;
    } catch (error) {
        console.error('上传失败:', error);
        throw error;
    }
}

// HTML文件选择器调用示例
document.getElementById('fileInput').addEventListener('change', async (event) => {
    const file = event.target.files[0];
    if (file && file.name.endsWith('.csv')) {
        try {
            const result = await uploadCSV(file);
            alert(`成功导入 ${result.data.rows_imported} 行数据`);
        } catch (error) {
            alert('上传失败: ' + error.message);
        }
    }
});
```

```python
# Python
def upload_csv(file_path, table_name='data_table'):
    try:
        with open(file_path, 'rb') as file:
            files = {'file': file}
            data = {
                'tableName': table_name,
                'userId': USER_CONFIG['userId'],
                'username': USER_CONFIG['username']
            }
            
            response = requests.post(f'{API_BASE_URL}/upload', files=files, data=data)
            result = handle_response(response)
            print('上传成功:', result)
            return result
    except Exception as error:
        print('上传失败:', error)
        raise

# 调用示例
result = upload_csv('data.csv', 'my_table')
print(f"成功导入 {result['data']['rows_imported']} 行数据")
```

```bash
# curl
curl -X POST "http://localhost:5000/api/upload" \
  -F "file=@data.csv" \
  -F "tableName=data_table" \
  -F "userId=user123" \
  -F "username=张三"
```

## 🤖 数据分析接口

### POST /api/analyze-stream - 流式AI分析

```javascript
// JavaScript - 使用fetch进行流式接收
async function analyzeDataStream(query) {
    try {
        // 发送分析请求
        const response = await fetch(`${API_BASE_URL}/analyze-stream`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({
                userId: USER_CONFIG.userId,
                username: USER_CONFIG.username,
                query: query
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        // 处理流式响应
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // 保留不完整的行

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        handleStreamData(data);
                    } catch (e) {
                        console.warn('解析流数据失败:', line);
                    }
                }
            }
        }
    } catch (error) {
        console.error('分析失败:', error);
        throw error;
    }
}

// 处理流式数据
function handleStreamData(data) {
    switch (data.type) {
        case 'status':
            console.log('状态:', data.message);
            break;
        case 'progress':
            console.log('进度:', data.step, '-', data.message);
            break;
        case 'content':
            console.log('内容:', data.content);
            // 可以在这里更新UI显示AI回复
            break;
        case 'complete':
            console.log('分析完成，对话ID:', data.conversation_id);
            break;
        case 'error':
            console.error('分析错误:', data.message);
            break;
    }
}

// 调用示例
analyzeDataStream('分析用户年龄分布情况').then(() => {
    console.log('分析流程启动成功');
}).catch(error => {
    console.error('分析启动失败:', error);
});
```

```python
# Python - 使用requests的流式处理
import json

def analyze_data_stream(query):
    try:
        payload = {
            'userId': USER_CONFIG['userId'],
            'username': USER_CONFIG['username'],
            'query': query
        }
        
        response = requests.post(
            f'{API_BASE_URL}/analyze-stream',
            headers=get_headers(),
            json=payload,
            stream=True
        )
        
        if not response.ok:
            raise Exception(f'HTTP {response.status_code}: {response.reason}')
        
        # 处理流式响应
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith('data: '):
                try:
                    data = json.loads(line[6:])
                    handle_stream_data(data)
                except json.JSONDecodeError:
                    print(f'解析流数据失败: {line}')
                    
    except Exception as error:
        print('分析失败:', error)
        raise

def handle_stream_data(data):
    data_type = data.get('type')
    if data_type == 'status':
        print('状态:', data.get('message'))
    elif data_type == 'progress':
        print('进度:', data.get('step'), '-', data.get('message'))
    elif data_type == 'content':
        print('内容:', data.get('content'))
    elif data_type == 'complete':
        print('分析完成，对话ID:', data.get('conversation_id'))
    elif data_type == 'error':
        print('分析错误:', data.get('message'))

# 调用示例
analyze_data_stream('分析用户年龄分布情况')
```

## 💬 对话管理接口

### POST /api/conversations/create - 创建新对话

```javascript
// JavaScript
async function createNewConversation(name, description = '') {
    try {
        const response = await fetch(`${API_BASE_URL}/conversations/create`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({
                userId: USER_CONFIG.userId,
                username: USER_CONFIG.username,
                conversation_name: name,
                description: description
            })
        });

        const data = await handleResponse(response);
        console.log('新对话创建成功:', data);
        return data;
    } catch (error) {
        console.error('创建对话失败:', error);
        throw error;
    }
}

// 调用示例
createNewConversation('数据分析对话', '关于销售数据的分析').then(conversation => {
    console.log('对话ID:', conversation.conversation_id);
});
```

```python
# Python
def create_new_conversation(name, description=''):
    try:
        payload = {
            'userId': USER_CONFIG['userId'],
            'username': USER_CONFIG['username'],
            'conversation_name': name,
            'description': description
        }
        
        response = requests.post(
            f'{API_BASE_URL}/conversations/create',
            headers=get_headers(),
            json=payload
        )
        
        data = handle_response(response)
        print('新对话创建成功:', data)
        return data
    except Exception as error:
        print('创建对话失败:', error)
        raise

# 调用示例
conversation = create_new_conversation('数据分析对话', '关于销售数据的分析')
print('对话ID:', conversation.get('conversation_id'))
```

### GET /api/conversations/list - 获取对话列表

```javascript
// JavaScript
async function getConversationsList() {
    try {
        const response = await fetch(`${API_BASE_URL}/conversations/list`, {
            headers: getHeaders()
        });

        const data = await handleResponse(response);
        console.log('对话列表:', data);
        return data.conversations || [];
    } catch (error) {
        console.error('获取对话列表失败:', error);
        throw error;
    }
}

// 调用示例
getConversationsList().then(conversations => {
    conversations.forEach(conv => {
        console.log(`${conv.conversation_name} (${conv.message_count}条消息)`);
    });
});
```

### POST /api/conversations/switch - 切换对话

```javascript
// JavaScript
async function switchConversation(conversationId) {
    try {
        const response = await fetch(`${API_BASE_URL}/conversations/switch`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({
                userId: USER_CONFIG.userId,
                conversation_id: conversationId
            })
        });

        const data = await handleResponse(response);
        console.log('切换对话成功:', data);
        return data;
    } catch (error) {
        console.error('切换对话失败:', error);
        throw error;
    }
}

// 调用示例
switchConversation('conv_20240101_120000_001').then(() => {
    console.log('已切换到指定对话');
});
```

### GET /api/conversations/stats - 获取对话统计

```javascript
// JavaScript
async function getConversationStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/conversations/stats`, {
            headers: getHeaders()
        });

        const data = await handleResponse(response);
        console.log('对话统计:', data.stats);
        return data.stats;
    } catch (error) {
        console.error('获取统计失败:', error);
        throw error;
    }
}

// 调用示例
getConversationStats().then(stats => {
    console.log(`总对话数: ${stats.total_conversations}`);
    console.log(`总消息数: ${stats.total_messages}`);
    console.log(`平均每对话消息数: ${stats.avg_messages_per_conversation}`);
});
```

## ❌ 错误处理

### 通用错误处理模式

```javascript
// JavaScript - 统一错误处理
class APIError extends Error {
    constructor(message, status, response) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.response = response;
    }
}

async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: getHeaders(),
            ...options
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new APIError(
                errorData.message || `HTTP ${response.status}`,
                response.status,
                errorData
            );
        }

        return await response.json();
    } catch (error) {
        if (error instanceof APIError) {
            throw error;
        }
        throw new APIError('网络请求失败', 0, { originalError: error });
    }
}

// 使用示例
try {
    const data = await apiRequest(`${API_BASE_URL}/status`);
    console.log('请求成功:', data);
} catch (error) {
    if (error instanceof APIError) {
        switch (error.status) {
            case 400:
                console.error('请求参数错误:', error.message);
                break;
            case 401:
                console.error('认证失败:', error.message);
                break;
            case 500:
                console.error('服务器错误:', error.message);
                break;
            default:
                console.error('请求失败:', error.message);
        }
    } else {
        console.error('未知错误:', error);
    }
}
```

## 🎯 完整示例

### 完整的数据分析流程

```javascript
// JavaScript - 完整的数据分析流程示例
class DataAnalyzer {
    constructor(apiBaseUrl, userId, username) {
        this.apiBaseUrl = apiBaseUrl;
        this.userId = userId;
        this.username = username;
        this.currentConversationId = null;
    }

    getHeaders(additionalHeaders = {}) {
        return {
            'Content-Type': 'application/json',
            'X-User-ID': this.userId,
            'X-Username': encodeURIComponent(this.username),
            ...additionalHeaders
        };
    }

    async handleResponse(response) {
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    }

    // 1. 检查系统状态
    async checkSystemStatus() {
        const response = await fetch(`${this.apiBaseUrl}/status`, {
            headers: this.getHeaders()
        });
        return this.handleResponse(response);
    }

    // 2. 上传CSV文件
    async uploadCSV(file, tableName = 'data_table') {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('tableName', tableName);
        formData.append('userId', this.userId);
        formData.append('username', this.username);

        const response = await fetch(`${this.apiBaseUrl}/upload`, {
            method: 'POST',
            body: formData
        });
        return this.handleResponse(response);
    }

    // 3. 创建新对话
    async createConversation(name, description = '') {
        const response = await fetch(`${this.apiBaseUrl}/conversations/create`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify({
                userId: this.userId,
                username: this.username,
                conversation_name: name,
                description: description
            })
        });
        const data = await this.handleResponse(response);
        this.currentConversationId = data.conversation_id;
        return data;
    }

    // 4. 执行流式分析
    async analyzeData(query, onProgress = null) {
        const response = await fetch(`${this.apiBaseUrl}/analyze-stream`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify({
                userId: this.userId,
                username: this.username,
                query: query
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let fullResponse = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop();

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        
                        if (onProgress) {
                            onProgress(data);
                        }

                        if (data.type === 'content') {
                            fullResponse += data.content;
                        } else if (data.type === 'complete') {
                            this.currentConversationId = data.conversation_id;
                            return {
                                response: fullResponse,
                                conversationId: data.conversation_id
                            };
                        }
                    } catch (e) {
                        console.warn('解析流数据失败:', line);
                    }
                }
            }
        }

        return { response: fullResponse, conversationId: this.currentConversationId };
    }

    // 5. 获取对话历史
    async getConversationHistory() {
        const response = await fetch(`${this.apiBaseUrl}/conversations/list`, {
            headers: this.getHeaders()
        });
        const data = await this.handleResponse(response);
        return data.conversations || [];
    }
}

// 使用示例
async function completeAnalysisWorkflow() {
    const analyzer = new DataAnalyzer(API_BASE_URL, 'user123', '张三');

    try {
        // 1. 检查系统状态
        console.log('检查系统状态...');
        const status = await analyzer.checkSystemStatus();
        console.log('系统状态:', status);

        // 2. 上传文件（假设已有文件）
        // const uploadResult = await analyzer.uploadCSV(file);
        // console.log('上传结果:', uploadResult);

        // 3. 创建新对话
        console.log('创建新对话...');
        const conversation = await analyzer.createConversation('数据分析会话', '销售数据分析');
        console.log('对话创建成功:', conversation.conversation_id);

        // 4. 执行分析
        console.log('开始分析...');
        const result = await analyzer.analyzeData(
            '请分析数据表中的主要趋势和模式',
            (progressData) => {
                console.log('分析进度:', progressData);
            }
        );
        console.log('分析完成:', result.response);

        // 5. 获取历史记录
        const history = await analyzer.getConversationHistory();
        console.log('对话历史:', history);

    } catch (error) {
        console.error('工作流程失败:', error);
    }
}

// 启动完整工作流程
completeAnalysisWorkflow();
```

### React组件示例

```jsx
// React组件示例
import React, { useState, useEffect } from 'react';

const DataAnalysisComponent = () => {
    const [status, setStatus] = useState(null);
    const [conversations, setConversations] = useState([]);
    const [currentQuery, setCurrentQuery] = useState('');
    const [analysisResult, setAnalysisResult] = useState('');
    const [isAnalyzing, setIsAnalyzing] = useState(false);

    const API_BASE_URL = 'http://localhost:5000/api';
    const USER_CONFIG = { userId: 'user123', username: '张三' };

    const getHeaders = () => ({
        'Content-Type': 'application/json',
        'X-User-ID': USER_CONFIG.userId,
        'X-Username': encodeURIComponent(USER_CONFIG.username)
    });

    // 获取系统状态
    useEffect(() => {
        fetch(`${API_BASE_URL}/status`, { headers: getHeaders() })
            .then(response => response.json())
            .then(data => setStatus(data))
            .catch(error => console.error('获取状态失败:', error));
    }, []);

    // 获取对话列表
    useEffect(() => {
        fetch(`${API_BASE_URL}/conversations/list`, { headers: getHeaders() })
            .then(response => response.json())
            .then(data => setConversations(data.conversations || []))
            .catch(error => console.error('获取对话列表失败:', error));
    }, []);

    // 执行分析
    const handleAnalyze = async () => {
        if (!currentQuery.trim()) return;

        setIsAnalyzing(true);
        setAnalysisResult('');

        try {
            const response = await fetch(`${API_BASE_URL}/analyze-stream`, {
                method: 'POST',
                headers: getHeaders(),
                body: JSON.stringify({
                    userId: USER_CONFIG.userId,
                    username: USER_CONFIG.username,
                    query: currentQuery
                })
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop();

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.type === 'content') {
                                setAnalysisResult(prev => prev + data.content);
                            } else if (data.type === 'complete') {
                                setIsAnalyzing(false);
                            }
                        } catch (e) {
                            console.warn('解析失败:', line);
                        }
                    }
                }
            }
        } catch (error) {
            console.error('分析失败:', error);
            setIsAnalyzing(false);
        }
    };

    return (
        <div className="data-analysis-component">
            <h2>智能数据分析</h2>
            
            {/* 系统状态 */}
            <div className="status-section">
                <h3>系统状态</h3>
                {status && (
                    <div>
                        <p>数据库连接: {status.database_connected ? '✅' : '❌'}</p>
                        <p>记录数量: {status.record_count}</p>
                    </div>
                )}
            </div>

            {/* 查询输入 */}
            <div className="query-section">
                <h3>数据分析查询</h3>
                <textarea
                    value={currentQuery}
                    onChange={(e) => setCurrentQuery(e.target.value)}
                    placeholder="请输入您的分析查询..."
                    rows={4}
                    cols={50}
                />
                <br />
                <button 
                    onClick={handleAnalyze} 
                    disabled={isAnalyzing || !currentQuery.trim()}
                >
                    {isAnalyzing ? '分析中...' : '开始分析'}
                </button>
            </div>

            {/* 分析结果 */}
            <div className="result-section">
                <h3>分析结果</h3>
                <div className="result-content">
                    {analysisResult || '暂无分析结果'}
                </div>
            </div>

            {/* 对话历史 */}
            <div className="conversations-section">
                <h3>对话历史</h3>
                <ul>
                    {conversations.map(conv => (
                        <li key={conv.conversation_id}>
                            {conv.conversation_name} ({conv.message_count}条消息)
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
};

export default DataAnalysisComponent;
```

## 📝 注意事项

1. **用户认证**：所有API调用都需要提供有效的用户ID和用户名
2. **错误处理**：建议实现完善的错误处理机制
3. **流式响应**：分析接口使用流式响应，需要正确处理流数据
4. **文件上传**：上传接口需要使用FormData格式
5. **编码问题**：用户名包含中文时需要进行URL编码
6. **CORS设置**：确保后端已正确配置CORS支持

## 🔗 相关文档

- [README.md](README.md) - 项目总体介绍
- [API接口文档](README.md#📡-api-接口文档) - 详细的API说明
- [已知问题](README.md#🚨-已知问题和限制) - 当前系统限制

---

**文档版本**：v1.0  
**最后更新**：2024年1月  
**适用版本**：DataAnalyzer v1.1.2+
