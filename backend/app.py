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

# 🆕 导入简化版对话记录管理器
from conversation_manager import ConversationManager

app = Flask(__name__)

# 禁用Flask默认日志输出
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
app.logger.setLevel(logging.ERROR)

# 配置CORS
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# 配置
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB最大文件大小

# 用户分析器和对话管理器实例缓存
user_analyzers = {}
user_conversation_managers = {}

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
        if user_paths['db_path'].exists():
            analyzer.current_db_path = str(user_paths['db_path'])
            analyzer.current_table_name = "data_table"  # 简化：固定表名
        
        # 缓存分析器
        user_analyzers[user_id] = analyzer
        
        print(f"✅ 用户 {user_data['username']} 已连接")
    
    return user_analyzers[user_id]

def get_user_conversation_manager(user_data):
    """获取或创建用户专属的对话管理器实例"""
    user_id = user_data['user_id']
    
    if user_id not in user_conversation_managers:
        # 获取用户路径
        user_paths = user_manager.get_user_paths(user_id)
        
        # 创建对话管理器
        conversation_manager = ConversationManager(user_paths)
        
        # 缓存管理器
        user_conversation_managers[user_id] = conversation_manager
        
        print(f"📚 用户 {user_data['username']} HTML管理器已初始化")
    
    return user_conversation_managers[user_id]

@app.route('/api/status', methods=['GET'])
@require_user
def get_status(user_data):
    """获取系统状态"""
    try:
        analyzer = get_user_analyzer(user_data)
        conversation_manager = get_user_conversation_manager(user_data)
        
        # 获取记录数
        record_count = 0
        if analyzer.current_db_path and analyzer.current_table_name:
            try:
                result = analyzer.query_database(f"SELECT COUNT(*) FROM {analyzer.current_table_name}")
                if "data" in result and result["data"]:
                    record_count = result["data"][0][0]
            except:
                pass
        
        # 获取简化的状态摘要
        conversation_summary = conversation_manager.get_conversation_summary()
        
        status = {
            "system_ready": True,
            "database_connected": analyzer.current_db_path is not None,
            "database_path": analyzer.current_db_path or "",
            "table_name": analyzer.current_table_name or "",
            "record_count": record_count,
            "api_status": "connected",
            "user_info": user_data,
            "conversation_info": conversation_summary
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
            
            print(f"✅ 成功导入 {result['rows_imported']} 行数据")
            
            return jsonify({
                "success": True,
                "message": result["message"],
                "data": {
                    "rows_imported": result["rows_imported"],
                    "columns": result["columns"],
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
    """执行智能数据分析 - 简化版，专注HTML报告保存"""
    try:
        print(f"🔍 用户 {user_data['username']} 开始分析")
        
        analyzer = get_user_analyzer(user_data)
        conversation_manager = get_user_conversation_manager(user_data)
        
        if not analyzer.current_db_path:
            return jsonify({"success": False, "message": "请先上传数据"}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "请求数据为空"}), 400
            
        query = data.get('query', '').strip()
        if not query:
            return jsonify({"success": False, "message": "分析需求不能为空"}), 400
        
        # 开始新的对话记录
        conversation_id = conversation_manager.start_new_conversation(query, user_data)
        
        def generate_stream():
            """生成流式分析数据 - 简化版"""
            try:
                # 发送开始分析消息
                start_msg = '🚀 开始分析数据...'
                print(f"\n{start_msg}")
                yield f"data: {json.dumps({'type': 'status', 'message': start_msg}, ensure_ascii=False)}\n\n"
                
                # 构建系统提示词
                system_prompt = f"""你是专业的数据分析师。请按以下步骤进行分析：

1. 首先调用 get_table_info 获取表结构
2. 然后根据用户需求执行相应的SQL查询，注意SQL语句必须是统计类的命令，禁止输出过多内容，消耗过多的token
3. 最后基于查询结果生成详细的HTML格式的分析报告

当前用户: {user_data['username']}
数据库: {analyzer.current_db_path}
表名: {analyzer.current_table_name}

用户需求: {query}"""

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
                        ai_response_content = ""  # 🔥 收集完整AI响应
                        
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
                                    
                                    # 🔥 关键：收集完整AI响应用于HTML提取
                                    ai_response_content += text_content
                                    conversation_manager.add_ai_response_chunk(text_content, 'text')
                                    
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
                            
                            continue
                        else:
                            # 🔥 修复：分析完成后的HTML处理
                            complete_msg = '✅ 分析完成！'
                            print(f"\n{complete_msg}")
                            
                            # 🔥 关键：完成对话并提取保存HTML
                            completed_conversation = conversation_manager.complete_conversation('completed')
                            
                            # 🔥 发送HTML准备就绪信号
                            if completed_conversation and completed_conversation.get('html_report_path'):
                                html_file_path = completed_conversation['html_report_path']
                                yield f"data: {json.dumps({'type': 'html_ready', 'file_path': html_file_path}, ensure_ascii=False)}\n\n"
                                print(f"📊 HTML报告路径已发送给前端: {html_file_path}")
                            
                            yield f"data: {json.dumps({'type': 'status', 'message': complete_msg}, ensure_ascii=False)}\n\n"
                            break
                            
                    except Exception as api_error:
                        error_msg = f'API调用错误: {str(api_error)}'
                        print(f"\n❌ {error_msg}")
                        yield f"data: {json.dumps({'type': 'error', 'message': error_msg}, ensure_ascii=False)}\n\n"
                        
                        conversation_manager.complete_conversation('error')
                        break
                
                if iteration >= max_iterations:
                    error_msg = '达到最大迭代次数限制'
                    print(f"\n❌ {error_msg}")
                    yield f"data: {json.dumps({'type': 'error', 'message': error_msg}, ensure_ascii=False)}\n\n"
                    
                    conversation_manager.complete_conversation('interrupted')
                
            except Exception as e:
                error_msg = f'分析过程错误: {str(e)}'
                print(f"\n❌ {error_msg}")
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg}, ensure_ascii=False)}\n\n"
                
                try:
                    conversation_manager.complete_conversation('error')
                except:
                    pass
        
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

