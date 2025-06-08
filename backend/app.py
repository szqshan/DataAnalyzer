# 修改 backend/app.py - 添加多用户支持

from flask import Flask, request, jsonify, send_file, Response, stream_with_context
from flask_cors import CORS
import os
import json
import traceback
from werkzeug.utils import secure_filename
import tempfile
from datetime import datetime
import time
import pandas as pd
import sqlite3
import uuid
import sys
from pathlib import Path

# 导入用户管理中间件
from user_middleware import user_manager, require_user, get_current_user

# 导入分析器类
from datatest1_7_5 import DatabaseAnalyzer, ConversationMemory

app = Flask(__name__)

# 配置CORS，允许跨域请求，包括file://协议
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# 配置
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB最大文件大小

# 用户分析器实例缓存
user_analyzers = {}

def get_user_analyzer(user_data):
    """获取或创建用户专属的分析器实例"""
    user_id = user_data['user_id']
    
    if user_id not in user_analyzers:
        # 获取API密钥
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("未找到 ANTHROPIC_API_KEY 环境变量")
        
        # 获取API基础URL（如果设置了的话）
        base_url = os.getenv('ANTHROPIC_BASE_URL')
        
        # 调试输出
        print(f"🔍 从环境变量读取到的 ANTHROPIC_BASE_URL: {base_url}")
        
        # 创建分析器
        analyzer = DatabaseAnalyzer(api_key, base_url=base_url)
        
        # 获取用户路径
        user_paths = user_manager.get_user_paths(user_id)
        
        # 设置用户专属路径
        if user_paths['db_path'].exists():
            analyzer.current_db_path = str(user_paths['db_path'])
            # 这里简化处理，假设表名为data_table
            analyzer.current_table_name = "data_table"
        
        # 设置用户专属记忆
        analyzer.memory = ConversationMemory(str(user_paths['memory_path']))
        
        # 缓存分析器
        user_analyzers[user_id] = analyzer
        
        print(f"✅ 为用户 {user_data['username']} ({user_id}) 创建了专属分析器")
    
    return user_analyzers[user_id]

