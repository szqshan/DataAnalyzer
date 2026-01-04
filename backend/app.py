from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import os
import json
import traceback
from werkzeug.utils import secure_filename
from datetime import datetime
from pathlib import Path
import time
import logging
from dotenv import load_dotenv
load_dotenv()

# 导入精简版用户管理中间件
from user_middleware import user_manager, require_user, allow_default_user, get_current_user

# 导入分析器类
from database_analyzer import DatabaseAnalyzer

# 导入对话历史记录管理器
from conversation_history import ConversationHistoryManager

# 导入模板管理器
from template_manager import TemplateManager

# 导入配置和Prompt
from config import Config
from prompts import Prompts

app = Flask(__name__)

# 禁用Flask默认日志输出
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
app.logger.setLevel(logging.ERROR)

# 配置CORS
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# 配置
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH  # 100MB最大文件大小

# 用户分析器和历史记录管理器实例缓存
user_analyzers = {}
user_history_managers = {}
user_template_managers = {}

def extract_query_from_data(data):
    """安全地从请求数据中提取查询字符串"""
    query_raw = data.get('query', '')
    
    if isinstance(query_raw, str):
        return query_raw.strip()
    
    if isinstance(query_raw, list):
        # 处理列表情况 - 合并所有非空文本
        parts = []
        for item in query_raw:
            if isinstance(item, dict):
                parts.append(str(item.get('text', '')).strip())
            else:
                parts.append(str(item).strip())
        return ' '.join(filter(None, parts))
        
    if isinstance(query_raw, dict):
        return str(query_raw.get('text', '')).strip()
        
    return str(query_raw).strip()

def get_user_analyzer(user_data, api_key):
    """获取或创建用户专属的分析器实例"""
    user_id = user_data['user_id']
    # 自动strip api_key
    api_key = api_key.strip() if isinstance(api_key, str) else api_key
    
    # 为每个用户+API Key组合创建唯一标识
    analyzer_key = f"{user_id}_{hash(api_key) % 10000}"
    
    if analyzer_key not in user_analyzers:
        if not api_key:
            raise ValueError("未提供用户API密钥")
        
        # 获取API基础URL
        base_url = os.getenv('ANTHROPIC_BASE_URL')
        
        # 验证API密钥有效性
        try:
            from anthropic import Anthropic
            client_params = {"api_key": api_key}
            if base_url:
                client_params["base_url"] = base_url
            
            test_client = Anthropic(**client_params)
            # 发送一个简单的测试请求来验证API密钥
            test_response = test_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
        except Exception as e:
            if "authentication" in str(e).lower() or "api_key" in str(e).lower() or "unauthorized" in str(e).lower():
                raise ValueError("API密钥无效，请检查您的凭据")
            else:
                raise ValueError(f"API连接失败: {str(e)}")
        
        # 创建分析器
        analyzer = DatabaseAnalyzer(api_key, base_url=base_url)
        
        # 获取用户路径
        user_paths = user_manager.get_user_paths(user_id)
        
        # 设置用户专属路径
        analyzer.current_db_path = str(user_paths['db_path'])
        analyzer.current_table_name = "data_table"  # 简化：固定表名
        
        # 缓存分析器
        user_analyzers[analyzer_key] = analyzer
        
    return user_analyzers[analyzer_key]

def get_user_history_manager(user_data):
    """获取或创建用户专属的历史记录管理器实例"""
    user_id = user_data['user_id']
    
    if user_id not in user_history_managers:
        # 获取用户路径
        user_paths = user_manager.get_user_paths(user_id)
        
        # 创建历史记录管理器
        history_manager = ConversationHistoryManager(user_paths, user_id)
        
        # 缓存管理器
        user_history_managers[user_id] = history_manager
        
    return user_history_managers[user_id]

