// api.js - 修复版多用户支持的前端API类
class DatabaseAnalyzerAPI {
    constructor(baseURL = 'http://localhost:5000/api') {
        this.baseURL = baseURL;
        this.debug = true; // 启用调试模式
        
        // 自动检测API服务器地址
        this.detectAPIServer();
    }
    
    // 自动检测API服务器地址
    async detectAPIServer() {
        // 尝试的服务器列表
        const servers = [
            'http://localhost:5000/api',  // 本地开发服务器
            '/api',                       // 相对路径（当前域）
            window.location.origin + '/api', // 当前域的绝对路径
            'http://127.0.0.1:5000/api'   // 使用IP地址
        ];
        
        this.log('正在自动检测API服务器地址...');
        
        for (const server of servers) {
            try {
                const response = await fetch(`${server}/health`, {
                    method: 'GET',
                    headers: { 'Accept': 'application/json' },
                    mode: 'cors',
                    cache: 'no-cache',
                    timeout: 2000
                });
                
                if (response.ok) {
                    this.baseURL = server;
                    this.log(`✅ 已连接到API服务器: ${server}`);
                    return;
                }
            } catch (error) {
                this.log(`尝试连接到 ${server} 失败: ${error.message}`, 'warn');
            }
        }
        
        this.log('⚠️ 无法自动检测API服务器，使用默认地址', 'warn');
    }
    
    log(message, type = 'info') {
        if (this.debug) {
            console.log(`[API ${type.toUpperCase()}]`, message);
        }
    }
    
    // 获取当前用户信息的请求头
    getUserHeaders() {
        const user = window.userManager ? window.userManager.getCurrentUser() : null;
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (user) {
            headers['X-User-ID'] = user.userId;
            
            // 修复: 对用户名进行URL编码以避免非ASCII字符问题
            try {
                headers['X-Username'] = encodeURIComponent(user.username);
                this.log(`用户信息: ${user.username} (${user.userId}) - 已编码用户名`);
            } catch (error) {
                // 如果编码失败，使用安全的默认值
                headers['X-Username'] = 'DefaultUser';
                this.log(`用户名编码失败，使用默认值: ${error.message}`, 'warn');
            }
        } else {
            this.log('未找到用户信息', 'warn');
        }
        
        return headers;
    }
    