# 新增：用户状态接口
@app.route('/api/user/status', methods=['GET'])
@require_user
def get_user_status(user_data):
    """获取用户状态信息"""
    try:
        user_stats = user_manager.get_user_stats(user_data['user_id'])
        user_paths = user_manager.get_user_paths(user_data['user_id'])
        
        return jsonify({
            "success": True,
            "user_info": user_data,
            "user_stats": user_stats,
            "paths": {
                "database": str(user_paths['db_path']) if user_paths['db_path'].exists() else None,
                "memory": str(user_paths['memory_path']) if user_paths['memory_path'].exists() else None,
                "reports_dir": str(user_paths['reports_dir'])
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"获取用户状态失败: {str(e)}"
        }), 500

@app.route('/api/status', methods=['GET'])
@require_user
def get_status(user_data):
    """获取系统状态 - 多用户版本"""
    try:
        analyzer = get_user_analyzer(user_data)
        memory_summary = analyzer.memory.get_memory_summary()
        
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
            "memory_stats": memory_summary,
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
        print(f"📤 接收到文件上传请求 - 用户: {user_data['username']} ({user_data['user_id']})")
        print(f"📋 请求头: {dict(request.headers)}")
        
        analyzer = get_user_analyzer(user_data)
        
        # 检查文件
        if 'file' not in request.files:
            print(f"❌ 用户 {user_data['username']} 上传失败: 未找到文件")
            print(f"📋 请求表单数据: {list(request.form.keys())}")
            print(f"📋 请求文件数据: {list(request.files.keys())}")
            return jsonify({"success": False, "message": "未找到文件"}), 400
        
        file = request.files['file']
        if file.filename == '':
            print(f"❌ 用户 {user_data['username']} 上传失败: 未选择文件")
            return jsonify({"success": False, "message": "未选择文件"}), 400
        
        if not file.filename.lower().endswith('.csv'):
            print(f"❌ 用户 {user_data['username']} 上传失败: 文件类型不支持 - {file.filename}")
            return jsonify({"success": False, "message": "只支持CSV文件"}), 400
        
        # 获取参数
        table_name = request.form.get('tableName', 'data_table')
        
        # 获取用户路径
        user_paths = user_manager.get_user_paths(user_data['user_id'])
        user_db_path = str(user_paths['db_path'])
        user_uploads_dir = user_paths['uploads_dir']
        
        print(f"📋 用户上传信息 - 文件: {file.filename}, 表名: {table_name}, 数据库: {user_db_path}")
        
        # 确保上传目录存在
        if not os.path.exists(user_uploads_dir):
            try:
                os.makedirs(user_uploads_dir)
                print(f"📁 创建用户上传目录: {user_uploads_dir}")
            except Exception as e:
                print(f"❌ 无法创建上传目录: {e}")
                return jsonify({
                    "success": False,
                    "message": f"服务器错误: 无法创建上传目录",
                    "error": str(e)
                }), 500
        
        # 保存文件到用户专属目录
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{filename}"
        file_path = user_uploads_dir / safe_filename
        
        try:
            print(f"📁 开始保存文件: {file_path}")
            file.save(str(file_path))
            file_size = os.path.getsize(str(file_path))
            print(f"📁 用户 {user_data['username']} 文件已保存: {file_path} (大小: {file_size} 字节)")
            
            # 验证文件是否真的保存成功
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件保存后无法找到: {file_path}")
                
            if file_size == 0:
                raise ValueError(f"文件保存成功但大小为0: {file_path}")
                
        except Exception as save_error:
            print(f"❌ 保存文件失败: {save_error}")
            print(f"📋 错误详情: {traceback.format_exc()}")
            return jsonify({
                "success": False,
                "message": f"保存文件失败: {str(save_error)}",
                "user_info": user_data
            }), 500
        
        # 导入数据库
        try:
            print(f"📊 开始导入CSV到SQLite - 文件: {file_path}")
            result = analyzer.import_csv_to_sqlite(str(file_path), table_name, user_db_path)
            
            if result["success"]:
                # 清理临时文件
                try:
                    os.remove(str(file_path))
                    print(f"🗑️ 临时文件已删除: {file_path}")
                except Exception as e:
                    print(f"⚠️ 无法删除临时文件: {e}")
                
                print(f"✅ 用户 {user_data['username']} 成功导入 {result['rows_imported']} 行数据")
                
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
                print(f"❌ 导入失败: {result.get('message', '未知错误')}")
                return jsonify(result), 400
                
        except Exception as import_error:
            print(f"❌ 导入数据库失败: {import_error}")
            print(f"📋 错误详情: {traceback.format_exc()}")
            return jsonify({
                "success": False,
                "message": f"导入数据库失败: {str(import_error)}",
                "error_details": traceback.format_exc(),
                "user_info": user_data
            }), 500
            
    except Exception as e:
        print(f"❌ 上传处理异常: {e}")
        print(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"上传失败: {str(e)}",
            "error_details": traceback.format_exc(),
            "user_info": user_data
        }), 500

# 传统分析接口（保持兼容性）
@app.route('/api/analyze', methods=['POST'])
@require_user
def analyze_data(user_data):
    """执行智能数据分析 - 非流式版本（多用户）"""
    try:
        analyzer = get_user_analyzer(user_data)
        
        if not analyzer.current_db_path:
            return jsonify({"success": False, "message": "请先上传数据"}), 400
        
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({"success": False, "message": "分析需求不能为空"}), 400
        
        print(f"🔍 用户 {user_data['username']} 开始分析: {query}")
        
        # 执行分析
        result = analyzer.analyze_with_llm(query)
        
        # 获取最新的记忆信息
        memory_summary = analyzer.memory.get_memory_summary()
        
        return jsonify({
            "success": True,
            "result": result,
            "analysis_id": memory_summary.get("conversation_count", 0),
            "memory_stats": memory_summary,
            "user_info": user_data
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"分析失败: {str(e)}",
            "error_details": traceback.format_exc(),
            "user_info": user_data
        }), 500