def get_user_template_manager(user_data, api_key):
    """获取或创建用户专属的模板管理器实例"""
    user_id = user_data['user_id']
    
    # 模板管理器也需要分析器来执行AI任务，所以需要API Key
    # 使用与分析器相同的Key生成逻辑
    manager_key = f"{user_id}_{hash(api_key) % 10000}" if api_key else user_id
    
    if manager_key not in user_template_managers:
        user_paths = user_manager.get_user_paths(user_id)
        
        # 尝试获取分析器实例（如果提供了API Key）
        analyzer = None
        if api_key:
            try:
                analyzer = get_user_analyzer(user_data, api_key)
            except:
                pass
        
        manager = TemplateManager(user_paths, user_id, analyzer)
        user_template_managers[manager_key] = manager
        
    return user_template_managers[manager_key]

@app.route('/api/status', methods=['GET'])
@allow_default_user
def get_status(user_data):
    """获取系统状态"""
    try:
        api_key = user_data.get('api_key')
        if not api_key:
            return jsonify({
                "system_ready": False,
                "error": "未提供API密钥",
                "database_connected": False,
                "user_info": user_data
            }), 400
        
        analyzer = get_user_analyzer(user_data, api_key)
        
        # 获取记录数
        record_count = 0
        if analyzer.current_db_path and analyzer.current_table_name:
            try:
                result = analyzer.query_database(f"SELECT COUNT(*) FROM {analyzer.current_table_name}")
                if "data" in result and result["data"]:
                    record_count = result["data"][0][0]
            except:
                pass
        
        status = {
            "system_ready": True,
            "database_connected": analyzer.current_db_path is not None,
            "database_path": analyzer.current_db_path or "",
            "table_name": analyzer.current_table_name or "",
            "record_count": record_count,
            "api_status": "connected",
            "user_info": user_data
        }
        
        return jsonify(status)
    
    except Exception as e:
        return jsonify({
            "system_ready": False,
            "error": str(e),
            "database_connected": False,
            "user_info": user_data
        }), 500

@app.route('/api/upload', methods=['POST'])
@allow_default_user
def upload_csv(user_data):
    """上传CSV文件并导入到用户专属数据库"""
    try:
        api_key = user_data.get('api_key')
        if not api_key:
            return jsonify({"success": False, "message": "未提供API密钥"}), 400
        
        analyzer = get_user_analyzer(user_data, api_key)
        
        # 检查文件
        if 'file' not in request.files:
            return jsonify({"success": False, "message": "未找到文件"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "message": "未选择文件"}), 400
        
        # 检查文件格式 - 只支持CSV
        file_ext = os.path.splitext(file.filename.lower())[1]
        if file_ext != '.csv':
            return jsonify({
                "success": False, 
                "message": f"只支持CSV文件格式，当前文件格式: {file_ext}"
            }), 400
        
        # 获取用户路径
        user_paths = user_manager.get_user_paths(user_data['user_id'])
        user_db_path = str(user_paths['db_path'])
        user_uploads_dir = user_paths['uploads_dir']
        
        # 确保上传目录存在
        if not os.path.exists(user_uploads_dir):
            os.makedirs(user_uploads_dir)
        
        # 保存文件到用户专属目录
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{filename}"
        file_path = user_uploads_dir / safe_filename
        
        file.save(str(file_path))
        
        # 生成动态表名（基于文件名）
        table_name = analyzer._generate_table_name(filename)
        
        # 导入数据库
        result = analyzer.import_csv_to_sqlite(str(file_path), table_name, user_db_path)
        
        if result["success"]:
            # 清理临时文件
            try:
                os.remove(str(file_path))
            except:
                pass
            
            return jsonify({
                "success": True,
                "message": result["message"],
                "data": {
                    "rows_imported": result.get("rows_imported", 0),
                    "columns": result.get("columns", []),
                    "table_name": table_name,
                    "db_path": user_db_path,
                    "file_format": result.get("file_format", ".csv"),
                    "user_info": user_data
                }
            })
        else:
            return jsonify(result), 400
            
    except Exception as e:
        print(f"❌ 上传失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"上传失败: {str(e)}",
            "user_info": user_data
        }), 500

