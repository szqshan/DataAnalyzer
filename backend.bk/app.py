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

# 导入精简版用户管理中间件
from user_middleware import user_manager, require_user, get_current_user

# 导入分析器类
from datatest1_7_5 import DatabaseAnalyzer

# 导入对话历史记录管理器
from conversation_history import ConversationHistoryManager

app = Flask(__name__)

# 禁用Flask默认日志输出
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
app.logger.setLevel(logging.ERROR)

# 配置CORS
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# 配置
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB最大文件大小

# 用户分析器和历史记录管理器实例缓存
user_analyzers = {}
user_history_managers = {}

def get_user_analyzer(user_data):
    """获取或创建用户专属的分析器实例"""
    user_id = user_data['user_id']
    
    if user_id not in user_analyzers:
        # 获取API密钥
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("未找到 ANTHROPIC_API_KEY 环境变量")
        
        # 获取API基础URL
        base_url = os.getenv('ANTHROPIC_BASE_URL')
        
        # 创建分析器
        analyzer = DatabaseAnalyzer(api_key, base_url=base_url)
        
        # 获取用户路径
        user_paths = user_manager.get_user_paths(user_id)
        
        # 设置用户专属路径
        analyzer.current_db_path = str(user_paths['db_path'])
        analyzer.current_table_name = "data_table"  # 简化：固定表名
        
        # 缓存分析器
        user_analyzers[user_id] = analyzer
        
        print(f"✅ 用户 {user_data['username']} 已连接")
    
    return user_analyzers[user_id]

def get_user_history_manager(user_data):
    """获取或创建用户专属的历史记录管理器实例"""
    user_id = user_data['user_id']
    
    if user_id not in user_history_managers:
        # 获取用户路径
        user_paths = user_manager.get_user_paths(user_id)
        
        # 创建历史记录管理器
        history_manager = ConversationHistoryManager(user_paths)
        
        # 缓存管理器
        user_history_managers[user_id] = history_manager
        
        print(f"📚 用户 {user_data['username']} 历史记录管理器已初始化")
    
    return user_history_managers[user_id]

