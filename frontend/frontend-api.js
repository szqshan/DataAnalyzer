// 前端API集成 - 替换Web界面中的模拟代码
// frontend-api.js

class DatabaseAnalyzerAPI {
    constructor(baseURL = 'http://localhost:5000/api') {
        this.baseURL = baseURL;
    }
    
    // 通用请求方法
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };
        
        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || `HTTP ${response.status}`);
            }
            
            return data;
        } catch (error) {
            console.error(`API请求失败: ${endpoint}`, error);
            throw error;
        }
    }
    
    // 获取系统状态
    async getStatus() {
        return await this.request('/status');
    }
    
    // 上传CSV文件
    async uploadCSV(file, tableName, dbPath) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('tableName', tableName);
        formData.append('dbPath', dbPath);
        
        return await this.request('/upload', {
            method: 'POST',
            headers: {}, // 让浏览器自动设置Content-Type
            body: formData
        });
    }
    
    // 智能分析
    async analyze(query) {
        return await this.request('/analyze', {
            method: 'POST',
            body: JSON.stringify({ query })
        });
    }
    
    // 获取分析记忆
    async getMemory(conversationId = null, limit = 10) {
        const params = new URLSearchParams();
        if (conversationId) params.append('conversation_id', conversationId);
        if (limit) params.append('limit', limit);
        
        const endpoint = `/memory${params.toString() ? '?' + params.toString() : ''}`;
        return await this.request(endpoint);
    }
    
    // 获取SQL执行历史
    async getSQLHistory(conversationId) {
        return await this.request(`/memory/${conversationId}/sql`);
    }
    
    // 导出HTML报告
    async exportReport(conversationId) {
        const url = `${this.baseURL}/export/${conversationId}`;
        
        try {
            const response = await fetch(url);
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || '导出失败');
            }
            
            // 处理文件下载
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = `analysis_report_${conversationId}.html`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(downloadUrl);
            
            return { success: true };
        } catch (error) {
            console.error('导出失败:', error);
            throw error;
        }
    }
    
    // 清空记忆
    async clearMemory() {
        return await this.request('/memory', {
            method: 'DELETE'
        });
    }
    
    // 执行自定义SQL查询
    async executeQuery(sql) {
        return await this.request('/query', {
            method: 'POST',
            body: JSON.stringify({ sql })
        });
    }
    
    // 获取表结构信息
    async getTableInfo() {
        return await this.request('/table-info');
    }
    
    // 获取报告列表
    async getReports() {
        return await this.request('/reports');
    }
    
    // 健康检查
    async healthCheck() {
        return await this.request('/health');
    }
}

// 创建API实例
const api = new DatabaseAnalyzerAPI();

// 替换原有的前端函数，使用真实API调用

// 1. 替换文件上传函数
async function uploadFile(file, tableName, dbPath) {
    const progressDiv = document.getElementById('upload-progress');
    const progressBar = progressDiv.querySelector('.progress-bar');
    const statusText = document.getElementById('upload-status');
    
    progressDiv.style.display = 'block';
    uploadBtn.disabled = true;
    
    try {
        // 显示上传进度（模拟）
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 10;
            if (progress > 90) progress = 90;
            progressBar.style.width = progress + '%';
            statusText.textContent = `上传中... ${Math.round(progress)}%`;
        }, 200);
        
        // 调用真实API
        const result = await api.uploadCSV(file, tableName, dbPath);
        
        // 清除进度动画
        clearInterval(progressInterval);
        progressBar.style.width = '100%';
        statusText.textContent = '上传成功！';
        
        // 更新数据库状态
        updateDBStatus(
            result.data.db_path,
            result.data.table_name,
            result.data.rows_imported
        );
        
        setTimeout(() => {
            progressDiv.style.display = 'none';
            uploadBtn.disabled = false;
            showSuccessMessage(result.message);
            showTab('analysis');
        }, 1000);
        
    } catch (error) {
        statusText.textContent = '上传失败: ' + error.message;
        uploadBtn.disabled = false;
        showErrorMessage('上传失败: ' + error.message);
    }
}