@app.route('/api/tables-info', methods=['GET'])
@allow_default_user
def get_tables_info(user_data):
    """获取当前对话中所有表的详细信息"""
    try:
        api_key = user_data.get('api_key')
        if not api_key:
            return jsonify({"success": False, "message": "未提供API密钥"}), 400
        
        analyzer = get_user_analyzer(user_data, api_key)
        
        # 检查是否有数据库连接
        if not analyzer.current_db_path:
            return jsonify({
                "success": False, 
                "message": "未连接到数据库，请先上传数据文件"
            }), 400
        
        # 获取表结构信息
        table_schema_result = analyzer.get_table_schema()
        
        # 如果返回字符串，说明是错误信息
        if isinstance(table_schema_result, str):
            return jsonify({
                "success": False,
                "message": table_schema_result
            }), 400
        
        # 返回成功结果
        return jsonify({
            "success": True,
            "message": f"成功获取 {table_schema_result['total_tables']} 个表的信息",
            "data": table_schema_result,
            "user_info": user_data
        })
        
    except Exception as e:
        print(f"❌ 获取表信息失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"获取表信息失败: {str(e)}",
            "user_info": user_data
        }), 500

@app.route('/api/tables/delete', methods=['POST'])
@allow_default_user
def delete_table(user_data):
    """删除指定的数据库表"""
    try:
        api_key = user_data.get('api_key')
        if not api_key:
            return jsonify({"success": False, "message": "未提供API密钥"}), 400
        
        analyzer = get_user_analyzer(user_data, api_key)
        
        # 获取请求数据
        data = request.get_json()
        if not data or 'table_name' not in data:
            return jsonify({
                "success": False,
                "message": "缺少表名参数"
            }), 400
        
        table_name = data['table_name'].strip()
        if not table_name:
            return jsonify({
                "success": False,
                "message": "表名不能为空"
            }), 400
        
        # 执行删除操作
        result = analyzer.delete_table(table_name)
        
        if result["success"]:
            return jsonify({
                "success": True,
                "message": result["message"],
                "data": {
                    "deleted_table": result["deleted_table"],
                    "deleted_rows": result["deleted_rows"],
                    "remaining_tables": result["remaining_tables"]
                },
                "user_info": user_data
            })
        else:
            return jsonify({
                "success": False,
                "message": result["message"],
                "user_info": user_data
            }), 400
            
    except Exception as e:
        print(f"❌ 删除表操作失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"删除表操作失败: {str(e)}",
            "user_info": user_data
        }), 500

