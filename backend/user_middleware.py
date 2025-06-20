# user_middleware.py - 清理调试输出版本
from pathlib import Path
import json
import os
from datetime import datetime
from functools import wraps
from flask import request, jsonify
import hashlib
import time
import urllib.parse
import re

class UserManager:
    """精简版用户管理器 - 清理调试输出"""
    
    def __init__(self, base_data_dir="data"):
        self.base_data_dir = Path(base_data_dir)
        self.base_data_dir.mkdir(exist_ok=True)
        print(f"✅ 用户管理器初始化完成")
    
    def get_user_from_request(self, request):
        """从请求中提取用户信息"""
        user_id = None
        username = None
        
        # 策略1: 从请求头获取（优先级最高）
        user_id = request.headers.get('X-User-ID')
        username = request.headers.get('X-Username')
        
        # URL解码用户名
        if username:
            try:
                if '%' in username:
                    username = urllib.parse.unquote(username)
                username = self._safe_username(username)
            except:
                username = None
        
        # 策略2: 从URL参数获取
        if not user_id:
            user_id = request.args.get('userId')
            if not username:
                username = request.args.get('username', '')
        
        # 策略3: 从请求体获取（用于JSON和FormData）
        if not user_id:
            try:
                # 检查JSON数据
                if request.is_json:
                    json_data = request.get_json()
                    if json_data:
                        user_id = json_data.get('userId')
                        if not username:
                            username = json_data.get('username', '')
                
                # 检查表单数据（用于文件上传）
                elif request.form:
                    user_id = request.form.get('userId')
                    if not username:
                        username = request.form.get('username', '')
            except:
                pass
        
        # 策略4: 生成一致的访客ID（基于IP和User-Agent）
        if not user_id:
            ip = request.remote_addr or 'unknown'
            user_agent = request.headers.get('User-Agent', 'unknown')
            
            # 创建一个相对稳定的访客ID（在同一小时内保持一致）
            hour_seed = int(time.time() / 3600)  # 每小时变化
            temp_seed = f"{ip}_{user_agent}_{hour_seed}"
            guest_hash = hashlib.md5(temp_seed.encode('utf-8')).hexdigest()[:8]
            user_id = f"guest_{guest_hash}"
            
            if not username:
                username = f"Guest_{guest_hash[-4:]}"
        
        # 确保用户名安全
        if username:
            username = self._safe_username(username)
        else:
            username = f"User_{str(user_id)[-4:]}"
        
        user_info = {
            'user_id': str(user_id),
            'username': username,
            'is_guest': str(user_id).startswith('guest_')
        }
        
        return user_info
    
    def _safe_username(self, username):
        """安全的用户名处理"""
        if not username:
            return "Unknown"
        
        # 移除不安全字符
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', str(username))
        
        # 限制长度
        safe_name = safe_name[:50]
        
        # 确保不为空
        if not safe_name.strip():
            return f"User_{int(time.time()) % 10000}"
        
        return safe_name.strip()
    
    def get_user_directory(self, user_id):
        """获取用户专属目录"""
        # 确保用户ID是文件系统安全的
        safe_user_id = str(user_id)
        
        # 移除不安全字符
        safe_user_id = re.sub(r'[<>:"/\\|?*]', '_', safe_user_id)
        
        if not safe_user_id:
            safe_user_id = f"user_{int(time.time()) % 10000}"
            
        user_dir = self.base_data_dir / f"user_{safe_user_id}"
        user_dir.mkdir(exist_ok=True, parents=True)
        
        # 创建用户子目录
        (user_dir / "reports").mkdir(exist_ok=True, parents=True)
        (user_dir / "uploads").mkdir(exist_ok=True, parents=True)
        
        # 确保数据库文件存在
        db_path = user_dir / "analysis.db"
        if not db_path.exists():
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            conn.close()
        
        return user_dir
    
    def get_user_paths(self, user_id):
        """获取用户所有相关路径"""
        user_dir = self.get_user_directory(user_id)
        
        return {
            'user_dir': user_dir,
            'db_path': user_dir / "analysis.db",
            'memory_path': user_dir / "conversation_memory.json",
            'reports_dir': user_dir / "reports",
            'uploads_dir': user_dir / "uploads"
        }

# 全局用户管理器实例
user_manager = UserManager()

def require_user(f):
    """装饰器：自动处理用户身份识别"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # 获取用户信息
            user_info = user_manager.get_user_from_request(request)
            
            # 验证用户信息
            if not user_info.get('user_id'):
                return jsonify({
                    "success": False, 
                    "message": "用户身份识别失败"
                }), 400
            
            # 将用户信息传递给路由函数
            return f(user_info, *args, **kwargs)
            
        except Exception as e:
            return jsonify({
                "success": False, 
                "message": f"用户身份识别失败: {str(e)}"
            }), 500
    
    return decorated_function

def get_current_user():
    """在路由中直接获取当前用户信息"""
    return user_manager.get_user_from_request(request)