// 2. 替换智能分析函数
async function sendAnalysis() {
    const query = analysisInput.value.trim();
    if (!query) return;
    
    // 检查数据库连接状态
    try {
        const status = await api.getStatus();
        if (!status.database_connected) {
            showErrorMessage('请先上传数据');
            return;
        }
    } catch (error) {
        showErrorMessage('无法连接到后端服务');
        return;
    }
    
    // 添加用户消息
    addMessage(query, 'user');
    analysisInput.value = '';
    
    // 显示加载状态
    analysisLoading.style.display = 'block';
    sendAnalysisBtn.disabled = true;
    
    try {
        // 调用真实API
        const result = await api.analyze(query);
        
        // 显示AI回复
        addMessage(result.result, 'ai');
        
        // 更新统计信息
        if (result.memory_stats) {
            currentState.conversationCount = result.memory_stats.conversation_count;
            currentState.sqlCount = result.memory_stats.total_sql_calls || 0;
            updateStats();
        }
        
    } catch (error) {
        addMessage('分析失败: ' + error.message, 'ai');
        showErrorMessage('分析失败: ' + error.message);
    } finally {
        analysisLoading.style.display = 'none';
        sendAnalysisBtn.disabled = false;
    }
}

// 3. 替换记忆加载函数
async function loadMemoryData() {
    const memoryContent = document.getElementById('memory-content');
    memoryContent.innerHTML = '<div class="text-center"><div class="spinner-border text-primary"></div><p class="mt-2">加载中...</p></div>';
    
    try {
        const result = await api.getMemory();
        renderMemoryData(result.conversations);
        
        // 更新全局统计
        if (result.global_stats) {
            currentState.conversationCount = result.global_stats.total_conversations;
            currentState.sqlCount = result.global_stats.total_sql_calls;
            updateStats();
        }
        
    } catch (error) {
        memoryContent.innerHTML = `
            <div class="alert alert-danger alert-custom">
                <i class="bi bi-exclamation-triangle"></i> 加载失败: ${error.message}
            </div>
        `;
    }
}

// 4. 替换SQL历史查看函数
async function viewSQLHistory(id) {
    try {
        const result = await api.getSQLHistory(id);
        const sqlHistory = result.sql_history;
        
        let html = `<h6>SQL执行历史 - 对话 #${id}</h6>`;
        
        if (sqlHistory.length === 0) {
            html += '<p class="text-muted">该对话没有SQL执行记录</p>';
        } else {
            sqlHistory.forEach((sql, index) => {
                const statusClass = sql.success ? 'success' : 'danger';
                const statusIcon = sql.success ? '✅' : '❌';
                const statusText = sql.success ? '成功' : '失败';
                
                html += `
                    <div class="sql-display mb-2">
                        <div class="d-flex justify-content-between mb-1">
                            <small><strong>查询 ${sql.sequence || index + 1}:</strong> ${sql.tool_name}</small>
                            <small class="text-${statusClass}">
                                ${statusIcon} ${statusText} (${sql.execution_time.toFixed(3)}s)
                            </small>
                        </div>
                        ${sql.sql ? `<code>${sql.sql}</code>` : '<em>无SQL语句</em>'}
                        ${sql.rows_returned > 0 ? `<div class="mt-1"><small class="text-info">返回 ${sql.rows_returned} 行</small></div>` : ''}
                    </div>
                `;
            });
        }
        
        showInfoModal('SQL执行历史', html);
        
    } catch (error) {
        showErrorMessage('获取SQL历史失败: ' + error.message);
    }
}

// 5. 替换报告导出函数
async function exportReport(id) {
    try {
        showSuccessMessage(`正在导出对话 #${id} 的HTML报告...`);
        
        await api.exportReport(id);
        showSuccessMessage('报告导出成功！');
        
    } catch (error) {
        showErrorMessage('导出失败: ' + error.message);
    }
}