@app.route('/api/analyze-stream', methods=['POST'])
@allow_default_user
def analyze_data_stream(user_data):
    """流式数据分析接口"""
    try:
        data = request.get_json()
        query = extract_query_from_data(data)
        conversation_id = data.get('conversation_id')
        
        if not query:
            return jsonify({"success": False, "message": "查询内容不能为空"}), 400
        
        api_key = user_data.get('api_key')
        if not api_key:
            return jsonify({"success": False, "message": "未提供API密钥"}), 400
        
        analyzer = get_user_analyzer(user_data, api_key)
        history_manager = get_user_history_manager(user_data)
        
        if not analyzer.current_db_path:
            return jsonify({"success": False, "message": "请先上传数据文件"}), 400
            
        def generate_stream():
            try:
                # 检查是否有当前对话，如果没有则返回错误
                if not history_manager.current_conversation_id:
                    error_msg = "请先创建或选择一个对话"
                    yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
                    return
                
                # 支持前端传入conversation_id
                if conversation_id and conversation_id != history_manager.current_conversation_id:
                    # 切换到指定对话
                    history_manager.switch_conversation(conversation_id, user_data['user_id'])
                
                current_conversation = history_manager.get_current_conversation_info()
                
                # 获取历史对话上下文（当前对话内的历史）
                recent_conversations = history_manager.get_recent_conversations(user_data['user_id'], 3)
                context_info = ""
                if recent_conversations:
                    context_info = "\n**历史对话上下文：**\n"
                    for i, conv in enumerate(recent_conversations, 1):
                        context_info += f"{i}. 查询: {conv['user_query']}\n"
                        if conv.get('analysis_summary'):
                            context_info += f"   结果摘要: {conv['analysis_summary'][:100]}...\n"
                        context_info += f"   时间: {conv['start_time'][:19]}\n"
                        context_info += f"   对话: {conv.get('conversation_name', '未知对话')}\n\n"
                
                # 发送开始分析消息
                start_msg = f'🚀 开始智能分析数据... (当前对话: {current_conversation["conversation_name"]})'
                yield f"data: {json.dumps({'type': 'status', 'message': start_msg})}\n\n"
                
                # 构建系统提示词
                tables_summary = analyzer.get_conversation_tables_summary()
                custom_system_prompt = data.get('system_prompt')
                
                # 准备格式化参数
                format_args = {
                    "username": user_data['username'],
                    "db_path": analyzer.current_db_path,
                    "conversation_name": current_conversation['conversation_name'],
                    "conversation_id": current_conversation['conversation_id'],
                    "tables_summary": tables_summary,
                    "context_info": context_info,
                    "query": query
                }
                
                if custom_system_prompt:
                    # 如果前端提供了Prompt，尝试格式化它
                    try:
                        system_prompt = custom_system_prompt.format(**format_args)
                    except Exception as e:
                        # 如果格式化失败，追加上下文信息
                        system_prompt = custom_system_prompt + f"\n\n当前数据库表信息：\n{tables_summary}\n\n可用工具：\n- get_table_info: 获取当前对话中所有表的结构信息\n- query_database: 执行SQL查询获取数据，支持多表查询"
                else:
                    system_prompt = Prompts.ANALYSIS_SYSTEM_PROMPT.format(**format_args)
                
                # 仅首次分析时插入主记录
                import sqlite3
                with sqlite3.connect(history_manager.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT COUNT(*) FROM conversation_history WHERE conversation_id = ?', (current_conversation['conversation_id'],))
                    exists = cursor.fetchone()[0]
                
                if not exists:
                    # 插入主记录
                    history_manager.start_conversation(
                        user_data, query, system_prompt, 
                        analyzer.current_db_path, analyzer.current_table_name
                    )
                
                # 初始化消息历史
                messages = current_conversation.get('messages', [])
                
                # 追加本轮用户消息
                from datetime import datetime
                user_content = query
                if isinstance(user_content, str):
                    user_content_arr = [{"type": "text", "text": user_content}]
                else:
                    user_content_arr = user_content
                
                # 使用append_message方法添加用户消息并获取消息ID
                user_message_id = history_manager.append_message(
                    current_conversation['conversation_id'], 
                    "user", 
                    user_content_arr
                )
                
                # 发送用户消息ID给前端
                if user_message_id:
                    yield f"data: {json.dumps({'type': 'user_message_id', 'message_id': user_message_id})}\n\n"
                
                # 重新获取完整的消息历史（包含新添加的用户消息）
                current_conversation = history_manager.get_current_conversation_info()
                messages = current_conversation.get('messages', [])
                
                # 确保获取到 System Prompt
                if 'system_prompt' in current_conversation and current_conversation['system_prompt']:
                    current_system_prompt = current_conversation['system_prompt']
                else:
                    # 如果数据库里没有（可能是旧数据），使用当前计算的
                    current_system_prompt = system_prompt
                
                # 执行分析循环
                for event in analyzer.run_analysis_loop(
                    messages=messages,
                    system_prompt=current_system_prompt,
                    history_manager=history_manager,
                    current_conversation=current_conversation,
                    max_iterations=Config.MAX_ITERATIONS
                ):
                    yield f"data: {json.dumps(event)}\n\n"
                    
            except Exception as e:
                error_msg = f'分析过程错误: {str(e)}'
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
                
                # 记录错误状态
                if history_manager.current_conversation_id:
                    history_manager.complete_conversation(history_manager.current_conversation_id, 'error', error_msg, 0)
                    
        return Response(
            stream_with_context(generate_stream()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Cache-Control, Content-Type, X-User-ID, X-Username, X-API-Key',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            }
        )
        
    except Exception as e:
        print(f"❌ 分析请求失败: {e}")
        return jsonify({
            "success": False,
            "message": f"处理分析请求失败: {str(e)}"
        }), 500

# 对话管理相关API
@app.route('/api/conversations/create', methods=['POST'])
@allow_default_user
def create_new_conversation(user_data):
    try:
        history_manager = get_user_history_manager(user_data)
        
        # 获取请求参数
        data = request.get_json() or {}
        description = data.get('description')
        # conversation_name 不再从前端接收，由AI自动生成
        
        # 获取分析器实例以清空表列表
        api_key = user_data.get('api_key')
        analyzer = None
        if api_key:
            try:
                analyzer = get_user_analyzer(user_data, api_key)
            except:
                pass  # 如果获取分析器失败，继续创建对话
        
        # 创建新对话
        conversation_info = history_manager.create_new_conversation(
            user_data, None, description, analyzer  # conversation_name设为None，将使用默认值"新对话"
        )
        
        return jsonify({
            'success': True,
            'message': '新对话创建成功',
            'conversation': conversation_info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'创建新对话失败: {str(e)}'
        }), 500

@app.route('/api/conversations/list', methods=['GET'])
@allow_default_user
def get_conversations_list(user_data):
    try:
        history_manager = get_user_history_manager(user_data)
        
        conversations = history_manager.get_conversations_list(user_data['user_id'])
        
        return jsonify({
            'success': True,
            'conversations': conversations,
            'current_conversation_id': history_manager.current_conversation_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取对话列表失败: {str(e)}'
        }), 500

@app.route('/api/conversations/switch', methods=['POST'])
@allow_default_user
def switch_conversation(user_data):
    try:
        history_manager = get_user_history_manager(user_data)
        
        # 获取请求参数
        data = request.get_json() or {}
        conversation_id = data.get('conversation_id')
        
        if not conversation_id:
            return jsonify({
                'success': False,
                'message': '缺少对话ID参数'
            }), 400
        
        # 切换对话
        success = history_manager.switch_conversation(conversation_id, user_data['user_id'])
        
        if success:
            # 同步更新分析器的表列表
            api_key = user_data.get('api_key')
            if api_key:
                try:
                    analyzer = get_user_analyzer(user_data, api_key)
                    # 重新扫描数据库中的表，更新分析器的表列表
                    analyzer._sync_tables_from_database()
                except:
                    pass  # 如果同步失败，不影响切换对话
            
            current_conversation = history_manager.get_current_conversation_info()
            return jsonify({
                'success': True,
                'message': '对话切换成功',
                'current_conversation': current_conversation
            })
        else:
            return jsonify({
                'success': False,
                'message': '对话切换失败：对话不存在或无权限'
            }), 404
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'切换对话失败: {str(e)}'
        }), 500

