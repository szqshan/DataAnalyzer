# user_middleware.py - 清理调试输出版本
from pathlib import Path
import json
import os
from datetime import datetime
from functools import wraps
from flask import request, jsonify
import time
import urllib.parse
import re

class UserManager:
    """用户管理器 - 仅支持付费用户"""
    
    def __init__(self, base_data_dir="data"):
        self.base_data_dir = Path(base_data_dir)
        self.base_data_dir.mkdir(exist_ok=True)
    
    def get_user_from_request(self, request, use_default=False):
        """从请求中提取用户信息 - 可选择使用默认用户"""
        user_id = None
        username = None
        api_key = None
        
        # 策略1: 从请求头获取（优先级最高）
        user_id = request.headers.get('X-User-ID')
        username = request.headers.get('X-Username')
        api_key = request.headers.get('X-API-Key')
        
        # 解码用户名（支持 Base64 和 URL 编码）
        if username:
            try:
                # 首先尝试 Base64 解码（前端使用 btoa 编码）
                try:
                    import base64
                    decoded_bytes = base64.b64decode(username)
                    username = urllib.parse.unquote(decoded_bytes.decode('utf-8'))
                except:
                    # 如果 Base64 解码失败，尝试 URL 解码
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
            if not api_key:
                api_key = request.args.get('apiKey')
        
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
                        if not api_key:
                            api_key = json_data.get('apiKey')
                
                # 检查表单数据（用于文件上传）
                elif request.form:
                    user_id = request.form.get('userId')
                    if not username:
                        username = request.form.get('username', '')
                    if not api_key:
                        api_key = request.form.get('apiKey')
            except:
                pass
        
        # 如果没有找到用户信息且允许使用默认用户
        if use_default and (not user_id or not api_key):
            # 从环境变量获取默认API密钥
            default_api_key = os.getenv('ANTHROPIC_API_KEY')
            if default_api_key:
                user_id = 'default_user'
                username = '数据分析用户'
                api_key = default_api_key
        
        # 验证必要字段
        if not user_id or not api_key:
            return None
        
        # 确保用户名安全
        if username:
            username = self._safe_username(username)
        else:
            username = f"User_{str(user_id)[-8:]}"
        
        user_info = {
            'user_id': str(user_id),
            'username': username,
            'is_guest': False,  # 不再支持访客模式
            'api_key': api_key
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
    """装饰器：要求用户提供有效的user_id和api_key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # 获取用户信息
            user_info = user_manager.get_user_from_request(request)
            # 验证用户信息 - 必须有user_id和api_key
            if not user_info:
                return jsonify({
                    "success": False, 
                    "message": "需要提供有效的用户ID和API Key",
                    "error_code": "MISSING_CREDENTIALS"
                }), 401
            if not user_info.get('user_id') or not user_info.get('api_key'):
                return jsonify({
                    "success": False, 
                    "message": "用户ID和API Key不能为空",
                    "error_code": "INVALID_CREDENTIALS"
                }), 401
            # 将用户信息传递给路由函数
            return f(user_info, *args, **kwargs)
        except Exception as e:
            return jsonify({
                "success": False, 
                "message": f"用户身份识别失败: {str(e)}",
                "error_code": "AUTH_ERROR"
            }), 500
    return decorated_function

def allow_default_user(f):
    """装饰器：允许使用默认用户（无需认证）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # 获取用户信息，允许使用默认用户
            user_info = user_manager.get_user_from_request(request, use_default=True)
            
            # 如果仍然没有用户信息，返回错误
            if not user_info:
                return jsonify({
                    "success": False, 
                    "message": "无法获取用户信息，请检查环境配置",
                    "error_code": "NO_USER_INFO"
                }), 500
            
            # 将用户信息传递给路由函数
            return f(user_info, *args, **kwargs)
        except Exception as e:
            return jsonify({
                "success": False, 
                "message": f"用户身份识别失败: {str(e)}",
                "error_code": "AUTH_ERROR"
            }), 500
    return decorated_function

def get_current_user():
    """在路由中直接获取当前用户信息"""
    return user_manager.get_user_from_request(request)

def get_current_user_or_default():
    """在路由中获取当前用户信息或默认用户"""
    return user_manager.get_user_from_request(request, use_default=True)