# 🔥 简化：获取最新HTML报告的API
@app.route('/api/latest-report', methods=['GET'])
@require_user
def get_latest_report(user_data):
    """获取最新的HTML分析报告 - 简化版"""
    try:
        conversation_manager = get_user_conversation_manager(user_data)
        user_paths = user_manager.get_user_paths(user_data['user_id'])
        
        # 检查最新报告文件
        latest_report_path = user_paths['reports_dir'] / 'latest_analysis_report.html'
        
        if latest_report_path.exists():
            # 直接读取文件内容
            with open(latest_report_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 验证HTML内容完整性
            if len(html_content) > 500 and '<!DOCTYPE html>' in html_content and '</html>' in html_content:
                return jsonify({
                    'success': True,
                    'html_content': html_content,
                    'file_path': str(latest_report_path),
                    'last_modified': datetime.fromtimestamp(latest_report_path.stat().st_mtime).isoformat(),
                    'file_size': len(html_content)
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'HTML报告文件已损坏或不完整'
                }), 500
        else:
            return jsonify({
                'success': False,
                'message': '没有找到HTML报告'
            }), 404
        
    except Exception as e:
        print(f"❌ 获取HTML报告失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取HTML报告失败: {str(e)}'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    health_data = {
        "status": "healthy",
        "service": "智能数据库分析系统 (简化版 - 专注HTML报告)",
        "version": "3.2.0",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "CSV数据导入",
            "流式AI分析",
            "HTML报告生成",
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
        
        print("🚀 启动智能数据库分析系统 (简化版)")
        print("📊 专注功能: CSV导入 + AI分析 + HTML报告保存")
        print("🌐 地址: http://localhost:5000")
        
        app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")