@app.route('/api/conversations/current', methods=['GET'])
@allow_default_user
def get_current_conversation(user_data):
    try:
        history_manager = get_user_history_manager(user_data)
        
        current_conversation = history_manager.get_current_conversation_info()
        
        return jsonify({
            'success': True,
            'current_conversation': current_conversation
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取当前对话失败: {str(e)}'
        }), 500

# 对话历史记录相关API
@app.route('/api/conversations', methods=['GET'])
@allow_default_user
def get_conversations(user_data):
    try:
        history_manager = get_user_history_manager(user_data)
        
        # 获取查询参数
        limit = int(request.args.get('limit', 10))
        offset = int(request.args.get('offset', 0))
        
        conversations = history_manager.get_conversation_history(
            user_data['user_id'], limit, offset
        )
        
        # 获取统计信息
        stats = history_manager.get_conversation_stats(user_data['user_id'])
        
        return jsonify({
            'success': True,
            'conversations': conversations,
            'stats': stats,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'total': stats['total_conversations']
            }
        })
        
    except Exception as e:
        print(f"❌ 获取对话历史失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取对话历史失败: {str(e)}'
        }), 500

@app.route('/api/conversations/<conversation_id>', methods=['GET'])
@allow_default_user
def get_conversation_detail(user_data, conversation_id):
    try:
        history_manager = get_user_history_manager(user_data)
        
        conversation = history_manager.get_conversation_detail(conversation_id)
        
        if not conversation:
            return jsonify({
                'success': False,
                'message': '对话记录不存在'
            }), 404
        
        # 验证用户权限
        if conversation['user_id'] != user_data['user_id']:
            return jsonify({
                'success': False,
                'message': '无权限访问此对话记录'
            }), 403
        
        return jsonify({
            'success': True,
            'conversation': conversation
        })
        
    except Exception as e:
        print(f"❌ 获取对话详情失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取对话详情失败: {str(e)}'
        }), 500

