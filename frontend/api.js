// P1精简版 api.js - 修复流式输出处理 + 对话记录功能
// 版本: 3.3.0 - 支持对话记录和HTML报告

class DatabaseAnalyzerAPI {
    constructor(baseURL = 'http://localhost:5000/api') {
        this.baseURL = baseURL;
        this.debug = false;
        
        // 确保用户ID一致性
        this.ensureUserConsistency();
        
        // 初始化
        this.init();
    }
    
    // 确保用户身份一致性
    ensureUserConsistency() {
        let userId = localStorage.getItem('simple_user_id');
        let username = localStorage.getItem('simple_username');
        
        if (!userId) {
            userId = 'user_' + Math.random().toString(36).substr(2, 8);
            username = `User_${userId.slice(-4)}`;
            
            localStorage.setItem('simple_user_id', userId);
            localStorage.setItem('simple_username', username);
        }
        
        this.currentUserId = userId;
        this.currentUsername = username;
        
        console.log(`🔑 用户身份确认: ${username} (${userId})`);
    }
    
    async init() {
        try {
            const response = await fetch(`${this.baseURL}/health`, {
                method: 'GET',
                headers: { 'Accept': 'application/json' },
                timeout: 3000
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('✅ API服务器连接成功');
                console.log(`📊 服务版本: ${data.version}`);
                if (data.features) {
                    console.log(`🚀 支持功能: ${data.features.join(', ')}`);
                }
            }
        } catch (error) {
            console.warn('⚠️ API服务器连接失败，使用默认配置');
        }
    }
    
    log(message, type = 'info') {
        if (this.debug) {
            console.log(`[API-${type.toUpperCase()}]`, message);
        }
    }
    
    getUserHeaders() {
        return {
            'Content-Type': 'application/json',
            'X-User-ID': this.currentUserId,
            'X-Username': encodeURIComponent(this.currentUsername)
        };
    }
    
    getSimpleUserId() {
        return this.currentUserId;
    }
    
    getSimpleUsername() {
        return this.currentUsername;
    }
    
    // 核心请求方法
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: this.getUserHeaders(),
            ...options
        };
        
        if (options.headers) {
            config.headers = { ...config.headers, ...options.headers };
        }
        
        config.headers['X-User-ID'] = this.currentUserId;
        config.headers['X-Username'] = encodeURIComponent(this.currentUsername);
        