// 6. 替换清空记忆函数
async function clearMemory() {
    if (!confirm('⚠️ 确认清空所有分析记忆？此操作不可撤销。')) {
        return;
    }
    
    try {
        const result = await api.clearMemory();
        
        // 重置本地状态
        currentState.conversationCount = 0;
        currentState.sqlCount = 0;
        updateStats();
        
        // 清空聊天记录
        const chatContainer = document.getElementById('chat-container');
        chatContainer.innerHTML = `
            <div class="message system-message">
                <div class="message-bubble">
                    🗑️ 记忆已清空，开始新的分析会话
                </div>
            </div>
        `;
        
        showSuccessMessage(result.message);
        
    } catch (error) {
        showErrorMessage('清空失败: ' + error.message);
    }
}

// 7. 替换结果刷新函数
async function refreshResults() {
    const resultsContent = document.getElementById('results-content');
    resultsContent.innerHTML = '<div class="text-center"><div class="spinner-border text-primary"></div><p class="mt-2">加载中...</p></div>';
    
    try {
        const reports = await api.getReports();
        
        if (reports.reports.length === 0) {
            resultsContent.innerHTML = `
                <div class="text-center text-muted">
                    <i class="bi bi-file-earmark-text display-1"></i>
                    <p>暂无分析结果</p>
                    <small>完成数据分析后，结果将在这里显示</small>
                </div>
            `;
            return;
        }
        
        // 显示最新的报告
        const latestReport = reports.reports[reports.reports.length - 1];
        
        resultsContent.innerHTML = `
            <div class="card feature-card">
                <h6><i class="bi bi-file-earmark-text"></i> 最新分析报告</h6>
                <div class="row mb-3">
                    <div class="col-md-6">
                        <canvas id="sample-chart" width="300" height="200"></canvas>
                    </div>
                    <div class="col-md-6">
                        <h6>📊 报告信息</h6>
                        <ul class="list-unstyled">
                            <li><strong>报告ID:</strong> #${latestReport.conversation_id}</li>
                            <li><strong>生成时间:</strong> ${new Date(latestReport.timestamp).toLocaleString()}</li>
                            <li><strong>报告大小:</strong> ${(latestReport.size / 1024).toFixed(1)}KB</li>
                            <li><strong>分析问题:</strong> ${latestReport.query.substring(0, 50)}...</li>
                        </ul>
                        
                        <h6 class="mt-3">🎯 报告摘要</h6>
                        <div class="alert alert-info alert-custom">
                            <small>${latestReport.title}</small>
                        </div>
                    </div>
                </div>
                
                <div class="d-flex gap-2">
                    <button class="btn btn-outline-primary btn-sm" onclick="showFullReport(${latestReport.conversation_id})">
                        <i class="bi bi-fullscreen"></i> 全屏查看
                    </button>
                    <button class="btn btn-outline-success btn-sm" onclick="exportReport(${latestReport.conversation_id})">
                        <i class="bi bi-download"></i> 导出HTML
                    </button>
                    <button class="btn btn-outline-info btn-sm" onclick="shareReport()">
                        <i class="bi bi-share"></i> 分享报告
                    </button>
                </div>
            </div>
            
            ${reports.reports.length > 1 ? `
                <div class="mt-3">
                    <h6>📚 历史报告 (${reports.total_count}个)</h6>
                    <div class="row">
                        ${reports.reports.slice(-4).map(report => `
                            <div class="col-md-3 mb-2">
                                <div class="card">
                                    <div class="card-body p-2">
                                        <h6 class="card-title">#${report.conversation_id}</h6>
                                        <p class="card-text small">${report.title.substring(0, 40)}...</p>
                                        <button class="btn btn-outline-primary btn-sm w-100" onclick="exportReport(${report.conversation_id})">
                                            <i class="bi bi-download"></i> 导出
                                        </button>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
        `;
        
        // 绘制示例图表
        drawSampleChart();
        
    } catch (error) {
        resultsContent.innerHTML = `
            <div class="alert alert-danger alert-custom">
                <i class="bi bi-exclamation-triangle"></i> 加载失败: ${error.message}
            </div>
        `;
    }
}

// 8. 系统状态检查函数
async function checkSystemStatus() {
    try {
        const status = await api.getStatus();
        
        // 更新数据库状态
        if (status.database_connected) {
            updateDBStatus(
                status.database_path,
                status.table_name,
                status.record_count
            );
        }
        
        // 更新统计信息
        if (status.memory_stats) {
            currentState.conversationCount = status.memory_stats.conversation_count || 0;
            currentState.sqlCount = status.memory_stats.total_sql_calls || 0;
            updateStats();
        }
        
        // 更新连接状态
        document.getElementById('connection-status').textContent = 
            status.system_ready ? '已连接' : '连接异常';
        
        return status;
        
    } catch (error) {
        document.getElementById('connection-status').textContent = '连接失败';
        console.error('系统状态检查失败:', error);
        return null;
    }
}

// 9. 页面初始化 - 替换原有的初始化代码
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🤖 智能数据库分析系统正在初始化...');
    
    try {
        // 检查后端连接
        showToast('正在连接后端服务...', 'info');
        
        const status = await checkSystemStatus();
        
        if (status && status.system_ready) {
            showSuccessMessage('系统初始化完成！');
            
            // 如果已有数据库连接，自动加载记忆
            if (status.database_connected) {
                setTimeout(() => {
                    loadMemoryData();
                }, 1000);
            }
        } else {
            showErrorMessage('后端服务连接失败，请检查服务是否启动');
        }
        
    } catch (error) {
        showErrorMessage('系统初始化失败: ' + error.message);
        console.error('初始化错误:', error);
    }
});

