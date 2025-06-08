# 完整优化版数据库分析器 - 完整SQL执行记录
# 版本: 2.1.0 - 最终优化版

from anthropic import Anthropic
import sqlite3
import pandas as pd
import os
from tkinter import filedialog
import tkinter as tk
from datetime import datetime
import json
import re
from typing import Dict, List, Optional, Any

class ConversationMemory:
    """完整记忆管理类 - 保存所有SQL执行记录和HTML内容"""
    
    def __init__(self, memory_file="conversation_memory.json"):
        self.conversation_history = []
        self.memory_file = memory_file
        self.load_memory()

    def save_context(self, user_input, ai_response, html_content: str = None, 
                    tool_calls: List = None, analysis_metadata: Dict = None):
        """
        保存完整的对话上下文
        
        Args:
            user_input: 用户输入 (字符串或字典)
            ai_response: AI的完整响应内容 (字符串)
            html_content: 生成的HTML内容
            tool_calls: 完整的工具调用列表
            analysis_metadata: 分析元数据
        """
        timestamp = datetime.now().isoformat()
        
        # 调试输出
        print(f"\n🔍 保存上下文 - 工具调用列表类型: {type(tool_calls)}")
        if isinstance(tool_calls, list):
            print(f"📊 工具调用数量: {len(tool_calls)}")
        
        # 处理可能是字典的输入
        user_query = ""
        tool_calls_list = []
        if isinstance(user_input, dict):
            user_query = user_input.get("input", "")
            # 如果tools存在于user_input中，使用它作为工具调用列表
            if tool_calls is None and "tools" in user_input:
                tool_calls_list = user_input.get("tools", [])
                print(f"📌 从user_input获取工具调用: {len(tool_calls_list)}个")
        else:
            user_query = str(user_input)
        
        # 如果外部传入了工具调用列表，优先使用它
        if tool_calls is not None:
            tool_calls_list = tool_calls
            print(f"📌 使用外部传入的工具调用: {len(tool_calls_list)}个")
            
        # 确保AI响应是字符串
        ai_response_text = str(ai_response) if ai_response is not None else ""
        
        # 保存完整的工具调用记录（包括所有SQL执行详情）
        complete_tool_calls = []
        if tool_calls_list:
            for i, tool_call in enumerate(tool_calls_list, 1):
                print(f"  工具 #{i}: {tool_call.get('tool_name')}")
                complete_tool = {
                    "sequence": i,
                    "tool_name": tool_call.get('tool_name'),
                    "tool_input": tool_call.get('input', {}),
                    "execution_result": tool_call.get('result', {}),
                    "timestamp": datetime.now().isoformat(),
                    "success": 'error' not in tool_call.get('result', {}),
                    "performance": {
                        "execution_time": tool_call.get('result', {}).get('execution_time', 0),
                        "rows_returned": tool_call.get('result', {}).get('row_count', 0)
                    }
                }
                complete_tool_calls.append(complete_tool)
        
        # 构建完整的对话记录
        conversation_entry = {
            "conversation_id": len(self.conversation_history) + 1,
            "timestamp": timestamp,
            "user_interaction": {
                "query": user_query,
                "query_type": self._classify_query(user_query),
                "keywords": self._extract_keywords(user_query)
            },
            "ai_analysis": {
                "full_response": ai_response_text,
                "summary": self._extract_summary(ai_response_text),
                "key_insights": self._extract_insights(ai_response_text),
                "html_output": html_content or "",
                "response_length": len(ai_response_text) if ai_response_text else 0
            },
            "database_operations": {
                "total_tool_calls": len(complete_tool_calls),
                "complete_sql_history": complete_tool_calls,
                "database_info": {
                    "db_path": analysis_metadata.get('database', '') if analysis_metadata else '',
                    "table_name": analysis_metadata.get('table', '') if analysis_metadata else '',
                    "connection_status": "active" if analysis_metadata else "unknown"
                },
                "performance_summary": {
                    "total_execution_time": sum(tc.get('performance', {}).get('execution_time', 0) for tc in complete_tool_calls),
                    "total_rows_processed": sum(tc.get('performance', {}).get('rows_returned', 0) for tc in complete_tool_calls),
                    "successful_queries": sum(1 for tc in complete_tool_calls if tc.get('success', False)),
                    "failed_queries": sum(1 for tc in complete_tool_calls if not tc.get('success', True))
                }
            },
            "output_artifacts": {
                "html_report_file": analysis_metadata.get('html_file', '') if analysis_metadata else '',
                "html_content_size": len(html_content) if html_content else 0,
                "analysis_type": analysis_metadata.get('analysis_type', '') if analysis_metadata else 'unknown',
                "report_generated": bool(html_content)
            },
            "session_metadata": {
                "iterations_count": analysis_metadata.get('iterations', 0) if analysis_metadata else 0,
                "analysis_duration": self._calculate_duration(),
                "completion_status": "completed" if not analysis_metadata or analysis_metadata.get('iterations', 0) > 0 else "incomplete"
            }
        }
        
        self.conversation_history.append(conversation_entry)
        self.save_memory()
        
        # 显示详细保存状态
        print(f"\n💾 完整记忆已保存:")
        print(f"  🆔 对话ID: {conversation_entry['conversation_id']}")
        print(f"  🔧 工具调用: {len(complete_tool_calls)}次")
        print(f"  🗃️  SQL查询: {conversation_entry['database_operations']['performance_summary']['successful_queries']}次成功")
        if html_content:
            print(f"  📄 HTML内容: {len(html_content):,}字符")
        print(f"  ⏱️  总执行时间: {conversation_entry['database_operations']['performance_summary']['total_execution_time']:.3f}秒")
        print(f"  📊 处理数据: {conversation_entry['database_operations']['performance_summary']['total_rows_processed']:,}行")
    
    def _classify_query(self, query: str) -> str:
        """分类用户查询类型"""
        if not query:
            return "general"
            
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in ['html', '报告', '可视化', '图表']):
            return "report_generation"
        elif any(keyword in query_lower for keyword in ['分析', '统计', '洞察']):
            return "data_analysis"
        elif any(keyword in query_lower for keyword in ['优化', '改进', '修改']):
            return "optimization"
        elif any(keyword in query_lower for keyword in ['基础', '概览', '总结']):
            return "overview"
        else:
            return "general"
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        if not text:
            return []
            
        # 简单的关键词提取
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [word for word in words if len(word) > 2 and word not in ['the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'does', 'let', 'put', 'say', 'she', 'too', 'use']]
        return list(set(keywords))[:10]  # 返回前10个唯一关键词
    
    def _extract_summary(self, ai_response: str) -> str:
        """从AI响应中提取摘要"""
        if not ai_response:
            return "数据分析报告"
            
        lines = ai_response.split('\n')
        summary_parts = []
        
        for line in lines:
            line = line.strip()
            if any(keyword in line for keyword in ['## ', '### ', '#### ', '总结', '摘要', '关键发现', '核心洞察', '分析报告']):
                clean_line = re.sub(r'^#+\s*', '', line)
                if len(clean_line) > 5:
                    summary_parts.append(clean_line)
        
        # 如果没有找到标题，使用前几句话
        if not summary_parts:
            sentences = [s.strip() for s in ai_response.split('.') if len(s.strip()) > 20]
            summary_parts = sentences[:2]
                
        return ' | '.join(summary_parts[:3]) if summary_parts else "数据分析报告"
    
    def _extract_insights(self, ai_response: str) -> List[str]:
        """提取关键洞察"""
        if not ai_response:
            return []
            
        insights = []
        lines = ai_response.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line for keyword in ['建议', '优化', '改进', '注意', '关键', '发现', '洞察', '重要']):
                # 清理格式标记
                clean_line = re.sub(r'^[-*•]\s*', '', line)
                clean_line = re.sub(r'^\d+\.\s*', '', clean_line)
                if len(clean_line) > 15:  # 过滤太短的内容
                    insights.append(clean_line)
        
        return insights[:8]  # 最多保存8条洞察
    
    def _calculate_duration(self) -> str:
        """计算分析持续时间"""
        return f"{datetime.now().strftime('%H:%M:%S')}"
    
    def get_relevant_context(self, current_query: str, max_results: int = 2) -> str:
        """获取相关的历史上下文"""
        if not self.conversation_history:
            return ""
        
        current_keywords = set(self._extract_keywords(current_query))
        relevant_conversations = []
        
        for entry in self.conversation_history:
            # 计算关键词重叠度
            entry_keywords = set(entry['user_interaction']['keywords'])
            keyword_overlap = len(current_keywords & entry_keywords)
            
            # 计算查询类型匹配度
            query_type_match = 1 if entry['user_interaction']['query_type'] == self._classify_query(current_query) else 0
            
            # 综合相关度评分
            relevance_score = keyword_overlap + (query_type_match * 2)
            
            if relevance_score > 0:
                relevant_conversations.append((entry, relevance_score))
        
        if not relevant_conversations:
            return ""
        
        # 按相关度排序
        relevant_conversations.sort(key=lambda x: x[1], reverse=True)
        
        # 构建详细的上下文信息
        context_parts = ["=== 🔍 相关历史分析 ==="]
        for entry, score in relevant_conversations[:max_results]:
            context_parts.append(f"📅 对话ID {entry['conversation_id']} | {entry['timestamp'][:16]}")
            context_parts.append(f"❓ 问题: {entry['user_interaction']['query']}")
            context_parts.append(f"📊 摘要: {entry['ai_analysis']['summary']}")
            context_parts.append(f"🔧 工具调用: {entry['database_operations']['total_tool_calls']}次")
            
            # 显示关键SQL操作
            if entry['database_operations']['complete_sql_history']:
                context_parts.append(f"🗃️  主要SQL操作:")
                for i, sql_op in enumerate(entry['database_operations']['complete_sql_history'][:3], 1):
                    sql_text = sql_op['tool_input'].get('sql', sql_op['tool_name'])
                    if sql_text and sql_text != sql_op['tool_name']:
                        context_parts.append(f"   {i}. {sql_text[:80]}...")
                    else:
                        context_parts.append(f"   {i}. {sql_op['tool_name']}")
            
            if entry['ai_analysis']['html_output']:
                context_parts.append(f"📄 HTML报告: {entry['output_artifacts']['html_content_size']:,}字符")
            
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def get_html_content(self, conversation_id: int = None) -> str:
        """获取指定对话的HTML内容"""
        if conversation_id is None and self.conversation_history:
            # 获取最新的HTML内容
            latest = self.conversation_history[-1]
            return latest.get('ai_analysis', {}).get('html_output', '')
        
        for entry in self.conversation_history:
            if entry['conversation_id'] == conversation_id:
                return entry.get('ai_analysis', {}).get('html_output', '')
        
        return ""
    
    def get_sql_history(self, conversation_id: int = None) -> List[Dict]:
        """获取SQL执行历史"""
        if conversation_id is None:
            # 返回所有SQL历史
            all_sql = []
            for entry in self.conversation_history:
                for sql_op in entry['database_operations']['complete_sql_history']:
                    sql_op['conversation_id'] = entry['conversation_id']
                    sql_op['conversation_timestamp'] = entry['timestamp']
                    all_sql.append(sql_op)
            return all_sql
        else:
            # 返回指定对话的SQL历史
            for entry in self.conversation_history:
                if entry['conversation_id'] == conversation_id:
                    return entry['database_operations']['complete_sql_history']
            return []
    
    def save_memory(self):
        """保存记忆到文件 - 完整格式"""
        try:
            # 计算统计信息
            total_sql_calls = sum(entry['database_operations']['total_tool_calls'] for entry in self.conversation_history)
            total_html_reports = sum(1 for entry in self.conversation_history if entry['ai_analysis']['html_output'])
            total_successful_queries = sum(entry['database_operations']['performance_summary']['successful_queries'] for entry in self.conversation_history)
            total_failed_queries = sum(entry['database_operations']['performance_summary']['failed_queries'] for entry in self.conversation_history)
            
            memory_data = {
                "metadata": {
                    "version": "2.1.0",
                    "description": "完整SQL执行记录和HTML内容保存",
                    "created": datetime.now().isoformat(),
                    "total_conversations": len(self.conversation_history),
                    "last_updated": datetime.now().isoformat(),
                    "file_format": "complete_memory_with_full_sql_history"
                },
                "conversations": self.conversation_history,
                "global_statistics": {
                    "total_sql_operations": total_sql_calls,
                    "successful_sql_queries": total_successful_queries,
                    "failed_sql_queries": total_failed_queries,
                    "html_reports_generated": total_html_reports,
                    "avg_iterations_per_conversation": sum(entry['session_metadata']['iterations_count'] for entry in self.conversation_history) / len(self.conversation_history) if self.conversation_history else 0,
                    "total_data_rows_processed": sum(entry['database_operations']['performance_summary']['total_rows_processed'] for entry in self.conversation_history),
                    "total_execution_time": sum(entry['database_operations']['performance_summary']['total_execution_time'] for entry in self.conversation_history)
                },
                "schema_info": {
                    "conversation_structure": {
                        "conversation_id": "Unique identifier for each conversation",
                        "user_interaction": "Complete user query information",
                        "ai_analysis": "Full AI response and HTML content",
                        "database_operations": "Complete SQL execution history with results",
                        "output_artifacts": "Generated files and reports",
                        "session_metadata": "Analysis session information"
                    }
                }
            }
            
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, ensure_ascii=False, indent=2)
                
            print(f"💾 记忆文件已保存: {self.memory_file}")
            print(f"📊 文件大小: {os.path.getsize(self.memory_file):,} 字节")
                
        except Exception as e:
            print(f"💥 记忆保存失败: {e}")
    
    def load_memory(self):
        """从文件加载记忆"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    memory_data = json.load(f)
                
                # 兼容新旧格式
                if "conversations" in memory_data:
                    self.conversation_history = memory_data["conversations"]
                    stats = memory_data.get("global_statistics", {})
                    print(f"✅ 完整记忆加载成功:")
                    print(f"   📊 对话数: {len(self.conversation_history)}")
                    print(f"   🗃️  SQL操作: {stats.get('total_sql_operations', 0)}次")
                    print(f"   📄 HTML报告: {stats.get('html_reports_generated', 0)}个")
                    print(f"   📈 数据行数: {stats.get('total_data_rows_processed', 0):,}行")
                else:
                    # 兼容旧格式
                    old_history = memory_data.get("conversation_history", [])
                    print(f"⚠️  检测到旧格式，已兼容加载: {len(old_history)}条记录")
                    self.conversation_history = []
                    
        except Exception as e:
            print(f"⚠️  记忆加载失败: {e}")
            self.conversation_history = []
    
    def clear_memory(self):
        """清空记忆"""
        backup_name = f"{self.memory_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if os.path.exists(self.memory_file):
            # 创建备份
            import shutil
            shutil.copy2(self.memory_file, backup_name)
            os.remove(self.memory_file)
        
        self.conversation_history = []
        print("🗑️  记忆已清空")
        print(f"💾 备份文件: {backup_name}")
    
    def show_conversation_list(self):
        """显示详细对话列表"""
        if not self.conversation_history:
            print("📝 暂无对话记录")
            return
            
        print("\n📚 对话历史详细列表:")
        print("=" * 100)
        
        for entry in self.conversation_history:
            print(f"🆔 ID: {entry['conversation_id']} | ⏰ {entry['timestamp'][:19]} | 🎯 {entry['user_interaction']['query_type']}")
            print(f"❓ 问题: {entry['user_interaction']['query'][:70]}...")
            print(f"📊 摘要: {entry['ai_analysis']['summary'][:80]}...")
            print(f"🔧 操作: {entry['database_operations']['total_tool_calls']}次工具调用 | " +
                  f"✅ {entry['database_operations']['performance_summary']['successful_queries']}次成功 | " +
                  f"❌ {entry['database_operations']['performance_summary']['failed_queries']}次失败")
            print(f"📄 HTML: {'✅ ' + str(entry['output_artifacts']['html_content_size']) + '字符' if entry['ai_analysis']['html_output'] else '❌'}")
            print(f"⏱️  执行: {entry['database_operations']['performance_summary']['total_execution_time']:.3f}秒 | " +
                  f"📊 数据: {entry['database_operations']['performance_summary']['total_rows_processed']:,}行")
            print("-" * 100)
    
    def show_sql_details(self, conversation_id: int = None):
        """显示详细SQL执行记录"""
        sql_history = self.get_sql_history(conversation_id)
        
        if not sql_history:
            print("🗃️  无SQL执行记录")
            return
        
        print(f"\n🗃️  SQL执行详细记录 {'(对话ID: ' + str(conversation_id) + ')' if conversation_id else '(全部)'}")
        print("=" * 120)
        
        for sql_op in sql_history:
            print(f"🔄 序号: {sql_op.get('sequence', 'N/A')} | ⏰ {sql_op.get('timestamp', '')[:19]}")
            print(f"🔧 工具: {sql_op.get('tool_name', 'unknown')}")
            
            if sql_op.get('tool_input', {}).get('sql'):
                print(f"📝 SQL: {sql_op['tool_input']['sql']}")
            
            print(f"📊 结果: {'✅ 成功' if sql_op.get('success') else '❌ 失败'} | " +
                  f"⏱️ {sql_op.get('performance', {}).get('execution_time', 0):.3f}秒 | " +
                  f"📈 {sql_op.get('performance', {}).get('rows_returned', 0)}行")
            
            # 显示结果详情
            if sql_op.get('execution_result'):
                result = sql_op['execution_result']
                if 'columns' in result:
                    print(f"📋 列名: {', '.join(result['columns'][:5])}{'...' if len(result['columns']) > 5 else ''}")
                if 'error' in result:
                    print(f"❌ 错误: {result['error']}")
            
            print("-" * 120)
    
    def export_html_report(self, conversation_id: int, output_path: str = None):
        """导出指定对话的HTML报告"""
        html_content = self.get_html_content(conversation_id)
        if not html_content:
            print(f"❌ 对话 {conversation_id} 没有HTML内容")
            return False
            
        if output_path is None:
            output_path = f"exported_report_{conversation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"📄 HTML报告已导出: {output_path}")
            print(f"📊 文件大小: {os.path.getsize(output_path):,} 字节")
            return True
        except Exception as e:
            print(f"💥 导出失败: {e}")
            return False

    def get_memory_summary(self):
        """获取记忆摘要"""
        if not self.conversation_history:
            return {"conversation_count": 0}
            
        latest = self.conversation_history[-1]
        total_sql = sum(entry['database_operations']['total_tool_calls'] for entry in self.conversation_history)
        
        return {
            "conversation_count": len(self.conversation_history),
            "memory_file": self.memory_file,
            "latest_timestamp": latest["timestamp"],
            "latest_query": latest["user_interaction"]["query"],
            "has_html": bool(latest["ai_analysis"]["html_output"]),
            "total_sql_calls": total_sql,
            "latest_html_size": latest["output_artifacts"]["html_content_size"]
        }


class DatabaseAnalyzer:
    """数据库分析器类"""
    
    def __init__(self, api_key, model_name="claude-sonnet-4-20250514", base_url=None):
        """
        初始化数据库分析器
        
        Args:
            api_key: API密钥
            model_name: 模型名称
            base_url: API基础URL（可选）
        """
        client_params = {"api_key": api_key}
        if base_url:
            client_params["base_url"] = base_url
            print(f"🔧 DatabaseAnalyzer初始化: 使用自定义base_url={base_url}")
        else:
            print(f"🔧 DatabaseAnalyzer初始化: 未提供base_url，将使用默认值")
            
        self.client = Anthropic(**client_params)
        print(f"🔧 Anthropic客户端创建完成，实际使用的base_url: {self.client.base_url}")
        
        self.model_name = model_name
        self.debug_mode = False
        self.current_db_path = None
        self.current_table_name = None
        self.memory = ConversationMemory()
        
        # 定义工具 - 使用custom类型
        self.tools = [
            {
                "type": "custom",
                "name": "query_database",
                "description": "执行SQL查询获取数据库信息",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": "要执行的SQL查询语句"
                        }
                    },
                    "required": ["sql"]
                }
            },
            {
                "type": "custom",
                "name": "get_table_info",
                "description": "获取表的结构信息和样本数据",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
        
    def set_debug_mode(self, debug=True):
        """设置调试模式"""
        self.debug_mode = debug
        
    def debug_print(self, message, level="INFO"):
        """调试信息输出"""
        if self.debug_mode:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] [{level}] {message}")
            
    def debug_print_chunk(self, chunk):
        """详细打印模型响应块的内容"""
        if not self.debug_mode:
            return
            
        try:
            print("\n=== 模型响应块详情 ===")
            print(f"类型: {chunk.type}")
            
            if hasattr(chunk, 'content_block') and chunk.type == "content_block_start":
                print(f"内容块类型: {chunk.content_block.type}")
                if chunk.content_block.type == "tool_use":
                    print(f"工具名称: {chunk.content_block.name}")
                    print(f"工具ID: {chunk.content_block.id}")
            
            if hasattr(chunk, 'delta'):
                if hasattr(chunk.delta, 'type'):
                    print(f"Delta类型: {chunk.delta.type}")
                    
                    if chunk.delta.type == "tool_use" and hasattr(chunk.delta, 'tool_use'):
                        if hasattr(chunk.delta.tool_use, 'name'):
                            print(f"工具名称: {chunk.delta.tool_use.name}")
                        if hasattr(chunk.delta.tool_use, 'input'):
                            print(f"工具输入: {chunk.delta.tool_use.input}")
                    elif chunk.delta.type == "text_delta":
                        print(f"文本内容: {chunk.delta.text[:50]}...")
                    elif chunk.delta.type == "input_json_delta":
                        print(f"JSON输入: {chunk.delta.partial_json[:50]}...")
                else:
                    print(f"Delta没有type属性: {vars(chunk.delta) if hasattr(chunk.delta, '__dict__') else 'No __dict__'}")
            
            print("======================")
        except Exception as e:
            print(f"调试打印错误: {str(e)}")
            if self.debug_mode:
                import traceback
                traceback.print_exc()
    
    def import_csv_to_sqlite(self, csv_file_path, table_name, db_path="analysis_db.db"):
        """从CSV文件创建SQLite表并导入数据"""
        try:
            self.debug_print(f"开始导入CSV文件: {csv_file_path}")
            
            if not os.path.exists(csv_file_path):
                return {"success": False, "message": f"CSV文件不存在: {csv_file_path}"}
            
            # 读取CSV文件
            df = pd.read_csv(csv_file_path, encoding='utf-8')
            self.debug_print(f"CSV文件读取成功，共{len(df)}行，{len(df.columns)}列")
            
            # 清理列名
            df.columns = [self._clean_column_name(col) for col in df.columns]
            
            # 连接到SQLite数据库
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 删除已存在的表并创建新表
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            
            # 获取导入的行数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            rows_count = cursor.fetchone()[0]
            
            conn.commit()
            conn.close()
            
            # 保存当前数据库信息
            self.current_db_path = db_path
            self.current_table_name = table_name
            
            print(f"🗑️  清空之前的记忆以开始新的分析会话")
            self.memory.clear_memory()
            
            return {
                "success": True,
                "message": f"成功导入 {rows_count} 行数据到表 '{table_name}'",
                "rows_imported": rows_count,
                "columns": list(df.columns)
            }
            
        except Exception as e:
            self.debug_print(f"导入失败: {str(e)}", "ERROR")
            return {"success": False, "message": f"导入失败: {str(e)}"}
    
    def _clean_column_name(self, col_name):
        """清理列名"""
        cleaned = str(col_name).strip()
        cleaned = re.sub(r'[^\w\u4e00-\u9fff]', '_', cleaned)
        cleaned = re.sub(r'_+', '_', cleaned)
        cleaned = cleaned.strip('_')
        return cleaned or 'unnamed_column'
    
    def get_table_schema(self):
        """获取数据库表的结构信息"""
        if not self.current_db_path or not self.current_table_name:
            return "未连接到数据库"
        
        try:
            conn = sqlite3.connect(self.current_db_path)
            cursor = conn.cursor()
            
            # 获取表结构
            schema_info = cursor.execute(f"PRAGMA table_info({self.current_table_name})").fetchall()
            
            # 获取样本数据
            sample_data = cursor.execute(f"SELECT * FROM {self.current_table_name} LIMIT 3").fetchall()
            column_names = [description[0] for description in cursor.description]
            
            conn.close()
            
            # 构建结构描述
            schema = {
                "table_name": self.current_table_name,
                "columns": [{"name": col[1], "type": col[2]} for col in schema_info],
                "sample_data": [dict(zip(column_names, row)) for row in sample_data]
            }
            
            return schema
            
        except Exception as e:
            return f"获取表结构失败: {str(e)}"
    
    def query_database(self, sql):
        """执行SQL查询"""
        if not self.current_db_path:
            return {"error": "未连接到数据库"}
        
        # 输出正在执行的SQL
        print(f"\n🗃️  正在执行SQL查询:")
        print(f"   {sql}")
        
        try:
            conn = sqlite3.connect(self.current_db_path)
            cursor = conn.cursor()
            
            start_time = datetime.now()
            cursor.execute(sql)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            if sql.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                result_data = {
                    "columns": columns,
                    "data": results,
                    "row_count": len(results),
                    "sql_executed": sql,
                    "execution_time": execution_time,
                    "query_type": "SELECT",
                    "data_preview": results[:5] if results else []
                }
                
                print(f"✅ 查询成功: 返回 {len(results)} 行 x {len(columns)} 列 (耗时: {execution_time:.3f}s)")
                if len(results) > 0:
                    print(f"📋 列名: {', '.join(columns[:5])}{'...' if len(columns) > 5 else ''}")
                
                conn.close()
                return result_data
            else:
                conn.commit()
                conn.close()
                print(f"✅ 非查询语句执行成功 (耗时: {execution_time:.3f}s)")
                return {
                    "message": "查询执行成功", 
                    "sql_executed": sql, 
                    "execution_time": execution_time,
                    "query_type": "NON_SELECT"
                }
                
        except Exception as e:
            error_msg = f"查询执行失败: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "error": error_msg, 
                "sql_attempted": sql,
                "execution_time": 0,
                "query_type": "ERROR"
            }
    
    def execute_tool(self, tool_name, tool_input):
        """执行工具调用"""
        self.debug_print(f"执行工具: {tool_name}, 参数: {tool_input}")
        
        try:
            if tool_name == "query_database":
                sql = tool_input.get("sql", "")
                if not sql:
                    print("⚠️  警告: SQL参数为空")
                    return {"error": "SQL参数为空", "query_type": "ERROR"}
                return self.query_database(sql)
            
            elif tool_name == "get_table_info":
                print(f"🔍 获取表结构信息: {self.current_table_name}")
                result = self.get_table_schema()
                print(f"✅ 表结构获取完成")
                return {
                    "table_info": result,
                    "query_type": "TABLE_INFO",
                    "execution_time": 0.001
                }
            
            else:
                print(f"❌ 未知工具: {tool_name}")
                return {"error": f"未知工具: {tool_name}", "query_type": "ERROR"}
        except Exception as e:
            error_msg = f"工具执行错误: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return {
                "error": error_msg,
                "query_type": "ERROR",
                "execution_time": 0
            }
    
    def analyze_with_llm(self, user_query):
        """使用LLM进行智能数据分析 - 完整SQL记录版本"""
        if not self.current_db_path or not self.current_table_name:
            return "请先导入数据"
        
        self.debug_print(f"开始智能分析: {user_query}")
        
        # 创建HTML输出文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_filename = f"analysis_report_{timestamp}.html"
        
        # 获取相关的历史上下文
        conversation_context = self.memory.get_relevant_context(user_query)
        
        # 构建系统提示词
        system_prompt = f"""你是专业数据分析师，专门生成专家级美工质量的HTML数据分析报告。

        {conversation_context}

        数据库信息：
        - 路径: {self.current_db_path}
        - 表名: {self.current_table_name}

        🔧 可用工具：
        1. query_database: 执行SQL查询
        2. get_table_info: 获取表结构

        📋 分析流程：
        **阶段1：数据探索** (2-3次查询)
        - 获取总记录数和表结构
        - 检查核心字段完整性

        **阶段2：维度分析** (3-5次查询)  
        - 主要分类字段分布统计
        - 数值字段基础统计
        - 交叉验证数据一致性

        **阶段3：深度洞察** (2-3次查询)
        - 异常值检测
        - 多维度关联分析

        📊 HTML输出要求：
        **必须完整HTML文档** (<!DOCTYPE html>开头到</html>结尾)
        - Chart.js 3.9.1 交互图表
        - 专家级CSS设计
        - 响应式设计
        - 动态效果和交互
        - 要确保所有chart能够正常显示

        请基于数据分析生成完整的专家级HTML数据分析报告。"""

        # 用于收集完整的AI响应
        full_ai_response = []
        html_content = ""
        
        # 创建HTML文件
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write("")
        
        def write_to_html(content):
            """写入HTML文件并收集内容"""
            nonlocal html_content
            html_content += content
            with open(html_filename, 'a', encoding='utf-8') as f:
                f.write(content)
                f.flush()
        
        print(f"📄 正在生成HTML报告: {html_filename}")
        
        # 初始消息
        messages = [
            {"role": "user", "content": f"{system_prompt}\n\n用户需求: {user_query}"}
        ]
        
        # 根据用户查询判断分析深度
        query_lower = user_query.lower()
        if any(keyword in query_lower for keyword in ['简单', '基础', '概览', '快速']):
            max_iterations = 15
            analysis_type = "简单分析"
        elif any(keyword in query_lower for keyword in ['深度', '详细', '全面', '完整']):
            max_iterations = 30
            analysis_type = "深度分析"
        else:
            max_iterations = 50
            analysis_type = "标准分析"
        
        print(f"🎯 分析类型: {analysis_type} (最大{max_iterations}轮)")
        
        iteration = 0
        tool_calls_made = []
        
        while iteration < max_iterations:
            iteration += 1
            self.debug_print(f"第{iteration}轮对话")
            
            try:
                print(f"\n🔄 第{iteration}轮分析中...", end="", flush=True)
                
                # 调用Claude API (流式输出)
                response = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=40000,
                    messages=messages,
                    tools=self.tools,
                    stream=True
                )
                
                # 正确处理流式响应
                assistant_response = {"role": "assistant", "content": []}
                current_tool_inputs = {}  # 用于累积工具参数
                current_text_response = ""  # 收集文本响应
                
                print(f" 📝 正在写入HTML...")
                
                for chunk in response:
                    # 使用调试函数打印详细信息
                    self.debug_print_chunk(chunk)
                    
                    if chunk.type == "message_start":
                        continue
                    elif chunk.type == "content_block_start":
                        if chunk.content_block.type == "text":
                            assistant_response["content"].append({"type": "text", "text": ""})
                        elif chunk.content_block.type == "tool_use":
                            print(f"\n🔧 工具调用开始: {chunk.content_block.name}")
                            tool_block = {
                                "type": "tool_use",
                                "id": chunk.content_block.id,
                                "name": chunk.content_block.name,
                                "input": {}
                            }
                            assistant_response["content"].append(tool_block)
                            current_tool_inputs[chunk.content_block.id] = ""
                    elif chunk.type == "content_block_delta":
                        try:
                            if chunk.delta.type == "text_delta":
                                text_content = chunk.delta.text
                                assistant_response["content"][-1]["text"] += text_content
                                current_text_response += text_content
                                write_to_html(text_content)
                                print(".", end="", flush=True)
                            elif chunk.delta.type == "input_json_delta":
                                print(f"\n📄 JSON输入增量: {chunk.delta.partial_json[:30]}...")
                                if assistant_response["content"] and assistant_response["content"][-1].get("type") == "tool_use":
                                    tool_id = assistant_response["content"][-1]["id"]
                                    if tool_id in current_tool_inputs:
                                        current_tool_inputs[tool_id] += chunk.delta.partial_json
                        except Exception as e:
                            print(f"\n⚠️ 处理响应块错误: {str(e)}")
                            import traceback
                            traceback.print_exc()
                    elif chunk.type == "content_block_stop":
                        if assistant_response["content"] and assistant_response["content"][-1].get("type") == "tool_use":
                            tool_id = assistant_response["content"][-1]["id"]
                            if tool_id in current_tool_inputs:
                                try:
                                    json_str = current_tool_inputs[tool_id]
                                    # 处理可能的不完整JSON
                                    if json_str.strip():
                                        if not (json_str.strip().startswith('{') or json_str.strip().startswith('[')):
                                            json_str = '{' + json_str + '}'
                                        complete_input = json.loads(json_str)
                                        assistant_response["content"][-1]["input"] = complete_input
                                        print(f"\n✅ 解析工具参数成功: {complete_input}")
                                except json.JSONDecodeError as e:
                                    print(f"\n⚠️  工具参数解析失败: {e}")
                                    # 尝试修复常见的JSON错误
                                    try:
                                        # 尝试添加引号和大括号
                                        fixed_json = '{' + current_tool_inputs[tool_id].replace(':', '":').replace('{', '{"').replace(',', ',"') + '}'
                                        fixed_json = fixed_json.replace(':"', ':"').replace('",', '",').replace('{"', '{"')
                                        complete_input = json.loads(fixed_json)
                                        assistant_response["content"][-1]["input"] = complete_input
                                        print(f"\n🔧 修复后解析成功: {complete_input}")
                                    except:
                                        # 如果还是失败，使用空对象
                                        assistant_response["content"][-1]["input"] = {}
                                        print(f"\n❌ 无法修复JSON，使用空对象")
                    elif chunk.type == "message_stop":
                        break
                
                print(" ✅")
                
                # 收集完整的AI响应文本
                full_ai_response.append(current_text_response)
                
                # 添加响应到消息历史
                messages.append(assistant_response)
                
                # 检查是否有工具调用
                has_tool_use = any(block.get("type") == "tool_use" for block in assistant_response["content"])
                
                if has_tool_use:
                    # 执行工具调用
                    tool_results = []
                    
                    for content_block in assistant_response["content"]:
                        if content_block.get("type") == "tool_use":
                            tool_name = content_block["name"]
                            tool_input = content_block.get("input", {})
                            tool_id = content_block["id"]
                            
                            print(f"\n🔧 调用工具: {tool_name}")
                            
                            # 确保工具输入是有效的
                            if tool_name == "query_database":
                                if not tool_input or "sql" not in tool_input:
                                    # 如果没有SQL参数，尝试从名称中提取
                                    print(f"⚠️ 缺少SQL参数，尝试修复...")
                                    sql = "SELECT * FROM " + self.current_table_name + " LIMIT 5"
                                    tool_input = {"sql": sql}
                                    print(f"📝 使用默认SQL: {sql}")
                                else:
                                    print(f"📝 SQL: {tool_input['sql']}")
                            
                            # 执行工具
                            result = self.execute_tool(tool_name, tool_input)
                            
                            # 记录完整的工具调用信息
                            tool_calls_made.append({
                                "tool_name": tool_name,
                                "tool_input": tool_input,
                                "result": result
                            })
                            
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": tool_id,
                                "content": json.dumps(result, ensure_ascii=False, indent=2)
                            })
                    
                    # 添加工具结果到消息历史
                    messages.append({
                        "role": "user",
                        "content": tool_results
                    })
                    
                else:
                    # Claude给出了最终回答，保存完整记忆
                    complete_ai_response = "\n".join(full_ai_response)
                    
                    # 🔥 关键改进：保存完整的对话上下文，包括HTML内容和完整SQL记录
                    self.memory.save_context(
                        user_input=user_query,
                        ai_response=complete_ai_response,
                        html_content=html_content,
                        tool_calls=tool_calls_made,  # 包含完整SQL执行结果
                        analysis_metadata={
                            "database": self.current_db_path,
                            "table": self.current_table_name,
                            "analysis_type": analysis_type,
                            "iterations": iteration,
                            "html_file": html_filename
                        }
                    )
                    
                    print(f"\n✅ HTML报告生成完成!")
                    print(f"📄 文件位置: {os.path.abspath(html_filename)}")
                    print(f"📊 文件大小: {os.path.getsize(html_filename):,} 字节")
                    print(f"🔧 工具调用次数: {len(tool_calls_made)}")
                    print(f"💾 完整记录已保存: HTML({len(html_content):,}字符) + SQL详情")
                    
                    # 尝试自动打开HTML文件
                    try:
                        import webbrowser
                        webbrowser.open(f'file://{os.path.abspath(html_filename)}')
                        print("🌐 已自动在浏览器中打开报告")
                    except:
                        print("💡 请手动打开HTML文件查看报告")
                    
                    return f"HTML报告生成完成!\n文件: {html_filename}\n类型: {analysis_type}\n工具调用: {len(tool_calls_made)}次\n完整记录已保存: HTML({len(html_content):,}字符) + SQL详情"
                    
            except Exception as e:
                self.debug_print(f"API调用失败: {str(e)}", "ERROR")
                return f"分析失败: {str(e)}"
        
        return f"分析进行了{iteration}轮对话后达到限制"
    
    def show_memory_status(self):
        """显示记忆状态"""
        summary = self.memory.get_memory_summary()
        print("\n📚 当前记忆状态:")
        print(f"  📊 对话记录数: {summary['conversation_count']}")
        if summary.get('latest_timestamp'):
            print(f"  ⏰ 最新记录时间: {summary['latest_timestamp'][:19]}")
        
        if summary['conversation_count'] > 0:
            print(f"  ❓ 最新问题: {summary['latest_query'][:60]}...")
            print(f"  🗃️  总SQL调用: {summary.get('total_sql_calls', 0)}次")
            print(f"  📄 包含HTML: {'✅ ' + str(summary.get('latest_html_size', 0)) + '字符' if summary.get('has_html') else '❌'}")
    
    def show_sql_history(self):
        """显示SQL执行历史"""
        self.memory.show_sql_details()
    
    def clear_memory(self):
        """清空记忆"""
        self.memory.clear_memory()


def select_csv_file():
    """选择CSV文件"""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    try:
        csv_file = filedialog.askopenfilename(
            title="请选择CSV文件",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
            initialdir=os.getcwd()
        )
        root.destroy()
        return csv_file if csv_file else None
    except Exception as e:
        root.destroy()
        print(f"文件选择失败: {e}")
        return None

def main():
    """主程序 - 完整SQL记录版本"""
    print("🤖 智能数据库分析系统 (完整SQL记录版 v2.1)")
    print("=" * 60)
    
    # 配置API密钥
    api_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not api_key:
        print("未找到环境变量 ANTHROPIC_API_KEY")
        api_key = input("请输入您的 Anthropic API 密钥: ").strip()
    
    if not api_key:
        print("❌ 未提供API密钥，程序无法继续")
        return
    
    # 创建分析器实例
    analyzer = DatabaseAnalyzer(api_key)
    
    # 调试模式设置
    debug_choice = input("是否启用调试模式？(y/n, 默认n): ").strip().lower()
    analyzer.set_debug_mode(debug_choice == 'y')
    
    # 显示当前记忆状态
    analyzer.show_memory_status()
    
    # 数据导入选择
    print("\n📁 数据管理选项:")
    print("1. 导入新的CSV文件")
    print("2. 继续使用之前的数据")
    print("3. 查看记忆状态")
    print("4. 查看对话列表")
    print("5. 查看SQL执行历史")
    print("6. 清空记忆")
    
    choice = input("请选择操作 (1-6, 默认1): ").strip() or "1"
    
    if choice == "1":
        csv_file = select_csv_file()
        if not csv_file:
            print("未选择文件，程序退出")
            return
        
        table_name = input("请输入表名 (默认: data_table): ").strip() or "data_table"
        db_path = input("请输入数据库路径 (默认: analysis.db): ").strip() or "analysis.db"
        
        print(f"\n正在导入数据...")
        import_result = analyzer.import_csv_to_sqlite(csv_file, table_name, db_path)
        
        if not import_result["success"]:
            print(f"❌ {import_result['message']}")
            return
        
        print(f"✅ {import_result['message']}")
        
    elif choice == "2":
        if not analyzer.current_db_path:
            print("❌ 没有找到之前的数据库，请先导入数据")
            return
        print(f"✅ 继续使用数据库: {analyzer.current_db_path}")
        
    elif choice == "3":
        analyzer.show_memory_status()
        input("\n按回车键继续...")
        
    elif choice == "4":
        analyzer.memory.show_conversation_list()
        input("\n按回车键继续...")
        
    elif choice == "5":
        analyzer.show_sql_history()
        input("\n按回车键继续...")
        
    elif choice == "6":
        analyzer.clear_memory()
        input("按回车键继续...")
    
    # 智能分析交互
    print(f"\n🤖 智能分析模式已启动！(完整SQL记录版)")
    print("💡 现在会保存每个SQL的完整执行结果和HTML内容")
    print("\n📋 可用命令:")
    print("  - 'memory': 查看记忆状态")
    print("  - 'list': 查看对话列表")
    print("  - 'sql': 查看完整SQL执行历史")
    print("  - 'sql [ID]': 查看指定对话的SQL历史")
    print("  - 'export [ID]': 导出指定对话的HTML")
    print("  - 'html [ID]': 查看指定对话的HTML内容")
    print("  - 'clear': 清空记忆")
    print("  - 'quit': 退出程序")
    print("\n🚀 示例问题：")
    print("  - '帮我分析这个数据集的基本情况'")
    print("  - '给我生成一个完整的HTML分析报告'")
    print("  - '基于对话1的分析，重新生成更详细的报告'")
    print("  - '使用对话2的SQL查询结果，生成不同风格的图表'")
    print("-" * 60)
    
    while True:
        try:
            query = input("\n🔍 请描述您的分析需求: ").strip()
            
            if query.lower() in ['quit', 'exit', '退出']:
                print("👋 再见！所有记忆已自动保存。")
                break
                
            elif query.lower() in ['memory', '记忆']:
                analyzer.show_memory_status()
                continue
                
            elif query.lower() in ['list', '列表']:
                analyzer.memory.show_conversation_list()
                continue
                
            elif query.lower().startswith('sql'):
                parts = query.split()
                if len(parts) > 1 and parts[1].isdigit():
                    analyzer.memory.show_sql_details(int(parts[1]))
                else:
                    analyzer.memory.show_sql_details()
                continue
                
            elif query.lower().startswith('export'):
                parts = query.split()
                if len(parts) > 1 and parts[1].isdigit():
                    analyzer.memory.export_html_report(int(parts[1]))
                else:
                    print("用法: export [对话ID]")
                continue
                
            elif query.lower().startswith('html'):
                parts = query.split()
                if len(parts) > 1 and parts[1].isdigit():
                    html_content = analyzer.memory.get_html_content(int(parts[1]))
                    if html_content:
                        print(f"📄 HTML内容长度: {len(html_content):,} 字符")
                        print(f"📋 预览: {html_content[:300]}...")
                        
                        export_choice = input("是否导出到新文件？(y/n): ").strip().lower()
                        if export_choice == 'y':
                            analyzer.memory.export_html_report(int(parts[1]))
                    else:
                        print("❌ 指定对话没有HTML内容")
                else:
                    print("用法: html [对话ID]")
                continue
                
            elif query.lower() in ['clear', '清空']:
                confirm = input("⚠️  确认清空所有记忆？这将创建备份文件。(y/n): ").strip().lower()
                if confirm == 'y':
                    analyzer.clear_memory()
                continue
            
            if not query:
                continue
            
            print(f"\n🔄 Claude正在智能分析中...")
            
            # 执行智能分析
            result = analyzer.analyze_with_llm(query)
            
            print("\n" + "="*80)
            print("🤖 智能分析结果:")
            print("="*80)
            print(result)
            print("="*80)
            
            # 显示本次分析的统计
            summary = analyzer.memory.get_memory_summary()
            
            print(f"\n📊 当前记忆状态:")
            print(f"  📈 总对话数: {summary['conversation_count']}")
            print(f"  🗃️  总SQL调用: {summary.get('total_sql_calls', 0)}")
            print(f"  📄 最新HTML: {'✅ ' + str(summary.get('latest_html_size', 0)) + '字符' if summary.get('has_html') else '❌'}")
            print(f"  💾 记忆文件: {summary.get('memory_file', 'N/A')}")
            
        except KeyboardInterrupt:
            print("\n👋 程序被用户中断，所有记忆已保存，再见！")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {str(e)}")
            if analyzer.debug_mode:
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    main()