        try {
            const response = await fetch(url, config);
            
            if (options.expectStream) {
                return response;
            }
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || `HTTP ${response.status}`);
            }
            
            return data;
        } catch (error) {
            this.log(`请求失败: ${endpoint} - ${error.message}`, 'error');
            throw error;
        }
    }
    
    async getStatus() {
        return await this.request('/status');
    }
    
    async uploadCSV(file, tableName = 'data_table') {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('tableName', tableName);
        formData.append('userId', this.currentUserId);
        formData.append('username', this.currentUsername);
        
        return await this.request('/upload', {
            method: 'POST',
            headers: {
                'X-User-ID': this.currentUserId,
                'X-Username': encodeURIComponent(this.currentUsername)
            },
            body: formData
        });
    }
    
    // 🔥 修复后的流式分析 - 正确处理Server-Sent Events
    async analyzeStream(query, onMessage, onComplete, onError) {
        try {
            const response = await fetch(`${this.baseURL}/analyze-stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'text/event-stream',
                    'Cache-Control': 'no-cache',
                    'X-User-ID': this.currentUserId,
                    'X-Username': encodeURIComponent(this.currentUsername)
                },
                body: JSON.stringify({ 
                    query,
                    userId: this.currentUserId,
                    username: this.currentUsername
                })
            });
            
            if (!response.ok) {
                try {
                    const errorData = await response.json();
                    throw new Error(errorData.message || `HTTP ${response.status}`);
                } catch (parseError) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
            }
            
            // 🔥 创建流式读取器
            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let buffer = '';
            
            try {
                while (true) {
                    const { done, value } = await reader.read();
                    
                    if (done) {
                        console.log('📡 流式数据传输完成');
                        if (onComplete) onComplete();
                        break;
                    }
                    
                    // 解码数据块
                    buffer += decoder.decode(value, { stream: true });
                    
                    // 按行处理数据
                    const lines = buffer.split('\n');
                    buffer = lines.pop() || ''; // 保留最后一个不完整的行
                    
                    for (const line of lines) {
                        const trimmedLine = line.trim();
                        
                        if (trimmedLine === '') {
                            continue; // 跳过空行
                        }
                        
                        // 处理SSE数据格式
                        if (trimmedLine.startsWith('data: ')) {
                            try {
                                const jsonStr = trimmedLine.slice(6); // 移除 'data: '
                                
                                if (jsonStr === '[DONE]') {
                                    console.log('📡 收到完成信号');
                                    if (onComplete) onComplete();
                                    break;
                                }
                                
                                const data = JSON.parse(jsonStr);
                                
                                // 根据消息类型处理
                                if (data.type === 'status') {
                                    console.log(`📊 状态: ${data.message}`);
                                    if (onMessage) {
                                        onMessage({
                                            type: 'status',
                                            content: data.message
                                        });
                                    }
                                } else if (data.type === 'ai_response') {
                                    // 实时AI响应
                                    if (onMessage) {
                                        onMessage({
                                            type: 'ai_response',
                                            content: data.content
                                        });
                                    }
                                } else if (data.type === 'tool_result') {
                                    // 工具执行结果
                                    console.log(`🔧 工具结果: ${data.tool}`);
                                    if (onMessage) {
                                        onMessage({
                                            type: 'tool_result',
                                            tool: data.tool,
                                            content: data.result
                                        });
                                    }
                                } else if (data.type === 'final_html') {
                                    // 🆕 最终HTML报告
                                    console.log('📊 收到最终HTML报告');
                                    if (onMessage) {
                                        onMessage({
                                            type: 'final_html',
                                            content: data.content
                                        });
                                    }
                                } else if (data.type === 'error') {
                                    console.error(`❌ 错误: ${data.message}`);
                                    if (onError) {
                                        onError(new Error(data.message));
                                    }
                                    return;
                                }
                                
                            } catch (parseError) {
                                console.warn('⚠️ 解析SSE数据失败:', trimmedLine, parseError);
                                // 继续处理其他行，不中断流
                            }
                        }
                    }
                }
            } finally {
                reader.releaseLock();
            }
            
        } catch (error) {
            console.error('❌ 流式分析失败:', error);
            if (onError) {
                onError(error);
            }
            throw error;
        }
    }
    
    // 🆕 获取对话历史
    async getConversations(limit = 10, offset = 0) {
        return await this.request(`/conversations?limit=${limit}&offset=${offset}`);
    }
    
    // 🆕 获取特定对话详情
    async getConversationDetail(conversationId) {
        return await this.request(`/conversations/${conversationId}`);
    }
    
    // 🆕 获取最新HTML报告
    async getLatestReport() {
        return await this.request('/latest-report');
    }
    
    // 健康检查
    async healthCheck() {
        try {
            const response = await fetch(`${this.baseURL}/health`, {
                method: 'GET',
                headers: { 'Accept': 'application/json' },
                timeout: 5000
            });
            
            if (response.ok) {
                const data = await response.json();
                this.log('健康检查成功');
                return data;
            } else {
                throw new Error(`健康检查失败: HTTP ${response.status}`);
            }
        } catch (error) {
            this.log(`健康检查失败: ${error.message}`, 'error');
            throw error;
        }
    }
    
    async testConnection() {
        this.log('开始连接测试...');
        
        try {
            const health = await this.healthCheck();
            this.log(`连接测试成功: ${health.status}`);
            
            return { 
                success: true, 
                health,
                message: '连接正常'
            };
            
        } catch (error) {
            this.log(`连接测试失败: ${error.message}`, 'error');
            return { 
                success: false, 
                error: error.message,
                message: '连接失败'
            };
        }
    }
    
    // 🆕 高级功能：批量操作
    async batchOperation(operations) {
        const results = [];
        
        for (const operation of operations) {
            try {
                let result;
                switch (operation.type) {
                    case 'getStatus':
                        result = await this.getStatus();
                        break;
                    case 'getConversations':
                        result = await this.getConversations(operation.limit, operation.offset);
                        break;
                    case 'getLatestReport':
                        result = await this.getLatestReport();
                        break;
                    default:
                        throw new Error(`未知操作类型: ${operation.type}`);
                }
                
                results.push({
                    operation: operation.type,
                    success: true,
                    data: result
                });
                
            } catch (error) {
                results.push({
                    operation: operation.type,
                    success: false,
                    error: error.message
                });
            }
        }
        
        return results;
    }
    
    // 🆕 数据导出功能
    exportConversations(conversations, format = 'json') {
        try {
            let exportData;
            let mimeType;
            let fileName;
            
            const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
            
            switch (format.toLowerCase()) {
                case 'json':
                    exportData = JSON.stringify(conversations, null, 2);
                    mimeType = 'application/json';
                    fileName = `conversations_${timestamp}.json`;
                    break;
                    
                case 'csv':
                    // 简化的CSV导出
                    const headers = ['对话ID', '开始时间', '用户查询', '状态', '工具调用次数'];
                    const rows = conversations.map(conv => [
                        conv.conversation_id,
                        conv.start_time,
                        `"${conv.user_query.replace(/"/g, '""')}"`,
                        conv.status,
                        conv.tool_calls_count || 0
                    ]);
                    
                    exportData = [headers.join(','), ...rows.map(row => row.join(','))].join('\n');
                    mimeType = 'text/csv;charset=utf-8';
                    fileName = `conversations_${timestamp}.csv`;
                    break;
                    
                default:
                    throw new Error(`不支持的导出格式: ${format}`);
            }
            
            // 创建下载
            const blob = new Blob([exportData], { type: mimeType });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = fileName;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            console.log(`✅ 导出成功: ${fileName}`);
            return { success: true, fileName };
            
        } catch (error) {
            console.error('❌ 导出失败:', error);
            return { success: false, error: error.message };
        }
    }
    
    // 🆕 缓存管理
    enableCache(ttl = 60000) { // 默认缓存1分钟
        this.cache = new Map();
        this.cacheTTL = ttl;
        
        // 清理过期缓存
        setInterval(() => {
            const now = Date.now();
            for (const [key, value] of this.cache.entries()) {
                if (now - value.timestamp > this.cacheTTL) {
                    this.cache.delete(key);
                }
            }
        }, this.cacheTTL);
        
        console.log('✅ 缓存已启用');
    }
    
    _getCacheKey(endpoint, options) {
        return `${endpoint}_${JSON.stringify(options || {})}`;
    }
    
    _getFromCache(key) {
        if (!this.cache) return null;
        
        const cached = this.cache.get(key);
        if (cached && Date.now() - cached.timestamp < this.cacheTTL) {
            return cached.data;
        }
        
        return null;
    }
    
    _setCache(key, data) {
        if (!this.cache) return;
        
        this.cache.set(key, {
            data,
            timestamp: Date.now()
        });
    }
}