@app.route('/api/analyze-stream', methods=['POST'])
@require_user
def analyze_data_stream(user_data):
    """执行智能数据分析 - 流式输出版本（多用户）"""
    try:
        analyzer = get_user_analyzer(user_data)
        
        if not analyzer.current_db_path:
            return jsonify({"success": False, "message": "请先上传数据"}), 400
        
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({"success": False, "message": "分析需求不能为空"}), 400
        
        # 调试函数：打印模型响应内容
        def debug_print_chunk(chunk):
            """打印模型响应块的详细内容"""
            try:
                print("\n=== 模型响应块 ===")
                print(f"类型: {chunk.type}")
                
                if hasattr(chunk, 'delta'):
                    print(f"Delta类型: {chunk.delta.type}")
                    
                    if chunk.delta.type == "tool_use":
                        if hasattr(chunk.delta.tool_use, 'name'):
                            print(f"工具名称: {chunk.delta.tool_use.name}")
                        if hasattr(chunk.delta.tool_use, 'input'):
                            print(f"工具输入: {chunk.delta.tool_use.input}")
                    elif chunk.delta.type == "text_delta":
                        print(f"文本内容: {chunk.delta.text[:50]}...")
                
                print("===================")
            except Exception as e:
                print(f"调试打印错误: {e}")
        
        # 检测浏览器类型
        user_agent = request.headers.get('User-Agent', '')
        is_edge = 'Edg/' in user_agent
        if is_edge:
            print(f"⚠️ 检测到Edge浏览器请求 - 用户: {user_data['username']}")
            print(f"📋 User-Agent: {user_agent}")
        
        # 设置响应头，确保兼容性
        response_headers = {
            'Content-Type': 'text/event-stream; charset=utf-8',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',  # 禁用Nginx缓冲
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Cache-Control, Content-Type',
            'Access-Control-Allow-Methods': 'POST, OPTIONS'
        }
        
        @stream_with_context
        def generate_analysis_stream():
            """生成流式分析数据"""
            try:
                # 记录是否为Edge浏览器
                is_edge = user_agent and 'Edg/' in user_agent
                if is_edge:
                    app.logger.warning(f"Edge浏览器请求 - 用户: {user_data['username']}, UA: {user_agent[:50]}")
                
                # 初始化变量
                full_ai_response = ""
                tool_results = []
                sql_count = 0  # SQL查询计数器
                messages = []
                
                # 添加用户消息到历史
                messages.append({"role": "user", "content": query})
                
                # 发送开始分析消息
                start_msg = {
                    'type': 'status',
                    'message': '🚀 开始分析...'
                }
                yield f"data: {json.dumps(start_msg)}\n\n"
                
                # 发送系统状态
                status_msg = {'type': 'status', 'message': '📊 检查数据库连接...'}
                yield f"data: {json.dumps(status_msg)}\n\n"
                time.sleep(0.2)
                
                db_status_msg = {
                    'type': 'status', 
                    'message': f"✅ 数据库已连接: {analyzer.current_table_name}"
                }
                yield f"data: {json.dumps(db_status_msg)}\n\n"
                time.sleep(0.2)
                
                # 开始分析过程
                engine_msg = {'type': 'status', 'message': '🔧 启动智能分析引擎...'}
                yield f"data: {json.dumps(engine_msg)}\n\n"
                time.sleep(0.2)
                
                # 获取相关的历史上下文
                conversation_context = analyzer.memory.get_relevant_context(query)
                if conversation_context:
                    memory_msg = {'type': 'status', 'message': '🧠 加载历史分析记录...'}
                    yield f"data: {json.dumps(memory_msg)}\n\n"
                    time.sleep(0.2)
                
                # 构建系统提示词
                system_prompt = f"""你是专业数据分析师，负责生成数据分析报告。

**必须严格按照以下步骤执行分析**：
1. 首先，调用 get_table_info 工具获取表结构（无需参数）
2. 然后，使用 query_database 工具执行SQL查询（参数格式：{{"sql": "SELECT * FROM table"}}）
3. 根据查询结果进行分析并生成报告

不要跳过任何步骤，必须使用工具获取数据，不要猜测数据内容。每次只能执行一个工具调用，等待结果后再进行下一步。

                当前用户: {user_data['username']} (ID: {user_data['user_id']})
                
                {conversation_context}

                数据库信息：
                - 路径: {analyzer.current_db_path}
                - 表名: {analyzer.current_table_name}

                🔧 可用工具：
                1. get_table_info: 获取表结构 (无需参数)
                2. query_database: 执行SQL查询 (参数: {{"sql": "你的SQL语句"}})

                请基于用户需求进行数据分析并生成简洁明了的分析报告。记住，你必须使用工具来获取数据，不要猜测或假设数据内容。"""

                # 初始消息
                messages = [
                    {"role": "user", "content": f"{system_prompt}\n\n用户需求: {query}"}
                ]
                
                # 根据用户查询判断分析深度
                query_lower = query.lower()
                if any(keyword in query_lower for keyword in ['简单', '基础', '概览', '快速']):
                    max_iterations = 15
                    analysis_type = "简单分析"
                elif any(keyword in query_lower for keyword in ['深度', '详细', '全面', '完整']):
                    max_iterations = 30
                    analysis_type = "深度分析"
                else:
                    max_iterations = 20
                    analysis_type = "标准分析"
                
                type_msg = {
                    'type': 'status', 
                    'message': f"🎯 分析类型: {analysis_type}"
                }
                yield f"data: {json.dumps(type_msg)}\n\n"
                
                iteration = 0
                full_ai_response = ""
                tool_results = []
                
                while iteration < max_iterations:
                    iteration += 1
                    
                    try:
                        # 调用Claude API (流式输出)
                        response = analyzer.client.messages.create(
                            model=analyzer.model_name,
                            max_tokens=40000,
                            messages=messages,
                            tools=analyzer.tools,
                            stream=True
                        )
                        
                        # 处理流式响应
                        current_tool_call = None
                        current_tool_input = {}
                        
                        # 用于构建完整的助手响应
                        assistant_message = {"role": "assistant", "content": []}
                        
                        print(f"\n🔍 开始处理模型响应流...")
                        
                        for chunk in response:
                            # 调试输出
                            if hasattr(chunk, 'type'):
                                print(f"块类型: {chunk.type}", end=" | ", flush=True)
                                
                                # 详细调试
                                debug_print_chunk(chunk)
                            
                            # 处理工具调用开始
                            if chunk.type == "content_block_start" and hasattr(chunk, 'content_block') and chunk.content_block.type == "tool_use":
                                print(f"工具调用开始: {chunk.content_block.name}", flush=True)
                                current_tool_call = chunk.content_block.name
                                current_tool_input = {}
                                
                                # 添加新的工具调用到助手消息
                                tool_block = {
                                    "type": "tool_use",
                                    "name": current_tool_call,
                                    "input": {}
                                }
                                assistant_message["content"].append(tool_block)
                                
                                tool_msg = {
                                    'type': 'status',
                                    'message': f"🔧 执行工具: {current_tool_call}"
                                }
                                yield f"data: {json.dumps(tool_msg)}\n\n"
                            
                            # 处理工具调用
                            elif chunk.type == "content_block_delta" and chunk.delta.type == "tool_use":
                                print(f"工具调用块: {chunk.delta.tool_use.name if hasattr(chunk.delta.tool_use, 'name') else '未知'}", flush=True)
                                
                                # 处理工具输入参数
                                if "input" in chunk.delta.tool_use and chunk.delta.tool_use.input:
                                    for key, value in chunk.delta.tool_use.input.items():
                                        current_tool_input[key] = value
                                        print(f"工具参数: {key}={value}", flush=True)
                                        
                                    # 更新助手消息中的工具输入
                                    if assistant_message["content"] and assistant_message["content"][-1]["type"] == "tool_use":
                                        assistant_message["content"][-1]["input"] = current_tool_input
                            
                            # 处理JSON输入增量
                            elif chunk.type == "content_block_delta" and chunk.delta.type == "input_json_delta":
                                print(f"JSON输入增量: {chunk.delta.partial_json}", flush=True)
                                
                                # 累积JSON字符串
                                if 'json_accumulator' not in current_tool_input:
                                    current_tool_input['json_accumulator'] = ""
                                
                                current_tool_input['json_accumulator'] += chunk.delta.partial_json
                                
                                # 尝试解析完整的JSON
                                try:
                                    json_str = current_tool_input['json_accumulator']
                                    if json_str.strip() and (json_str.strip().startswith('{') or json_str.strip().startswith('[')):
                                        parsed_json = json.loads(json_str)
                                        print(f"解析JSON成功: {parsed_json}", flush=True)
                                        
                                        # 对于get_table_info工具，不需要参数
                                        if current_tool_call == "get_table_info":
                                            current_tool_input = {}
                                        # 对于query_database工具，需要sql参数
                                        elif current_tool_call == "query_database" and isinstance(parsed_json, dict):
                                            current_tool_input = parsed_json
                                        
                                        # 更新助手消息中的工具输入
                                        if assistant_message["content"] and assistant_message["content"][-1]["type"] == "tool_use":
                                            assistant_message["content"][-1]["input"] = current_tool_input
                                except Exception as json_error:
                                    # 可能是不完整的JSON，继续累积
                                    print(f"JSON解析错误: {json_error}", flush=True)
                            
                            # 处理文本响应
                            elif chunk.type == "content_block_delta" and chunk.delta.type == "text":
                                if chunk.delta.text:
                                    # 累加到完整响应
                                    full_ai_response += chunk.delta.text
                                    
                                    # 如果当前没有文本块，添加一个
                                    if not assistant_message["content"] or assistant_message["content"][-1]["type"] != "text":
                                        assistant_message["content"].append({"type": "text", "text": ""})
                                    
                                    # 更新最后一个文本块
                                    if assistant_message["content"] and assistant_message["content"][-1]["type"] == "text":
                                        assistant_message["content"][-1]["text"] += chunk.delta.text
                                    
                                    # 发送AI响应片段
                                    ai_msg = {
                                        'type': 'ai_response',
                                        'content': chunk.delta.text
                                    }
                                    yield f"data: {json.dumps(ai_msg)}\n\n"
                            
                            # 处理工具调用完成事件
                            elif chunk.type == "content_block_stop":
                                print(f"\n工具调用块结束", flush=True)
                                
                                # 如果有未执行的工具调用，执行它
                                if current_tool_call and current_tool_input:
                                    print(f"执行最终工具调用: {current_tool_call}", flush=True)
                                    
                                    try:
                                        # 如果是get_table_info工具，不需要额外参数
                                        if current_tool_call == "get_table_info" and not current_tool_input:
                                            current_tool_input = {}
                                            print(f"执行get_table_info工具，无需参数", flush=True)
                                        
                                        # 如果是SQL查询，发送SQL状态
                                        if current_tool_call == "query_database" and "sql" in current_tool_input:
                                            sql_query = current_tool_input["sql"]
                                            sql_msg = {
                                                'type': 'status',
                                                'message': f"🔍 执行SQL: {sql_query[:50]}..."
                                            }
                                            yield f"data: {json.dumps(sql_msg)}\n\n"
                                        elif current_tool_call == "get_table_info":
                                            tool_msg = {
                                                'type': 'status',
                                                'message': f"🔍 获取表结构: {analyzer.current_table_name}"
                                            }
                                            yield f"data: {json.dumps(tool_msg)}\n\n"
                                        
                                        result = analyzer.execute_tool(current_tool_call, current_tool_input)
                                        tool_results.append({
                                            "tool_name": current_tool_call,
                                            "input": current_tool_input,
                                            "result": result
                                        })
                                        
                                        print(f"工具执行成功: {current_tool_call}, 结果类型: {type(result)}", flush=True)
                                        
                                        # 发送工具执行结果状态
                                        if current_tool_call == "query_database" and "row_count" in result:
                                            result_msg = {
                                                'type': 'status',
                                                'message': f"✅ SQL查询完成: {result['row_count']}行 ({result.get('execution_time', 0):.3f}秒)"
                                            }
                                            yield f"data: {json.dumps(result_msg)}\n\n"
                                            # 增加SQL查询计数
                                            sql_count += 1
                                        elif current_tool_call == "get_table_info":
                                            table_info = result.get("table_info", {})
                                            columns_count = len(table_info.get("columns", []))
                                            result_msg = {
                                                'type': 'status',
                                                'message': f"✅ 表结构获取完成: {columns_count}列"
                                            }
                                            yield f"data: {json.dumps(result_msg)}\n\n"
                                        
                                        # 添加工具结果到消息流
                                        messages.append({
                                            "role": "user",
                                            "content": [{
                                                "type": "tool_result",
                                                "tool_call_id": len(tool_results),
                                                "content": json.dumps(result)
                                            }]
                                        })
                                        
                                        # 重置当前工具
                                        current_tool_call = None
                                        current_tool_input = {}
                                        
                                    except Exception as tool_error:
                                        print(f"最终工具执行错误: {tool_error}", flush=True)
                                        error_msg = {
                                            'type': 'status',
                                            'message': f"❌ 工具执行错误: {str(tool_error)[:100]}"
                                        }
                                        yield f"data: {json.dumps(error_msg)}\n\n"
                        
                        # 将助手消息添加到消息历史
                        messages.append(assistant_message)
                        
                        # 分析完成，跳出循环
                        break
                        
                    except Exception as api_error:
                        error_msg = {
                            'type': 'error',
                            'message': f"API调用错误: {str(api_error)}"
                        }
                        yield f"data: {json.dumps(error_msg)}\n\n"
                        print(f"❌ API调用错误: {api_error}")
                        break
                
                # 保存记忆
                try:
                    if analyzer.memory:
                        print(f"\n💾 保存记忆 - 工具调用数量: {len(tool_results)}", flush=True)
                        for i, tool in enumerate(tool_results):
                            print(f"  工具 #{i+1}: {tool.get('tool_name')}", flush=True)
                        
                        # 保存完整的上下文，包括用户输入、AI响应和工具调用结果
                        analyzer.memory.save_context(
                            {"input": query, "tools": tool_results}, 
                            full_ai_response,  # 直接传递字符串
                            analysis_metadata={
                                "database": analyzer.current_db_path,
                                "table": analyzer.current_table_name,
                                "analysis_type": analysis_type
                            }
                        )
                        memory_msg = {
                            'type': 'status',
                            'message': f"💾 分析记忆已保存"
                        }
                        yield f"data: {json.dumps(memory_msg)}\n\n"
                        app.logger.info(f"记忆文件已保存: {analyzer.memory.memory_file}")
                except Exception as mem_err:
                    app.logger.warning(f"⚠️ 保存记忆失败: {str(mem_err)}")
                    # 记录详细的错误信息
                    app.logger.error(f"记忆保存错误详情: {traceback.format_exc()}")
                    
                    # 尝试记录导致错误的数据结构
                    try:
                        app.logger.debug(f"用户输入类型: {type(query)}")
                        app.logger.debug(f"工具结果数量: {len(tool_results)}")
                        app.logger.debug(f"AI响应类型: {type(full_ai_response)}")
                        app.logger.debug(f"消息数量: {len(messages)}")
                    except:
                        app.logger.error("无法记录错误数据结构信息")
                    
                    # 向客户端发送错误状态，但不中断流程
                    error_msg = {
                        'type': 'warning',
                        'message': f"⚠️ 记忆保存遇到问题，但分析已完成"
                    }
                    yield f"data: {json.dumps(error_msg)}\n\n"

                # 发送分析完成消息
                complete_msg = {
                    'type': 'status',
                    'message': f"✅ 分析完成 - 🔧 工具调用: {len(tool_results)}次 | 🗃️ SQL查询: {sql_count}次成功"
                }
                yield f"data: {json.dumps(complete_msg)}\n\n"
                
            except Exception as e:
                error_msg = {
                    'type': 'error',
                    'message': f"分析过程错误: {str(e)}"
                }
                yield f"data: {json.dumps(error_msg)}\n\n"
                print(f"❌ 流式分析错误: {e}")
                print(traceback.format_exc())
        
        # 返回流式响应
        return Response(
            generate_analysis_stream(),
            mimetype='text/event-stream',
            headers=response_headers
        )
        
    except Exception as e:
        print(f"❌ 分析请求处理错误: {e}")
        print(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"处理分析请求失败: {str(e)}"
        }), 500