// 10. 定期状态检查
setInterval(async () => {
    try {
        await api.healthCheck();
        // 健康检查通过，可以更新UI状态
    } catch (error) {
        // 后端服务可能断开
        document.getElementById('connection-status').textContent = '连接中断';
        console.warn('后端服务健康检查失败:', error);
    }
}, 30000); // 每30秒检查一次

// 11. 新增功能：实时查询执行
async function executeCustomQuery() {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title"><i class="bi bi-database"></i> SQL查询工具</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="mb-3">
                        <label class="form-label">SQL查询语句 (仅支持SELECT)</label>
                        <textarea class="form-control" id="custom-sql" rows="4" 
                                  placeholder="SELECT * FROM ${currentState.tableName || 'your_table'} LIMIT 10;"></textarea>
                    </div>
                    <div id="query-result" class="mt-3"></div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                    <button type="button" class="btn btn-gradient" onclick="runCustomQuery()">
                        <i class="bi bi-play-fill"></i> 执行查询
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    modal.addEventListener('hidden.bs.modal', () => {
        document.body.removeChild(modal);
    });
}

async function runCustomQuery() {
    const sql = document.getElementById('custom-sql').value.trim();
    const resultDiv = document.getElementById('query-result');
    
    if (!sql) {
        resultDiv.innerHTML = '<div class="alert alert-warning">请输入SQL查询语句</div>';
        return;
    }
    
    resultDiv.innerHTML = '<div class="text-center"><div class="spinner-border text-primary"></div><p>执行中...</p></div>';
    
    try {
        const result = await api.executeQuery(sql);
        
        if (result.result.data.length === 0) {
            resultDiv.innerHTML = '<div class="alert alert-info">查询成功，但没有返回数据</div>';
            return;
        }
        
        // 构建表格
        let tableHTML = `
            <div class="alert alert-success">
                ✅ 查询成功！返回 ${result.result.total_rows} 行，耗时 ${result.result.execution_time.toFixed(3)}s
            </div>
            <div class="table-responsive">
                <table class="table table-striped table-sm">
                    <thead>
                        <tr>
                            ${result.result.columns.map(col => `<th>${col}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        result.result.data.forEach(row => {
            tableHTML += '<tr>' + row.map(cell => `<td>${cell || ''}</td>`).join('') + '</tr>';
        });
        
        tableHTML += `
                    </tbody>
                </table>
            </div>
        `;
        
        if (result.result.total_rows > 100) {
            tableHTML += '<div class="alert alert-info">注意：只显示前100行结果</div>';
        }
        
        resultDiv.innerHTML = tableHTML;
        
    } catch (error) {
        resultDiv.innerHTML = `<div class="alert alert-danger">❌ 查询失败: ${error.message}</div>`;
    }
}