// 创建API实例
const api = new DatabaseAnalyzerAPI();

// 🆕 启用缓存（可选）
// api.enableCache(30000); // 30秒缓存

// 导出API实例
window.databaseAPI = api;

// 🆕 全局工具函数
window.apiUtils = {
    // 格式化文件大小
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    // 格式化时间
    formatTime(isoString) {
        try {
            return new Date(isoString).toLocaleString('zh-CN');
        } catch (error) {
            return isoString;
        }
    },
    
    // 复制到剪贴板
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (error) {
            console.error('复制失败:', error);
            return false;
        }
    },
    
    // 验证文件类型
    validateFileType(file, allowedTypes = ['.csv']) {
        const fileName = file.name.toLowerCase();
        return allowedTypes.some(type => fileName.endsWith(type));
    }
};

// 页面加载处理
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🔍 开始API连接测试...');
    console.log(`👤 当前用户: ${api.currentUsername} (${api.currentUserId})`);
    
    // 添加全局错误处理
    window.addEventListener('unhandledrejection', event => {
        console.error('未处理的Promise拒绝:', event.reason);
        // 可以在这里添加用户友好的错误提示
    });
    
    setTimeout(async () => {
        try {
            const result = await api.testConnection();
            if (result.success) {
                console.log('✅ API连接测试成功');
                
                // 🆕 执行初始化数据加载
                try {
                    // 预加载系统状态
                    const status = await api.getStatus();
                    console.log('📊 系统状态预加载完成');
                    
                    // 可以在这里添加更多的初始化操作
                } catch (initError) {
                    console.warn('⚠️ 初始化数据加载失败:', initError.message);
                }
            } else {
                console.warn('⚠️ API连接测试失败:', result.message);
            }
        } catch (error) {
            console.error('❌ API连接测试异常:', error);
        }
    }, 1000);
});