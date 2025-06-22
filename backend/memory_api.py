# memory_api.py - 独立记忆管理API接口
# 功能：提供记忆管理的HTTP接口，不影响主程序

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import traceback
from pathlib import Path
import logging

# 导入记忆管理器
from memory_manager import MemoryManager

# 创建独立的Flask应用
memory_app = Flask(__name__)
CORS(memory_app, resources={r"/memory/*": {"origins": "*"}}, supports_credentials=True)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_user_info(request):
    """从请求中提取用户信息"""
    # 从请求头获取用户信息
    user_id = request.headers.get('X-User-ID')
    username = request.headers.get('X-Username')
    username_b64 = request.headers.get('X-Username-B64')
    api_key = request.headers.get('X-API-Key')
    
    # 处理Base64编码的用户名
    if username_b64 and not username:
        try:
            import base64
            username = base64.b64decode(username_b64).decode('utf-8')
        except Exception:
            username = username_b64
    
    # 如果请求头中没有，尝试从请求体获取
    if not user_id or not api_key:
        data = request.get_json() or {}
        user_id = user_id or data.get('userId')
        username = username or data.get('username')
        api_key = api_key or data.get('apiKey')
    
    if not user_id or not api_key:
        return None, "缺少用户ID或API密钥"
    
    return {
        'user_id': user_id,
        'username': username or user_id,
        'api_key': api_key
    }, None

def get_user_data_path(user_id: str) -> Path:
    """获取用户数据目录路径"""
    # 根据主程序的路径规则构建用户数据路径
    user_folder = f"user_{user_id.lower().replace(' ', '_')}"
    user_data_path = Path("data") / user_folder
    return user_data_path

def find_conversation_db_path(user_id: str, conversation_id: str) -> str:
    """查找对话的数据库文件路径"""
    user_data_path = get_user_data_path(user_id)
    
    # 查找对话元数据文件
    conversations_meta_file = user_data_path / f"{user_id}_conversations.json"
    
    if not conversations_meta_file.exists():
        return None
    
    try:
        with open(conversations_meta_file, 'r', encoding='utf-8') as f:
            conversations_meta = json.load(f)
        
        if conversation_id in conversations_meta.get('conversations', {}):
            conv_info = conversations_meta['conversations'][conversation_id]
            return conv_info.get('history_path')
    except Exception as e:
        logger.error(f"读取对话元数据失败: {e}")
    
    return None

@memory_app.route('/memory/analyze', methods=['POST'])
def analyze_memory():
    """分析对话记忆接口"""
    try:
        # 提取用户信息
        user_info, error = extract_user_info(request)
        if error:
            return jsonify({"success": False, "message": error}), 400
        
        data = request.get_json()
        conversation_id = data.get('conversation_id')
        
        if not conversation_id:
            return jsonify({"success": False, "message": "缺少对话ID"}), 400
        
        logger.info(f"🧠 用户 {user_info['user_id']} 请求分析对话记忆: {conversation_id}")
        
        # 查找对话数据库路径
        db_path = find_conversation_db_path(user_info['user_id'], conversation_id)
        if not db_path:
            return jsonify({
                "success": False, 
                "message": "未找到对话记录或对话不存在"
            }), 404
        
        if not os.path.exists(db_path):
            return jsonify({
                "success": False, 
                "message": f"对话数据库文件不存在: {db_path}"
            }), 404
        
        # 创建记忆管理器
        memory_manager = MemoryManager(user_info['api_key'])
        
        # 执行记忆分析
        result = memory_manager.analyze_conversation_memory(db_path, conversation_id)
        
        logger.info(f"✅ 记忆分析完成: {user_info['user_id']} - {conversation_id}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ 记忆分析失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"记忆分析失败: {str(e)}"
        }), 500

@memory_app.route('/memory/stats', methods=['POST'])
def get_memory_stats():
    """获取记忆统计信息接口"""
    try:
        # 提取用户信息
        user_info, error = extract_user_info(request)
        if error:
            return jsonify({"success": False, "message": error}), 400
        
        data = request.get_json()
        conversation_id = data.get('conversation_id')
        
        if not conversation_id:
            return jsonify({"success": False, "message": "缺少对话ID"}), 400
        
        # 查找对话数据库路径
        db_path = find_conversation_db_path(user_info['user_id'], conversation_id)
        if not db_path or not os.path.exists(db_path):
            return jsonify({
                "success": False, 
                "message": "未找到对话记录"
            }), 404
        
        # 创建记忆管理器并获取统计信息
        memory_manager = MemoryManager(user_info['api_key'])
        memory_manager.current_db_path = db_path
        stats = memory_manager._get_memory_stats(conversation_id)
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"❌ 获取记忆统计失败: {e}")
        return jsonify({
            "success": False,
            "message": f"获取统计信息失败: {str(e)}"
        }), 500

@memory_app.route('/memory/conversations', methods=['POST'])
def get_user_conversations():
    """获取用户的对话列表"""
    try:
        # 提取用户信息
        user_info, error = extract_user_info(request)
        if error:
            return jsonify({"success": False, "message": error}), 400
        
        user_data_path = get_user_data_path(user_info['user_id'])
        conversations_meta_file = user_data_path / f"{user_info['user_id']}_conversations.json"
        
        if not conversations_meta_file.exists():
            return jsonify({
                "success": True,
                "conversations": [],
                "message": "用户暂无对话记录"
            })
        
        try:
            with open(conversations_meta_file, 'r', encoding='utf-8') as f:
                conversations_meta = json.load(f)
            
            conversations = []
            for conv_id, conv_info in conversations_meta.get('conversations', {}).items():
                if conv_info.get('user_id') == user_info['user_id']:
                    conversations.append({
                        'conversation_id': conv_id,
                        'conversation_name': conv_info.get('conversation_name'),
                        'description': conv_info.get('description'),
                        'created_time': conv_info.get('created_time'),
                        'last_activity': conv_info.get('last_activity'),
                        'message_count': conv_info.get('message_count', 0),
                        'status': conv_info.get('status')
                    })
            
            # 按最后活动时间排序
            conversations.sort(key=lambda x: x.get('last_activity', ''), reverse=True)
            
            return jsonify({
                "success": True,
                "conversations": conversations
            })
            
        except Exception as e:
            logger.error(f"读取对话列表失败: {e}")
            return jsonify({
                "success": False,
                "message": f"读取对话列表失败: {str(e)}"
            }), 500
        
    except Exception as e:
        logger.error(f"❌ 获取对话列表失败: {e}")
        return jsonify({
            "success": False,
            "message": f"获取对话列表失败: {str(e)}"
        }), 500

@memory_app.route('/memory/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        "success": True,
        "service": "Memory Management API",
        "status": "running",
        "version": "1.0.0"
    })

@memory_app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "message": "API接口不存在"
    }), 404

@memory_app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "message": "服务器内部错误"
    }), 500

def run_memory_api(host='localhost', port=5002, debug=False):
    """启动记忆管理API服务"""
    print(f"🧠 记忆管理API启动中...")
    print(f"📡 服务地址: http://{host}:{port}")
    print(f"🔧 API接口:")
    print(f"   - POST /memory/analyze - 分析对话记忆")
    print(f"   - POST /memory/stats - 获取记忆统计")
    print(f"   - POST /memory/conversations - 获取对话列表")
    print(f"   - GET  /memory/health - 健康检查")
    
    memory_app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    # 独立运行记忆管理API
    run_memory_api(debug=True) 