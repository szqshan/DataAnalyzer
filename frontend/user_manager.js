// user_manager.js - 前端用户状态管理
class UserStateManager {
    constructor() {
        this.currentUser = null;
        this.userState = {};
        this.listeners = [];
        
        // 自动初始化用户
        this.initializeUser();
    }
    
    // 用户识别策略
    async initializeUser() {
        console.log('🔍 开始用户身份识别...');
        
        // 策略1: 从URL参数获取（主系统传递）
        const urlUser = this.getUserFromURL();
        if (urlUser) {
            await this.setUser(urlUser);
            console.log('✅ 从URL参数获取用户信息:', urlUser);
            return;
        }
        
        // 策略2: 从localStorage恢复
        const savedUser = this.getUserFromStorage();
        if (savedUser) {
            // 验证用户是否仍然有效（检查是否过期）
            if (this.isUserValid(savedUser)) {
                await this.setUser(savedUser);
                console.log('✅ 从localStorage恢复用户:', savedUser);
                return;
            } else {
                console.log('⚠️ localStorage中的用户信息已过期');
                this.clearUserStorage();
            }
        }
        
        // 策略3: 显示用户选择界面
        console.log('🆔 显示用户选择界面');
        this.showUserSelector();
    }
    
    getUserFromURL() {
        const urlParams = new URLSearchParams(window.location.search);
        const userId = urlParams.get('userId');
        const username = urlParams.get('username');
        const token = urlParams.get('token');
        
        if (userId) {
            // 清除URL参数（可选，美化URL）
            if (window.history && window.history.replaceState) {
                const cleanURL = window.location.pathname;
                window.history.replaceState({}, document.title, cleanURL);
            }
            
            return {
                userId: userId,
                username: username || `User_${userId}`,
                token: token || '',
                source: 'url',
                loginTime: Date.now()
            };
        }
        
        return null;
    }
    
    getUserFromStorage() {
        try {
            const userData = localStorage.getItem('current_user');
            if (userData) {
                return JSON.parse(userData);
            }
        } catch (e) {
            console.warn('解析localStorage用户数据失败:', e);
            this.clearUserStorage();
        }
        return null;
    }
    
    isUserValid(user) {
        // 检查用户信息是否过期（24小时）
        const maxAge = 24 * 60 * 60 * 1000; // 24小时
        return user.loginTime && (Date.now() - user.loginTime) < maxAge;
    }
    
    async setUser(userData) {
        this.currentUser = {
            ...userData,
            lastActivity: Date.now()
        };
        
        // 保存到localStorage
        this.saveUserToStorage();
        
        // 同步到服务器（可选）
        try {
            await this.syncUserToServer();
        } catch (e) {
            console.warn('同步用户信息到服务器失败:', e);
        }
        
        // 触发用户变更事件
        this.notifyUserChange();
        
        // 更新UI
        this.updateUserDisplay();
    }
    
    saveUserToStorage() {
        try {
            localStorage.setItem('current_user', JSON.stringify(this.currentUser));
            
            // 同时保存用户状态
            localStorage.setItem('user_state', JSON.stringify(this.userState));
        } catch (e) {
            console.warn('保存用户信息到localStorage失败:', e);
        }
    }
    