@app.route('/api/conversations/<conversation_id>', methods=['DELETE'])
@allow_default_user
def delete_conversation(user_data, conversation_id):
    try:
        history_manager = get_user_history_manager(user_data)
        
        success = history_manager.delete_conversation(conversation_id, user_data['user_id'])
        
        if success:
            return jsonify({
                'success': True,
                'message': '对话记录已删除'
            })
        else:
            return jsonify({
                'success': False,
                'message': '删除失败：记录不存在或无权限'
            }), 404
        
    except Exception as e:
        print(f"❌ 删除对话记录失败: {e}")
        return jsonify({
            'success': False,
            'message': f'删除对话记录失败: {str(e)}'
        }), 500

@app.route('/api/conversations/recent', methods=['GET'])
@allow_default_user
def get_recent_conversations(user_data):
    try:
        history_manager = get_user_history_manager(user_data)
        
        limit = int(request.args.get('limit', 5))
        conversations = history_manager.get_recent_conversations(user_data['user_id'], limit)
        
        return jsonify({
            'success': True,
            'conversations': conversations
        })
        
    except Exception as e:
        print(f"❌ 获取最近对话失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取最近对话失败: {str(e)}'
        }), 500

@app.route('/api/conversations/stats', methods=['GET'])
@allow_default_user
def get_conversation_stats(user_data):
    try:
        history_manager = get_user_history_manager(user_data)
        
        stats = history_manager.get_conversation_stats(user_data['user_id'])
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        print(f"❌ 获取对话统计失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取对话统计失败: {str(e)}'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    health_data = {
        "status": "healthy",
        "service": "智能数据库分析系统",
        "version": "3.4.0",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "CSV数据导入",
            "流式AI分析",
            "对话历史记录",
            "多用户支持"
        ]
    }
    
    # 检查是否是JSONP请求
    callback = request.args.get('callback', False)
    if callback:
        jsonp_response = f"{callback}({json.dumps(health_data)});"
        return Response(jsonp_response, mimetype="application/javascript")
    else:
        return jsonify(health_data)