// 12. 添加快捷操作按钮到界面
function addQuickActions() {
    const quickActionsHTML = `
        <div class="card feature-card mb-3">
            <h6><i class="bi bi-tools"></i> 快捷工具</h6>
            <div class="d-grid gap-2">
                <button class="btn btn-outline-gradient btn-sm" onclick="executeCustomQuery()">
                    <i class="bi bi-database"></i> SQL查询
                </button>
                <button class="btn btn-outline-gradient btn-sm" onclick="showTableStructure()">
                    <i class="bi bi-table"></i> 表结构
                </button>
                <button class="btn btn-outline-gradient btn-sm" onclick="downloadSystemInfo()">
                    <i class="bi bi-info-circle"></i> 系统信息
                </button>
            </div>
        </div>
    `;
    
    // 将快捷工具插入到侧边栏
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        sidebar.insertAdjacentHTML('beforeend', quickActionsHTML);
    }
}

async function showTableStructure() {
    try {
        const result = await api.getTableInfo();
        
        let html = '<h6>📋 表结构信息</h6>';
        
        if (result.table_info && result.table_info.columns) {
            html += `
                <div class="mb-3">
                    <strong>表名:</strong> ${result.table_info.table_name}<br>
                    <strong>字段数:</strong> ${result.table_info.columns.length}
                </div>
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr><th>字段名</th><th>类型</th></tr>
                        </thead>
                        <tbody>
            `;
            
            result.table_info.columns.forEach(col => {
                html += `<tr><td>${col.name}</td><td>${col.type}</td></tr>`;
            });
            
            html += '</tbody></table></div>';
            
            if (result.table_info.sample_data && result.table_info.sample_data.length > 0) {
                html += '<h6 class="mt-3">📊 样本数据</h6>';
                html += '<div class="table-responsive"><table class="table table-sm"><thead><tr>';
                
                const firstRow = result.table_info.sample_data[0];
                Object.keys(firstRow).forEach(key => {
                    html += `<th>${key}</th>`;
                });
                html += '</tr></thead><tbody>';
                
                result.table_info.sample_data.forEach(row => {
                    html += '<tr>';
                    Object.values(row).forEach(value => {
                        html += `<td>${value || ''}</td>`;
                    });
                    html += '</tr>';
                });
                
                html += '</tbody></table></div>';
            }
        } else {
            html += '<div class="alert alert-warning">无法获取表结构信息</div>';
        }
        
        showInfoModal('表结构信息', html);
        
    } catch (error) {
        showErrorMessage('获取表结构失败: ' + error.message);
    }
}

async function downloadSystemInfo() {
    try {
        const status = await api.getStatus();
        const memory = await api.getMemory();
        
        const systemInfo = {
            timestamp: new Date().toISOString(),
            system_status: status,
            memory_summary: memory,
            browser_info: {
                userAgent: navigator.userAgent,
                language: navigator.language,
                platform: navigator.platform
            }
        };
        
        const blob = new Blob([JSON.stringify(systemInfo, null, 2)], { 
            type: 'application/json' 
        });
        
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `system_info_${new Date().getTime()}.json`;
        link.click();
        URL.revokeObjectURL(url);
        
        showSuccessMessage('系统信息已导出！');
        
    } catch (error) {
        showErrorMessage('导出系统信息失败: ' + error.message);
    }
}

// 页面加载完成后添加快捷工具
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(addQuickActions, 1000);
});

// 导出API实例供其他脚本使用
window.databaseAPI = api;