    async syncUserToServer() {
        if (!this.currentUser) return;
        
        // 调用后端API同步用户信息
        const response = await fetch('/api/user/status', {
            method: 'GET',
            headers: {
                'X-User-ID': this.currentUser.userId,
                'X-Username': this.currentUser.username
            }
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log('✅ 用户信息已同步到服务器');
            return result;
        }
    }
    
    updateUserDisplay() {
        if (!this.currentUser) return;
        
        // 更新导航栏用户信息
        const userDisplay = document.getElementById('user-display');
        if (userDisplay) {
            userDisplay.innerHTML = `
                <i class="bi bi-person-circle"></i> 
                ${this.currentUser.username} 
                <small class="text-muted">(${this.currentUser.userId})</small>
            `;
        }
        
        // 更新连接状态
        const connectionStatus = document.getElementById('connection-status');
        if (connectionStatus) {
            connectionStatus.innerHTML = `
                <span class="connection-indicator connected">
                    ${this.currentUser.username}
                </span>
            `;
        }
        
        // 更新用户状态卡片
        this.updateUserStatusCard();
    }
    
    updateUserStatusCard() {
        const statusCard = document.querySelector('.status-card');
        if (statusCard && this.currentUser) {
            // 在数据库状态卡片前添加用户信息
            const userInfoHTML = `
                <div class="user-info-section mb-3 pb-3 border-bottom border-light">
                    <h6><i class="bi bi-person-fill"></i> 当前用户</h6>
                    <small>用户名: ${this.currentUser.username}</small><br>
                    <small>用户ID: ${this.currentUser.userId}</small><br>
                    <small>登录时间: ${new Date(this.currentUser.loginTime).toLocaleString()}</small>
                </div>
            `;
            
            // 检查是否已经添加过用户信息
            if (!statusCard.querySelector('.user-info-section')) {
                const dbStatusTitle = statusCard.querySelector('h6');
                if (dbStatusTitle) {
                    dbStatusTitle.insertAdjacentHTML('beforebegin', userInfoHTML);
                }
            }
        }
    }
    
    showUserSelector() {
        // 创建用户选择模态框
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'user-selector-modal';
        modal.setAttribute('data-bs-backdrop', 'static');
        modal.setAttribute('data-bs-keyboard', 'false');
        
        modal.innerHTML = `
            <div class="modal-dialog modal-md">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title">
                            <i class="bi bi-person-plus"></i> 用户身份识别
                        </h5>
                    </div>
                    <div class="modal-body">
                        <div class="alert alert-info">
                            <i class="bi bi-info-circle"></i>
                            请选择或输入您的用户身份以开始使用数据分析系统
                        </div>
                        
                        <!-- 预设用户 -->
                        <h6><i class="bi bi-people"></i> 快速选择</h6>
                        <div class="row mb-3">
                            <div class="col-md-6">
                                <button class="btn btn-outline-primary w-100 mb-2" onclick="userManager.selectPresetUser('001', '张三', '数据分析师')">
                                    <i class="bi bi-person"></i> 张三<br>
                                    <small>数据分析师</small>
                                </button>
                            </div>
                            <div class="col-md-6">
                                <button class="btn btn-outline-primary w-100 mb-2" onclick="userManager.selectPresetUser('002', '李四', '业务经理')">
                                    <i class="bi bi-person"></i> 李四<br>
                                    <small>业务经理</small>
                                </button>
                            </div>
                        </div>
                        
                        <!-- 自定义用户 -->
                        <h6><i class="bi bi-pencil"></i> 自定义用户</h6>
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">用户ID</label>
                                    <input type="text" class="form-control" id="custom-user-id" 
                                           placeholder="例如: 003" maxlength="10">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">用户名</label>
                                    <input type="text" class="form-control" id="custom-username" 
                                           placeholder="例如: 王五" maxlength="20">
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">角色 (可选)</label>
                            <input type="text" class="form-control" id="custom-role" 
                                   placeholder="例如: 产品经理" maxlength="20">
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-outline-secondary" onclick="userManager.generateGuestUser()">
                            <i class="bi bi-shuffle"></i> 生成访客账号
                        </button>
                        <button type="button" class="btn btn-primary" onclick="userManager.confirmCustomUser()">
                            <i class="bi bi-check2"></i> 确认登录
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // 焦点到第一个输入框
        setTimeout(() => {
            document.getElementById('custom-user-id').focus();
        }, 500);
    }
    
    async selectPresetUser(userId, username, role) {
        await this.setUser({
            userId: userId,
            username: username,
            role: role || '',
            source: 'preset',
            loginTime: Date.now()
        });
        
        this.closeUserSelector();
        this.showWelcomeMessage(`欢迎，${username}！`);
    }
    
    async confirmCustomUser() {
        const userId = document.getElementById('custom-user-id').value.trim();
        const username = document.getElementById('custom-username').value.trim();
        const role = document.getElementById('custom-role').value.trim();
        
        if (!userId || !username) {
            this.showError('请填写用户ID和用户名');
            return;
        }
        
        // 验证用户ID格式
        if (!/^[a-zA-Z0-9_-]+$/.test(userId)) {
            this.showError('用户ID只能包含字母、数字、下划线和连字符');
            return;
        }
        
        await this.setUser({
            userId: userId,
            username: username,
            role: role || '',
            source: 'custom',
            loginTime: Date.now()
        });
        
        this.closeUserSelector();
        this.showWelcomeMessage(`欢迎，${username}！`);
    }
    
    generateGuestUser() {
        const guestId = 'guest_' + Math.random().toString(36).substr(2, 8);
        const guestName = '访客_' + guestId.slice(-4);
        
        this.setUser({
            userId: guestId,
            username: guestName,
            role: '访客',
            source: 'guest',
            loginTime: Date.now()
        });
        
        this.closeUserSelector();
        this.showWelcomeMessage(`欢迎，${guestName}！`);
    }
    
    closeUserSelector() {
        const modal = document.getElementById('user-selector-modal');
        if (modal) {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
            
            // 延迟移除DOM元素
            setTimeout(() => {
                if (modal.parentNode) {
                    modal.parentNode.removeChild(modal);
                }
            }, 300);
        }
    }
    
    showError(message) {
        // 在用户选择器中显示错误
        const modalBody = document.querySelector('#user-selector-modal .modal-body');
        if (modalBody) {
            // 移除之前的错误
            const existingAlert = modalBody.querySelector('.alert-danger');
            if (existingAlert) {
                existingAlert.remove();
            }
            
            // 添加新错误
            const errorAlert = document.createElement('div');
            errorAlert.className = 'alert alert-danger';
            errorAlert.innerHTML = `<i class="bi bi-exclamation-triangle"></i> ${message}`;
            modalBody.insertBefore(errorAlert, modalBody.firstChild);
        }
    }
    
    showWelcomeMessage(message) {
        // 显示欢迎消息
        if (window.showToast) {
            window.showToast(message, 'success');
        } else {
            console.log(message);
        }
    }
    
    // 切换用户
    async switchUser() {
        this.showUserSelector();
    }
    
    // 登出
    logout() {
        this.currentUser = null;
        this.userState = {};
        this.clearUserStorage();
        
        // 清空界面状态
        this.clearUIState();
        
        // 重新显示用户选择器
        setTimeout(() => {
            this.showUserSelector();
        }, 500);
        
        this.showWelcomeMessage('已退出登录');
    }
    
    clearUserStorage() {
        localStorage.removeItem('current_user');
        localStorage.removeItem('user_state');
    }
    
    clearUIState() {
        // 清空聊天记录
        const chatContainer = document.getElementById('chat-container');
        if (chatContainer) {
            chatContainer.innerHTML = `
                <div class="message system-message">
                    <div class="message-bubble">
                        🔄 正在切换用户，请稍候...
                    </div>
                </div>
            `;
        }
        
        // 重置统计数据
        if (window.updateStats) {
            window.currentState = {
                dbConnected: false,
                conversationCount: 0,
                sqlCount: 0
            };
            window.updateStats();
        }
    }
    
    // 状态管理
    setState(key, value) {
        this.userState[key] = value;
        this.saveUserToStorage();
    }
    
    getState(key, defaultValue = null) {
        return this.userState[key] || defaultValue;
    }
    
    // 事件监听
    addUserChangeListener(callback) {
        this.listeners.push(callback);
    }
    
    notifyUserChange() {
        this.listeners.forEach(callback => {
            try {
                callback(this.currentUser);
            } catch (e) {
                console.warn('用户变更监听器执行失败:', e);
            }
        });
    }
    
    // 获取当前用户信息
    getCurrentUser() {
        return this.currentUser;
    }
    
    // 检查是否已登录
    isLoggedIn() {
        return this.currentUser !== null;
    }
    
    // 更新最后活动时间
    updateActivity() {
        if (this.currentUser) {
            this.currentUser.lastActivity = Date.now();
            this.saveUserToStorage();
        }
    }
}

// 创建全局用户管理器实例
const userManager = new UserStateManager();

// 定期更新活动时间
setInterval(() => {
    userManager.updateActivity();
}, 60000); // 每分钟更新一次

// 页面可见性变化时更新活动时间
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
        userManager.updateActivity();
    }
});

// 导出给其他脚本使用
window.userManager = userManager;