@app.route('/api/conversations/<conversation_id>/messages/<message_id>/edit', methods=['POST'])
@allow_default_user
def edit_message(user_data, conversation_id, message_id):
    try:
        history_manager = get_user_history_manager(user_data)
        data = request.get_json() or {}
        new_content = data.get('new_content')
        if not new_content:
            return jsonify({'success': False, 'message': '缺少新内容'}), 400
        result = history_manager.edit_message(conversation_id, message_id, new_content)
        if result:
            return jsonify({'success': True, 'message': '消息编辑成功'})
        else:
            return jsonify({'success': False, 'message': '消息编辑失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'消息编辑异常: {str(e)}'}), 500

@app.route('/api/conversations/<conversation_id>/messages/<message_id>/delete', methods=['POST'])
@allow_default_user
def delete_message(user_data, conversation_id, message_id):
    try:
        history_manager = get_user_history_manager(user_data)
        result = history_manager.delete_message(conversation_id, message_id)
        if result:
            return jsonify({'success': True, 'message': '消息删除成功'})
        else:
            return jsonify({'success': False, 'message': '消息删除失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'消息删除异常: {str(e)}'}), 500

# 模板管理相关API
@app.route('/api/templates/generate', methods=['POST'])
@allow_default_user
def generate_template(user_data):
    """从现有的 HTML 报告生成 Vue 模板"""
    try:
        api_key = user_data.get('api_key')
        if not api_key:
            return jsonify({"success": False, "message": "未提供API密钥"}), 400
            
        data = request.get_json() or {}
        html_content = data.get('html_content')
        conversation_context = data.get('conversation_context', '')
        source_conversation_id = data.get('conversation_id')
        
        if not html_content:
            return jsonify({"success": False, "message": "缺少HTML内容"}), 400
            
        # 获取模板管理器
        template_manager = get_user_template_manager(user_data, api_key)
        
        # 生成模板
        template_data = template_manager.generate_template_from_report(html_content, conversation_context)
        
        # 保存模板
        template_id = template_manager.save_template(template_data, source_conversation_id)
        
        return jsonify({
            "success": True,
            "message": "模板生成成功",
            "data": {
                "template_id": template_id,
                "template_data": template_data
            }
        })
        
    except Exception as e:
        print(f"❌ 生成模板失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"生成模板失败: {str(e)}"
        }), 500

@app.route('/api/templates', methods=['GET'])
@allow_default_user
def list_templates(user_data):
    """获取用户的所有模板"""
    try:
        api_key = user_data.get('api_key') # 虽然不需要调用AI，但为了保持一致性
        template_manager = get_user_template_manager(user_data, api_key)
        
        templates = template_manager.list_templates()
        
        return jsonify({
            "success": True,
            "data": templates
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"获取模板列表失败: {str(e)}"
        }), 500

@app.route('/api/templates/<template_id>', methods=['GET'])
@allow_default_user
def get_template(user_data, template_id):
    """获取指定模板详情"""
    try:
        api_key = user_data.get('api_key')
        template_manager = get_user_template_manager(user_data, api_key)
        
        template = template_manager.get_template(template_id)
        
        if template:
            return jsonify({
                "success": True,
                "data": template
            })
        else:
            return jsonify({
                "success": False,
                "message": "模板不存在"
            }), 404
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"获取模板详情失败: {str(e)}"
        }), 500

@app.route('/api/templates/<template_id>', methods=['DELETE'])
@allow_default_user
def delete_template(user_data, template_id):
    """删除模板"""
    try:
        api_key = user_data.get('api_key')
        template_manager = get_user_template_manager(user_data, api_key)
        
        success = template_manager.delete_template(template_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "模板删除成功"
            })
        else:
            return jsonify({
                "success": False,
                "message": "模板删除失败"
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"删除模板失败: {str(e)}"
        }), 500

if __name__ == '__main__':
    try:
        # 静默启动
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        
        print("🚀 启动智能数据库分析系统")
        print("📊 功能: CSV导入 + AI分析 + 历史记录")
        print("🌐 地址: http://localhost:5000")
        
        debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
        app.run(debug=debug_mode, host='0.0.0.0', port=5000, use_reloader=debug_mode)
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