@app.route('/api/status', methods=['GET'])
@require_user
def get_status(user_data):
    """获取系统状态"""
    try:
        analyzer = get_user_analyzer(user_data)
        
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
@require_user
def upload_csv(user_data):
    """上传CSV文件并导入到用户专属数据库"""
    try:
        print(f"📤 用户 {user_data['username']} 正在上传文件...")
        
        analyzer = get_user_analyzer(user_data)
        
        # 检查文件
        if 'file' not in request.files:
            return jsonify({"success": False, "message": "未找到文件"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "message": "未选择文件"}), 400
        
        if not file.filename.lower().endswith('.csv'):
            return jsonify({"success": False, "message": "只支持CSV文件"}), 400
        
        # 获取参数
        table_name = request.form.get('tableName', 'data_table')
        
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
        
        # 导入数据库
        result = analyzer.import_csv_to_sqlite(str(file_path), table_name, user_db_path)
        
        if result["success"]:
            # 清理临时文件
            try:
                os.remove(str(file_path))
            except:
                pass
            
            print(f"✅ 成功导入 {result.get('rows_imported', 0)} 行数据")
            
            return jsonify({
                "success": True,
                "message": result["message"],
                "data": {
                    "rows_imported": result.get("rows_imported", 0),
                    "columns": result.get("columns", []),
                    "table_name": table_name,
                    "db_path": user_db_path,
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

@app.route('/api/analyze-stream', methods=['POST'])
@require_user
def analyze_data_stream(user_data):
    """流式数据分析接口"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({"success": False, "message": "查询内容不能为空"}), 400
        
        print(f"🔍 用户 {user_data['username']} 开始分析: {query}")
        
        analyzer = get_user_analyzer(user_data)
        history_manager = get_user_history_manager(user_data)
        
        if not analyzer.current_db_path:
            return jsonify({"success": False, "message": "请先上传数据文件"}), 400
        
        def generate_stream():
            conversation_id = None
            tool_calls = []
            
            try:
                # 获取历史对话上下文
                recent_conversations = history_manager.get_recent_conversations(user_data['user_id'], 3)
                context_info = ""
                if recent_conversations:
                    context_info = "\n**历史对话上下文：**\n"
                    for i, conv in enumerate(recent_conversations, 1):
                        context_info += f"{i}. 查询: {conv['user_query']}\n"
                        if conv.get('analysis_summary'):
                            context_info += f"   结果摘要: {conv['analysis_summary'][:100]}...\n"
                        context_info += f"   时间: {conv['start_time'][:19]}\n\n"

                # 发送开始分析消息
                start_msg = '🚀 开始智能分析数据...'
                print(f"\n{start_msg}")
                yield f"data: {json.dumps({'type': 'status', 'message': start_msg}, ensure_ascii=False)}\n\n"

                # 构建系统提示词
                system_prompt = f"""你是专业的数据分析师。请根据用户需求智能分析并决定是否需要查询数据库。

**分析流程：**
1. 首先分析用户的具体需求
2. 检查历史对话中是否已有相关信息
3. 判断当前已有的信息是否足够回答用户问题
4. 如果已有信息不足，则调用 get_table_info 获取表结构，然后执行相应的SQL查询
5. 如果已有信息足够，直接基于已有信息进行分析和回答

**重要原则：**
- 优先使用历史对话中的已有信息
- 避免重复查询已知信息
- 只在必要时调用数据库查询工具
- 确保回答准确、完整、有用
- 如果用户询问的是之前分析过的内容，直接引用历史结果

**可用工具：**
- get_table_info: 获取表结构信息
- query_database: 执行SQL查询获取数据

**当前上下文：**
- 用户: {user_data['username']}
- 数据库: {analyzer.current_db_path}
- 表名: {analyzer.current_table_name}

{context_info}
**当前用户需求:** {query}

请根据以上原则和历史上下文，智能判断是否需要查询数据库，然后提供专业的分析回答。如果历史对话中已有相关信息，请优先使用并适当引用。"""

                # 开始记录对话历史
                conversation_id = history_manager.start_conversation(
                    user_data, query, system_prompt, 
                    analyzer.current_db_path, analyzer.current_table_name
                )

                # 初始化消息历史
                messages = [{"role": "user", "content": system_prompt}]
                
                max_iterations = 100
                iteration = 0
                
                while iteration < max_iterations:
                    iteration += 1
                    has_tool_calls = False
                    
                    status_msg = f'🔄 第{iteration}轮分析...'
                    print(f"\n{status_msg}")
                    yield f"data: {json.dumps({'type': 'status', 'message': status_msg}, ensure_ascii=False)}\n\n"
                    
                    try:
                        # 核心流式API调用
                        response = analyzer.client.messages.create(
                            model=analyzer.model_name,
                            max_tokens=40000,
                            messages=messages,
                            tools=analyzer.tools,
                            stream=True
                        )
                        
                        # 流式响应处理核心逻辑
                        assistant_message = {"role": "assistant", "content": []}
                        current_tool_inputs = {}
                        
                        # 逐块处理流式数据
                        for chunk in response:
                            if chunk.type == "message_start":
                                continue
                                
                            elif chunk.type == "content_block_start":
                                if chunk.content_block.type == "text":
                                    assistant_message["content"].append({"type": "text", "text": ""})
                                elif chunk.content_block.type == "tool_use":
                                    tool_block = {
                                        "type": "tool_use",
                                        "id": chunk.content_block.id,
                                        "name": chunk.content_block.name,
                                        "input": {}
                                    }
                                    assistant_message["content"].append(tool_block)
                                    current_tool_inputs[chunk.content_block.id] = ""
                                    has_tool_calls = True
                                    
                                    tool_msg = f'🔧 调用工具: {chunk.content_block.name}'
                                    print(f"\n{tool_msg}")
                                    yield f"data: {json.dumps({'type': 'status', 'message': tool_msg}, ensure_ascii=False)}\n\n"
                            
                            elif chunk.type == "content_block_delta":
                                if chunk.delta.type == "text_delta":
                                    text_content = chunk.delta.text
                                    if assistant_message["content"] and assistant_message["content"][-1].get("type") == "text":
                                        assistant_message["content"][-1]["text"] += text_content
                                    
                                    print(text_content, end='', flush=True)
                                    yield f"data: {json.dumps({'type': 'ai_response', 'content': text_content}, ensure_ascii=False)}\n\n"
                                    
                                elif chunk.delta.type == "input_json_delta":
                                    if assistant_message["content"] and assistant_message["content"][-1].get("type") == "tool_use":
                                        tool_id = assistant_message["content"][-1]["id"]
                                        if tool_id in current_tool_inputs:
                                            current_tool_inputs[tool_id] += chunk.delta.partial_json
                            
                            elif chunk.type == "content_block_stop":
                                if assistant_message["content"] and assistant_message["content"][-1].get("type") == "tool_use":
                                    tool_id = assistant_message["content"][-1]["id"]
                                    if tool_id in current_tool_inputs:
                                        try:
                                            complete_input = json.loads(current_tool_inputs[tool_id])
                                            assistant_message["content"][-1]["input"] = complete_input
                                        except json.JSONDecodeError:
                                            assistant_message["content"][-1]["input"] = {}
                            
                            elif chunk.type == "message_stop":
                                print()
                                break
                        
                        # 添加助手消息到历史
                        messages.append(assistant_message)
                        
                        # 更新对话消息历史
                        if conversation_id:
                            history_manager.update_conversation_messages(conversation_id, messages)
                        
                        # 执行工具调用
                        if has_tool_calls:
                            tool_results = []
                            
                            for content_block in assistant_message["content"]:
                                if content_block.get("type") == "tool_use":
                                    tool_name = content_block["name"]
                                    tool_input = content_block["input"]
                                    tool_id = content_block["id"]
                                    
                                    try:
                                        result = analyzer.execute_tool(tool_name, tool_input)
                                        
                                        # 记录工具调用
                                        tool_call_record = {
                                            "tool_name": tool_name,
                                            "tool_input": tool_input,
                                            "tool_result": result,
                                            "execution_time": datetime.now().isoformat()
                                        }
                                        tool_calls.append(tool_call_record)
                                        
                                        tool_results.append({
                                            "type": "tool_result",
                                            "tool_use_id": tool_id,
                                            "content": json.dumps(result, ensure_ascii=False, indent=2)
                                        })
                                        
                                        complete_msg = f'✅ 工具 {tool_name} 执行完成'
                                        print(f"\n{complete_msg}")
                                        yield f"data: {json.dumps({'type': 'status', 'message': complete_msg}, ensure_ascii=False)}\n\n"
                                        yield f"data: {json.dumps({'type': 'tool_result', 'tool': tool_name, 'result': result}, ensure_ascii=False)}\n\n"
                                        
                                    except Exception as tool_error:
                                        error_msg = f'工具执行失败: {str(tool_error)}'
                                        print(f"\n❌ {error_msg}")
                                        yield f"data: {json.dumps({'type': 'error', 'message': error_msg}, ensure_ascii=False)}\n\n"
                            
                            if tool_results:
                                messages.append({
                                    "role": "user",
                                    "content": tool_results
                                })
                            
                            # 更新工具调用记录
                            if conversation_id and tool_calls:
                                history_manager.update_tool_calls(conversation_id, tool_calls)
                            
                            continue
                        else:
                            # 分析完成
                            complete_msg = '✅ 分析完成！'
                            print(f"\n{complete_msg}")
                            
                            # 完成对话记录
                            if conversation_id:
                                # 提取分析摘要（从AI响应中获取最后一段文本）
                                analysis_summary = ""
                                if assistant_message["content"]:
                                    for content in assistant_message["content"]:
                                        if content.get("type") == "text" and content.get("text"):
                                            analysis_summary = content["text"][-200:]  # 取最后200字符作为摘要
                                            break
                                
                                history_manager.complete_conversation(
                                    conversation_id, 'completed', analysis_summary, iteration
                                )
                            
                            yield f"data: {json.dumps({'type': 'status', 'message': complete_msg}, ensure_ascii=False)}\n\n"
                            break
                            
                    except Exception as api_error:
                        error_msg = f'API调用错误: {str(api_error)}'
                        print(f"\n❌ {error_msg}")
                        yield f"data: {json.dumps({'type': 'error', 'message': error_msg}, ensure_ascii=False)}\n\n"
                        
                        # 记录错误状态
                        if conversation_id:
                            history_manager.complete_conversation(conversation_id, 'error', error_msg, iteration)
                        break
                
                if iteration >= max_iterations:
                    error_msg = '达到最大迭代次数限制'
                    print(f"\n❌ {error_msg}")
                    yield f"data: {json.dumps({'type': 'error', 'message': error_msg}, ensure_ascii=False)}\n\n"
                    
                    # 记录中断状态
                    if conversation_id:
                        history_manager.complete_conversation(conversation_id, 'interrupted', error_msg, iteration)
                
            except Exception as e:
                error_msg = f'分析过程错误: {str(e)}'
                print(f"\n❌ {error_msg}")
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg}, ensure_ascii=False)}\n\n"
                
                # 记录错误状态
                if conversation_id:
                    history_manager.complete_conversation(conversation_id, 'error', error_msg, 0)
        
        return Response(
            stream_with_context(generate_stream()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Cache-Control, Content-Type, X-User-ID, X-Username',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            }
        )
        
    except Exception as e:
        print(f"❌ 分析请求失败: {e}")
        return jsonify({
            "success": False,
            "message": f"处理分析请求失败: {str(e)}"
        }), 500

# 对话历史记录相关API
@app.route('/api/conversations', methods=['GET'])
@require_user
def get_conversations(user_data):
    """获取用户对话历史列表"""
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
@require_user
def get_conversation_detail(user_data, conversation_id):
    """获取对话详情"""
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
@require_user
def delete_conversation(user_data, conversation_id):
    """删除对话记录"""
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
@require_user
def get_recent_conversations(user_data):
    """获取最近的对话记录（用于上下文）"""
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
@require_user
def get_conversation_stats(user_data):
    """获取对话统计信息"""
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

if __name__ == '__main__':
    try:
        # 静默启动
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        
        print("🚀 启动智能数据库分析系统")
        print("📊 功能: CSV导入 + AI分析 + 历史记录")
        print("🌐 地址: http://localhost:5000")
        
        app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")