    // 通用请求方法 - 增强错误处理
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                ...this.getUserHeaders(),
                ...options.headers
            },
            ...options
        };
        
        this.log(`发起请求: ${config.method || 'GET'} ${url}`);
        
        try {
            const response = await fetch(url, config);
            this.log(`响应状态: ${response.status} ${response.statusText}`);
            
            // 处理401未授权错误
            if (response.status === 401) {
                const errorMsg = '用户身份验证失败，请重新登录';
                this.log(errorMsg, 'error');
                if (window.userManager) {
                    window.userManager.logout();
                }
                throw new Error(errorMsg);
            }
            
            // 检查响应类型
            const contentType = response.headers.get('content-type');
            let data;
            
            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
            } else {
                const text = await response.text();
                this.log(`非JSON响应: ${text.substring(0, 200)}...`, 'warn');
                throw new Error(`服务器返回非JSON响应: ${response.status}`);
            }
            
            if (!response.ok) {
                const errorMsg = data.message || `HTTP ${response.status}`;
                this.log(`请求失败: ${errorMsg}`, 'error');
                throw new Error(errorMsg);
            }
            
            this.log('请求成功');
            return data;
            
        } catch (error) {
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                // 网络连接错误
                const networkError = '无法连接到后端服务，请检查服务是否启动';
                this.log(networkError, 'error');
                throw new Error(networkError);
            }
            
            this.log(`请求异常: ${error.message}`, 'error');
            throw error;
        }
    }
    
    // 健康检查 - 最基本的连接测试
    async healthCheck() {
        try {
            // 尝试使用标准请求
            const response = await fetch(`${this.baseURL}/health`, {
                method: 'GET',
                headers: { 'Accept': 'application/json' },
                mode: 'cors',
                cache: 'no-cache'
            });
            
            if (response.ok) {
                const data = await response.json();
                this.log('健康检查成功', 'success');
                return data;
            } else {
                throw new Error(`健康检查失败: HTTP ${response.status}`);
            }
        } catch (error) {
            // 如果标准请求失败，尝试使用动态脚本加载方式（类似JSONP）绕过跨域限制
            this.log('标准健康检查失败，尝试备用方法', 'warn');
            return new Promise((resolve, reject) => {
                // 创建一个全局回调函数
                const callbackName = 'healthCheckCallback_' + Math.floor(Math.random() * 1000000);
                window[callbackName] = (data) => {
                    // 清理
                    delete window[callbackName];
                    document.body.removeChild(script);
                    resolve(data);
                };
                
                // 创建脚本标签
                const script = document.createElement('script');
                script.src = `${this.baseURL}/health?callback=${callbackName}`;
                script.onerror = () => {
                    // 清理
                    delete window[callbackName];
                    document.body.removeChild(script);
                    reject(new Error('健康检查失败，无法连接到后端服务'));
                };
                
                // 添加到文档
                document.body.appendChild(script);
                
                // 设置超时
                setTimeout(() => {
                    if (window[callbackName]) {
                        delete window[callbackName];
                        document.body.removeChild(script);
                        reject(new Error('健康检查超时'));
                    }
                }, 5000);
            });
        }
    }
    
    // 修复：正确的状态检查方法名
    async getStatus() {
        return await this.request('/status');
    }
    
    // 保持向后兼容
    async getSystemStatus() {
        this.log('getSystemStatus() 已废弃，请使用 getStatus()', 'warn');
        return await this.getStatus();
    }
    
    // 用户相关接口
    async getUserStatus() {
        return await this.request('/user/status');
    }
    
    // 上传CSV文件 - 增强错误处理
    async uploadCSV(file, tableName, dbPath) {
        const user = window.userManager ? window.userManager.getCurrentUser() : null;
        
        if (!user) {
            throw new Error('请先完成用户身份识别');
        }
        
        this.log(`准备上传文件: ${file.name} (${file.size} bytes)`);
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('tableName', tableName || 'data_table');
        formData.append('dbPath', dbPath || 'analysis.db');
        
        // 添加用户信息到表单数据
        formData.append('userId', user.userId);
        formData.append('username', user.username);
        
        // 修复: 确保headers不包含非ASCII字符
        const headers = {};
        headers['X-User-ID'] = user.userId;
        
        // 修复: 对用户名进行URL编码以避免非ASCII字符问题
        try {
            headers['X-Username'] = encodeURIComponent(user.username);
            this.log(`上传用户信息: ${user.username} (${user.userId}) - 已编码用户名`);
        } catch (error) {
            // 如果编码失败，使用安全的默认值
            headers['X-Username'] = 'DefaultUser';
            this.log(`用户名编码失败，使用默认值: ${error.message}`, 'warn');
        }
        
        // 使用直接的fetch调用，而不是通过request方法，以便更好地控制
        try {
            const uploadUrl = `${this.baseURL}/upload`;
            this.log(`开始上传到: ${uploadUrl}`);
            
            // 使用更长的超时时间
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 120000); // 120秒超时
            
            this.log(`请求配置: 方法=POST, URL=${uploadUrl}, 超时=120秒`);
            this.log(`请求头: ${JSON.stringify(headers)}`);
            
            const response = await fetch(uploadUrl, {
                method: 'POST',
                headers: headers,
                body: formData,
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            this.log(`上传响应状态: ${response.status} ${response.statusText}`);
            
            // 检查响应类型
            const contentType = response.headers.get('content-type');
            this.log(`响应内容类型: ${contentType}`);
            
            let data;
            
            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
                this.log(`上传响应数据: ${JSON.stringify(data).substring(0, 100)}...`);
            } else {
                const text = await response.text();
                this.log(`非JSON响应: ${text.substring(0, 200)}...`, 'warn');
                throw new Error(`服务器返回非JSON响应: ${response.status}`);
            }
            
            if (!response.ok) {
                const errorMsg = data.message || `HTTP ${response.status}`;
                this.log(`上传失败: ${errorMsg}`, 'error');
                throw new Error(errorMsg);
            }
            
            this.log('上传成功');
            return data;
            
        } catch (error) {
            if (error.name === 'AbortError') {
                this.log('上传请求超时', 'error');
                throw new Error('上传请求超时，请检查网络连接和服务器状态');
            } else if (error.name === 'TypeError' && error.message.includes('fetch')) {
                this.log(`无法连接到后端服务: ${error.message}`, 'error');
                throw new Error(`无法连接到后端服务，请检查服务是否启动: ${error.message}`);
            } else if (error.message && error.message.includes('headers')) {
                this.log(`请求头错误: ${error.message}`, 'error');
                throw new Error(`请求头错误，可能包含无效字符: ${error.message}`);
            }
            
            this.log(`上传异常: ${error.message}`, 'error');
            throw error;
        }
    }
    
    /**
     * 发送流式分析请求
     * @param {string} query - 分析查询
     * @returns {Promise<Response>} - 返回流式响应
     */
    async analyzeStream(query) {
        const user = window.userManager ? window.userManager.getCurrentUser() : null;
        
        if (!user) {
            throw new Error('用户未登录，请先登录');
        }
        
        this.log(`发送流式分析请求: ${query}`);
        this.log(`当前用户: ${user.username} (ID: ${user.userId})`);
        
        try {
            // 构建请求体
            const requestBody = {
                query: query.trim(),
                user_id: user.userId,
                username: user.username
            };
            
            // 构建请求头
            const headers = this.getUserHeaders();
            headers['Accept'] = 'text/event-stream';
            headers['Cache-Control'] = 'no-cache';
            
            // 检测浏览器类型
            const isEdge = navigator.userAgent.indexOf('Edg/') !== -1;
            if (isEdge) {
                this.log('检测到Edge浏览器，使用兼容模式', 'info');
            }
            
            // 发送请求
            const response = await fetch(`${this.baseURL}/analyze-stream`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(requestBody),
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                let errorMessage = `服务器错误 (${response.status})`;
                try {
                    // 尝试获取错误信息
                    const errorText = await response.text();
                    if (errorText) {
                        try {
                            const errorJson = JSON.parse(errorText);
                            errorMessage = errorJson.message || errorText;
                        } catch {
                            errorMessage = errorText;
                        }
                    }
                } catch (e) {
                    this.log(`无法解析错误响应: ${e.message}`, 'error');
                }
                
                this.log(`流式分析请求失败: ${response.status} - ${errorMessage}`, 'error');
                throw new Error(errorMessage);
            }
            
            // 检查响应类型
            const contentType = response.headers.get('content-type');
            this.log(`收到响应，内容类型: ${contentType}`, 'info');
            
            return response;
        } catch (error) {
            this.log(`流式分析请求异常: ${error.message}`, 'error');
            throw error;
        }
    }
    
    // 传统分析方法
    async analyze(query) {
        const user = window.userManager ? window.userManager.getCurrentUser() : null;
        
        if (!user) {
            throw new Error('请先完成用户身份识别');
        }
        
        const requestBody = { 
            query: query.trim(),
            userId: user.userId,
            username: user.username
        };
        
        // 修复: 确保headers不包含非ASCII字符
        const headers = {
            'Content-Type': 'application/json'
        };
        headers['X-User-ID'] = user.userId;
        
        // 修复: 对用户名进行URL编码以避免非ASCII字符问题
        try {
            headers['X-Username'] = encodeURIComponent(user.username);
            this.log(`分析用户信息: ${user.username} (${user.userId}) - 已编码用户名`);
        } catch (error) {
            // 如果编码失败，使用安全的默认值
            headers['X-Username'] = 'DefaultUser';
            this.log(`用户名编码失败，使用默认值: ${error.message}`, 'warn');
        }
        
        return await this.request('/analyze', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(requestBody)
        });
    }
    
    // 获取所有用户列表（调试用）
    async getAllUsers() {
        return await this.request('/users');
    }
    
    // 连接测试方法
    async testConnection() {
        this.log('开始连接测试...');
        
        try {
            // 1. 基础健康检查
            const health = await this.healthCheck();
            this.log(`健康检查通过: ${health.status}`);
            
            // 2. 状态检查（需要用户信息）
            if (window.userManager && window.userManager.isLoggedIn()) {
                const status = await this.getStatus();
                this.log(`状态检查通过: 系统${status.system_ready ? '就绪' : '未就绪'}`);
                return { success: true, health, status };
            } else {
                this.log('用户未登录，跳过状态检查');
                return { success: true, health, status: null };
            }
            
        } catch (error) {
            this.log(`连接测试失败: ${error.message}`, 'error');
            return { success: false, error: error.message };
        }
    }
    
    // 以下接口暂时保持原样，后续实现
    async getMemory(conversationId = null, limit = 10) {
        throw new Error('记忆接口正在开发中...');
    }
    
    async getSQLHistory(conversationId) {
        throw new Error('SQL历史接口正在开发中...');
    }
    
    async exportReport(conversationId) {
        throw new Error('报告导出接口正在开发中...');
    }
    
    async clearMemory() {
        throw new Error('记忆清空接口正在开发中...');
    }
    
    async executeQuery(sql) {
        throw new Error('SQL查询接口正在开发中...');
    }
    
    async getTableInfo() {
        throw new Error('表信息接口正在开发中...');
    }
    
    async getReports() {
        throw new Error('报告列表接口正在开发中...');
    }
}

// 创建API实例
const api = new DatabaseAnalyzerAPI();

// 导出API实例供其他脚本使用
window.databaseAPI = api;

// 页面加载后自动测试连接
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🔍 开始后端连接测试...');
    
    setTimeout(async () => {
        try {
            const result = await api.testConnection();
            if (result.success) {
                console.log('✅ 后端连接测试成功');
            } else {
                console.error('❌ 后端连接测试失败:', result.error);
            }
        } catch (error) {
            console.error('❌ 连接测试异常:', error);
        }
    }, 1000);
});