# 添加一个额外的健康检查路由，不带/api前缀
@app.route('/health', methods=['GET'])
def root_health_check():
    """根路径健康检查接口"""
    health_data = {
        "status": "healthy",
        "service": "智能数据库分析系统 (多用户版)",
        "version": "2.1.0",
        "timestamp": datetime.now().isoformat()
    }
    
    # 检查是否是JSONP请求
    callback = request.args.get('callback', False)
    if callback:
        # 如果是JSONP请求，返回JavaScript代码
        jsonp_response = f"{callback}({json.dumps(health_data)});"
        return Response(jsonp_response, mimetype="application/javascript")
    else:
        # 普通JSON响应
        return jsonify(health_data)

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    health_data = {
        "status": "healthy",
        "service": "智能数据库分析系统 (多用户版)",
        "version": "2.1.0",
        "timestamp": datetime.now().isoformat()
    }
    
    # 检查是否是JSONP请求
    callback = request.args.get('callback', False)
    if callback:
        # 如果是JSONP请求，返回JavaScript代码
        jsonp_response = f"{callback}({json.dumps(health_data)});"
        return Response(jsonp_response, mimetype="application/javascript")
    else:
        # 普通JSON响应
        return jsonify(health_data)

# 新增：用户列表接口（用于调试和管理）
@app.route('/api/users', methods=['GET'])
def list_users():
    """获取所有用户列表（调试用）"""
    try:
        users = []
        data_dir = user_manager.base_data_dir
        
        for user_dir in data_dir.glob('user_*'):
            if user_dir.is_dir():
                user_id = user_dir.name.replace('user_', '')
                user_info_file = user_dir / 'user_info.json'
                
                if user_info_file.exists():
                    try:
                        with open(user_info_file, 'r', encoding='utf-8') as f:
                            user_info = json.load(f)
                            
                        # 添加统计信息
                        user_stats = user_manager.get_user_stats(user_id)
                        user_info['stats'] = user_stats
                        users.append(user_info)
                    except:
                        # 如果用户信息文件损坏，创建基本信息
                        users.append({
                            'user_id': user_id,
                            'username': f'User_{user_id}',
                            'is_guest': user_id.startswith('guest_'),
                            'last_activity': 'Unknown',
                            'stats': user_manager.get_user_stats(user_id)
                        })
        
        return jsonify({
            "success": True,
            "users": users,
            "total_users": len(users),
            "active_analyzers": len(user_analyzers)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"获取用户列表失败: {str(e)}"
        }), 500

