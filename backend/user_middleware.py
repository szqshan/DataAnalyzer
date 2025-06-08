# user_middleware.py - 用户管理中间件（修复编码问题）
from pathlib import Path
import json
import os
from datetime import datetime
from functools import wraps
from flask import request, jsonify
import hashlib
import time

class UserManager:
    """用户管理器 - 负责用户识别和文件路径管理"""
    
    def __init__(self, base_data_dir="data"):
        self.base_data_dir = Path(base_data_dir)
        self.base_data_dir.mkdir(exist_ok=True)
        
        # 创建共享目录
        (self.base_data_dir / "shared" / "uploads").mkdir(parents=True, exist_ok=True)
        
        print(f"✅ 用户管理器初始化完成，数据目录: {self.base_data_dir.absolute()}")
    
    def get_user_from_request(self, request):
        """从请求中提取用户信息"""
        # 策略1: 从请求头获取（推荐方式）
        user_id = request.headers.get('X-User-ID')
        username = request.headers.get('X-Username')
        
        # 处理URL编码的用户名
        if username:
            try:
                import urllib.parse
                # 检查是否是URL编码的字符串
                if '%' in username:
                    username = urllib.parse.unquote(username)
                    print(f"✅ 已解码用户名: {username}")
            except Exception as e:
                print(f"⚠️ 解码用户名失败: {e}")
        
        # 策略2: 从URL参数获取（GET请求）
        if not user_id:
            user_id = request.args.get('userId')
            username = request.args.get('username', '')
        
        # 策略3: 从请求体获取（POST请求）
        if not user_id and request.is_json:
            try:
                json_data = request.get_json()
                if json_data:
                    user_id = json_data.get('userId')
                    username = json_data.get('username', '')
            except:
                pass
        
        # 策略4: 从表单数据获取（文件上传）
        if not user_id and request.form:
            user_id = request.form.get('userId')
            username = request.form.get('username', '')
        
        # 如果都没有，生成临时用户ID
        if not user_id:
            # 基于IP和UserAgent生成相对稳定的临时ID
            ip = request.remote_addr or 'unknown'
            user_agent = request.headers.get('User-Agent', 'unknown')
            
            # 🔥 修复编码问题：确保所有字符串都使用UTF-8编码
            temp_seed = f"{ip}_{user_agent}_{int(time.time() / 3600)}"
            # 使用UTF-8编码进行哈希
            user_id = f"guest_{hashlib.md5(temp_seed.encode('utf-8')).hexdigest()[:8]}"
            # 使用英文避免编码问题
            username = username or f"Guest_{user_id[-4:]}"
        
        # 🔥 确保用户名使用安全字符
        if username:
            # 清理用户名中可能导致编码问题的字符
            username = self._clean_username(username)
        
        return {
            'user_id': str(user_id),
            'username': username or f"User_{user_id}",
            'is_guest': str(user_id).startswith('guest_')
        }
    
    def _clean_username(self, username):
        """清理用户名，避免编码问题"""
        if not username:
            return "Unknown"
        
        # 替换常见的中文字符为英文
        replacements = {
            '用户': 'User',
            '访客': 'Guest', 
            '管理员': 'Admin',
            '测试': 'Test',
            '张三': 'Zhang',
            '李四': 'Li',
            '王五': 'Wang',
            '数据分析师': 'Analyst',
            '业务经理': 'Manager',
            '产品经理': 'PM'
        }
        
        cleaned = str(username)
        for chinese, english in replacements.items():
            cleaned = cleaned.replace(chinese, english)
        
        # 如果仍有非ASCII字符，使用编码安全的方式处理
        try:
            # 尝试编码为latin-1，如果失败则使用ASCII安全版本
            cleaned.encode('latin-1')
            return cleaned
        except UnicodeEncodeError:
            # 转换为ASCII安全格式
            safe_name = cleaned.encode('ascii', 'ignore').decode('ascii')
            if not safe_name:
                return f"User_{int(time.time()) % 10000}"
            return safe_name
    
    def get_user_directory(self, user_id):
        """获取用户专属目录"""
        # 确保用户ID是ASCII安全的
        safe_user_id = str(user_id).encode('ascii', 'ignore').decode('ascii')
        if not safe_user_id:
            safe_user_id = f"user_{int(time.time()) % 10000}"
            
        user_dir = self.base_data_dir / f"user_{safe_user_id}"
        user_dir.mkdir(exist_ok=True)
        
        # 创建用户子目录
        (user_dir / "reports").mkdir(exist_ok=True)
        (user_dir / "uploads").mkdir(exist_ok=True)
        
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
    
    def save_user_info(self, user_info):
        """保存用户信息到文件"""
        user_dir = self.get_user_directory(user_info['user_id'])
        user_info_file = user_dir / "user_info.json"
        
        # 🔥 确保所有字符串字段都是编码安全的
        safe_user_info = {}
        for key, value in user_info.items():
            if isinstance(value, str):
                safe_user_info[key] = self._clean_username(value) if key == 'username' else value
            else:
                safe_user_info[key] = value
        
        user_data = {
            **safe_user_info,
            'last_activity': datetime.now().isoformat(),
            'created_at': datetime.now().isoformat() if not user_info_file.exists() else None
        }
        
        # 如果文件已存在，保留创建时间
        if user_info_file.exists():
            try:
                with open(user_info_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    user_data['created_at'] = existing_data.get('created_at', user_data['created_at'])
            except Exception as e:
                print(f"⚠️  读取现有用户文件失败: {e}")
        
        try:
            with open(user_info_file, 'w', encoding='utf-8') as f:
                json.dump(user_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  保存用户信息失败: {e}")
            # 使用ASCII安全模式保存
            with open(user_info_file, 'w', encoding='utf-8') as f:
                json.dump(user_data, f, ensure_ascii=True, indent=2)
        
        return user_data
    
    def get_user_stats(self, user_id):
        """获取用户统计信息"""
        try:
            paths = self.get_user_paths(user_id)
            
            stats = {
                'user_id': str(user_id),
                'has_database': paths['db_path'].exists(),
                'database_size': paths['db_path'].stat().st_size if paths['db_path'].exists() else 0,
                'has_memory': paths['memory_path'].exists(),
                'memory_size': paths['memory_path'].stat().st_size if paths['memory_path'].exists() else 0,
                'reports_count': len(list(paths['reports_dir'].glob('*.html'))) if paths['reports_dir'].exists() else 0,
                'total_size': 0
            }
            
            # 计算总大小
            if paths['user_dir'].exists():
                try:
                    for file_path in paths['user_dir'].rglob('*'):
                        if file_path.is_file():
                            stats['total_size'] += file_path.stat().st_size
                except Exception as e:
                    print(f"⚠️  计算用户目录大小失败: {e}")
            
            return stats
            
        except Exception as e:
            print(f"⚠️  获取用户统计失败: {e}")
            return {
                'user_id': str(user_id),
                'has_database': False,
                'database_size': 0,
                'has_memory': False,
                'memory_size': 0,
                'reports_count': 0,
                'total_size': 0
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
            
            # 保存用户信息
            user_data = user_manager.save_user_info(user_info)
            
            # 将用户信息传递给路由函数
            return f(user_data, *args, **kwargs)
            
        except UnicodeEncodeError as e:
            print(f"⚠️  编码错误: {e}")
            # 使用默认用户信息
            default_user = {
                'user_id': f"guest_{int(time.time()) % 10000}",
                'username': 'DefaultUser',
                'is_guest': True
            }
            user_data = user_manager.save_user_info(default_user)
            return f(user_data, *args, **kwargs)
            
        except Exception as e:
            error_msg = f"用户身份识别失败: {str(e)}"
            print(f"❌ {error_msg}")
            return jsonify({
                "success": False, 
                "message": error_msg
            }), 500
    
    return decorated_function

def get_current_user():
    """在路由中直接获取当前用户信息"""
    return user_manager.get_user_from_request(request)