# 添加静态文件服务
@app.route('/')
def index():
    """提供前端首页"""
    try:
        frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend', 'index.html')
        print(f"提供前端文件: {frontend_path}")
        return send_file(frontend_path)
    except Exception as e:
        print(f"无法提供前端文件: {e}")
        # 如果无法提供文件，返回一个简单的HTML页面
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>智能数据库分析系统</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; height: 100vh; }
                .container { max-width: 800px; margin: 0 auto; background: rgba(255, 255, 255, 0.1); padding: 20px; border-radius: 10px; backdrop-filter: blur(10px); }
                h1 { color: white; }
                .btn { display: inline-block; background: white; color: #667eea; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>智能数据库分析系统</h1>
                <p>前端文件无法加载。请使用以下链接访问系统：</p>
                <a class="btn" href="file://FRONTEND_PATH" target="_blank">打开前端界面</a>
                <p>或者直接在浏览器中打开：<code>file://FRONTEND_PATH</code></p>
                <hr>
                <p>API服务正常运行中。API端点：<code>http://localhost:5000/api</code></p>
                <p>健康检查：<a href="/api/health" style="color: white;">http://localhost:5000/api/health</a></p>
            </div>
        </body>
        </html>
        """.replace("FRONTEND_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend', 'index.html'))
        return html

@app.route('/<path:filename>')
def serve_static(filename):
    """提供前端静态文件"""
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend')
    file_path = os.path.join(frontend_dir, filename)
    print(f"提供静态文件: {file_path}")
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return "File not found", 404

if __name__ == '__main__':
    try:
        print("🤖 智能数据库分析系统 API 服务启动 (多用户版)")
        print("=" * 60)
        print("📡 API端点:")
        print("  GET  /api/status              - 系统状态 (多用户)")
        print("  GET  /api/user/status         - 用户状态")
        print("  POST /api/upload              - 上传CSV文件 (多用户)")
        print("  POST /api/analyze             - 智能分析 (多用户)")
        print("  POST /api/analyze-stream      - 智能分析流式 (多用户)")
        print("  GET  /api/users               - 用户列表 (调试)")
        print("  GET  /api/health              - 健康检查")
        print("=" * 60)
        print("🗂️  数据存储结构:")
        print("  data/")
        print("  ├── user_001/                # 用户1专属目录")
        print("  │   ├── analysis.db          # 用户1数据库")
        print("  │   ├── conversation_memory.json  # 用户1记忆")
        print("  │   ├── reports/             # 用户1报告")
        print("  │   └── uploads/             # 用户1上传")
        print("  ├── user_002/                # 用户2专属目录")
        print("  └── shared/")
        print("      └── uploads/             # 共享临时文件")
        print("=" * 60)
        
        # 开发模式启动
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("请检查 ANTHROPIC_API_KEY 环境变量是否设置")