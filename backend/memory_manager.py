# memory_manager.py - 独立记忆管理模块
# 功能：分析和优化对话历史记忆，减少token消耗

from anthropic import Anthropic
import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path

class MemoryManager:
    """独立的记忆管理器 - 不影响主程序功能"""
    
    def __init__(self, api_key: str, model_name: str = "claude-sonnet-4-20250514"):
        """
        初始化记忆管理器
        
        Args:
            api_key: API密钥
            model_name: 模型名称
        """
        self.client = Anthropic(api_key=api_key)
        self.model_name = model_name
        self.current_db_path = None
        self.current_conversation_id = None
        
        # 定义记忆操作工具
        self.tools = [
            {
                "name": "get_conversation_messages",
                "description": "获取对话中的所有消息",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "conversation_id": {
                            "type": "string",
                            "description": "对话ID"
                        }
                    },
                    "required": ["conversation_id"]
                }
            },
            {
                "name": "delete_message",
                "description": "标记删除指定消息（软删除）",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "message_id": {
                            "type": "string",
                            "description": "要删除的消息ID"
                        },
                        "reason": {
                            "type": "string",
                            "description": "删除原因"
                        }
                    },
                    "required": ["message_id", "reason"]
                }
            },
            {
                "name": "add_memory_summary",
                "description": "添加记忆总结到对话中",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "summary_content": {
                            "type": "string",
                            "description": "记忆总结内容"
                        },
                        "summary_type": {
                            "type": "string",
                            "description": "总结类型：key_points, data_insights, conclusions等"
                        }
                    },
                    "required": ["summary_content", "summary_type"]
                }
            },
            {
                "name": "mark_important_message",
                "description": "标记重要消息（确保不被删除）",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "message_id": {
                            "type": "string",
                            "description": "消息ID"
                        },
                        "importance_level": {
                            "type": "string",
                            "description": "重要性级别：critical, important, normal"
                        },
                        "reason": {
                            "type": "string",
                            "description": "标记为重要的原因"
                        }
                    },
                    "required": ["message_id", "importance_level", "reason"]
                }
            },
            {
                "name": "get_memory_stats",
                "description": "获取记忆统计信息",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "conversation_id": {
                            "type": "string",
                            "description": "对话ID"
                        }
                    },
                    "required": ["conversation_id"]
                }
            }
        ]
    
    def analyze_conversation_memory(self, history_db_path: str, conversation_id: str) -> Dict[str, Any]:
        """
        分析指定对话的记忆并执行优化
        
        Args:
            history_db_path: 历史数据库路径
            conversation_id: 对话ID
            
        Returns:
            分析和优化结果
        """
        self.current_db_path = history_db_path
        self.current_conversation_id = conversation_id
        
        print(f"🧠 开始分析对话记忆: {conversation_id}")
        print(f"📂 数据库路径: {history_db_path}")
        
        # 构建分析提示词
        analysis_prompt = f"""
你是一个专业的对话记忆管理专家。你的任务是分析用户的对话历史，优化记忆使用效率。

当前对话ID: {conversation_id}

你可以使用以下工具来分析和优化记忆：
1. get_conversation_messages - 获取对话消息
2. get_memory_stats - 获取记忆统计信息
3. delete_message - 删除无用消息  
4. add_memory_summary - 添加记忆总结
5. mark_important_message - 标记重要消息

请按以下步骤进行分析和优化：

1. 首先获取对话消息和统计信息
2. 分析消息的重要性和冗余性
3. 识别可以删除的消息：
   - 重复的询问或确认
   - 简单的"好的"、"明白"等回复
   - 错误的尝试或无效的查询
   - 冗余的中间步骤
4. 识别需要保留的关键消息：
   - 重要的数据分析结果
   - 关键的业务结论
   - 用户的核心需求
   - 有价值的洞察和发现
5. 为删除的内容生成简洁的记忆总结
6. 标记真正重要的消息
7. 执行优化操作

分析原则：
- 保留核心业务逻辑和重要结论
- 删除冗余和无价值的交互
- 生成简洁但完整的记忆总结
- 确保优化后的对话仍然有完整的上下文
- 优先保留数据分析结果和用户洞察

开始分析并执行优化操作。
"""
        
        try:
            # 使用LLM进行记忆分析和优化
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=4000,
                tools=self.tools,
                messages=[{"role": "user", "content": analysis_prompt}]
            )
            
            # 处理LLM的响应和工具调用
            return self._process_llm_response(response)
            
        except Exception as e:
            logging.error(f"记忆分析失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "记忆分析过程中出现错误"
            }
    
    def _process_llm_response(self, response) -> Dict[str, Any]:
        """处理LLM响应和工具调用"""
        results = {
            "success": True,
            "analysis_steps": [],
            "operations_performed": [],
            "statistics": {},
            "summary": ""
        }
        
        # 处理工具调用
        if hasattr(response, 'content'):
            for content_block in response.content:
                if hasattr(content_block, 'type'):
                    if content_block.type == 'text':
                        results["summary"] += content_block.text
                    elif content_block.type == 'tool_use':
                        # 执行工具调用
                        tool_result = self._execute_tool(
                            content_block.name, 
                            content_block.input
                        )
                        results["operations_performed"].append({
                            "tool": content_block.name,
                            "input": content_block.input,
                            "result": tool_result
                        })
        
        return results
    
    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """执行记忆操作工具"""
        try:
            if tool_name == "get_conversation_messages":
                return self._get_conversation_messages(tool_input["conversation_id"])
            elif tool_name == "delete_message":
                return self._delete_message(tool_input["message_id"], tool_input["reason"])
            elif tool_name == "add_memory_summary":
                return self._add_memory_summary(
                    tool_input["summary_content"], 
                    tool_input["summary_type"]
                )
            elif tool_name == "mark_important_message":
                return self._mark_important_message(
                    tool_input["message_id"],
                    tool_input["importance_level"],
                    tool_input["reason"]
                )
            elif tool_name == "get_memory_stats":
                return self._get_memory_stats(tool_input["conversation_id"])
            else:
                return {"success": False, "error": f"未知工具: {tool_name}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_conversation_messages(self, conversation_id: str) -> Dict[str, Any]:
        """获取对话中的所有消息"""
        try:
            with sqlite3.connect(self.current_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT messages FROM conversation_history 
                    WHERE conversation_id = ?
                ''', (conversation_id,))
                
                result = cursor.fetchone()
                if result and result[0]:
                    messages = json.loads(result[0])
                    print(f"📚 获取到 {len(messages)} 条消息")
                    return {
                        "success": True,
                        "messages": messages,
                        "count": len(messages)
                    }
                else:
                    return {"success": False, "error": "未找到对话消息"}
                    
        except Exception as e:
            return {"success": False, "error": f"获取消息失败: {str(e)}"}
    
    def _delete_message(self, message_id: str, reason: str) -> Dict[str, Any]:
        """标记删除指定消息"""
        try:
            with sqlite3.connect(self.current_db_path) as conn:
                cursor = conn.cursor()
                
                # 获取当前消息
                cursor.execute('''
                    SELECT messages FROM conversation_history 
                    WHERE conversation_id = ?
                ''', (self.current_conversation_id,))
                
                result = cursor.fetchone()
                if result and result[0]:
                    messages = json.loads(result[0])
                    
                    # 查找并标记删除消息
                    message_found = False
                    for msg in messages:
                        if msg.get("id") == message_id:
                            msg["deleted"] = True
                            msg["deleted_at"] = datetime.now().isoformat()
                            msg["deleted_reason"] = reason
                            message_found = True
                            break
                    
                    if message_found:
                        # 更新数据库
                        cursor.execute('''
                            UPDATE conversation_history 
                            SET messages = ?
                            WHERE conversation_id = ?
                        ''', (json.dumps(messages), self.current_conversation_id))
                        
                        conn.commit()
                        print(f"🗑️ 已删除消息: {message_id} (原因: {reason})")
                        return {"success": True, "message": f"消息 {message_id} 已标记删除"}
                    else:
                        return {"success": False, "error": f"未找到消息 {message_id}"}
                else:
                    return {"success": False, "error": "未找到对话记录"}
                    
        except Exception as e:
            return {"success": False, "error": f"删除消息失败: {str(e)}"}
    
    def _add_memory_summary(self, summary_content: str, summary_type: str) -> Dict[str, Any]:
        """添加记忆总结"""
        try:
            with sqlite3.connect(self.current_db_path) as conn:
                cursor = conn.cursor()
                
                # 获取当前消息
                cursor.execute('''
                    SELECT messages FROM conversation_history 
                    WHERE conversation_id = ?
                ''', (self.current_conversation_id,))
                
                result = cursor.fetchone()
                if result and result[0]:
                    messages = json.loads(result[0])
                else:
                    messages = []
                
                # 创建记忆总结消息
                summary_message = {
                    "id": f"memory_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "role": "system",
                    "content": summary_content,
                    "type": "memory_summary",
                    "summary_type": summary_type,
                    "created_at": datetime.now().isoformat(),
                    "is_memory_summary": True
                }
                
                # 添加到消息列表
                messages.append(summary_message)
                
                # 更新数据库
                cursor.execute('''
                    UPDATE conversation_history 
                    SET messages = ?
                    WHERE conversation_id = ?
                ''', (json.dumps(messages), self.current_conversation_id))
                
                conn.commit()
                print(f"📝 已添加记忆总结: {summary_type}")
                return {"success": True, "message": f"已添加{summary_type}类型的记忆总结"}
                
        except Exception as e:
            return {"success": False, "error": f"添加记忆总结失败: {str(e)}"}
    
    def _mark_important_message(self, message_id: str, importance_level: str, reason: str) -> Dict[str, Any]:
        """标记重要消息"""
        try:
            with sqlite3.connect(self.current_db_path) as conn:
                cursor = conn.cursor()
                
                # 获取当前消息
                cursor.execute('''
                    SELECT messages FROM conversation_history 
                    WHERE conversation_id = ?
                ''', (self.current_conversation_id,))
                
                result = cursor.fetchone()
                if result and result[0]:
                    messages = json.loads(result[0])
                    
                    # 查找并标记重要消息
                    message_found = False
                    for msg in messages:
                        if msg.get("id") == message_id:
                            msg["important"] = True
                            msg["importance_level"] = importance_level
                            msg["importance_reason"] = reason
                            msg["marked_important_at"] = datetime.now().isoformat()
                            message_found = True
                            break
                    
                    if message_found:
                        # 更新数据库
                        cursor.execute('''
                            UPDATE conversation_history 
                            SET messages = ?
                            WHERE conversation_id = ?
                        ''', (json.dumps(messages), self.current_conversation_id))
                        
                        conn.commit()
                        print(f"⭐ 已标记重要消息: {message_id} (级别: {importance_level})")
                        return {"success": True, "message": f"消息 {message_id} 已标记为{importance_level}"}
                    else:
                        return {"success": False, "error": f"未找到消息 {message_id}"}
                else:
                    return {"success": False, "error": "未找到对话记录"}
                    
        except Exception as e:
            return {"success": False, "error": f"标记重要消息失败: {str(e)}"}
    
    def _get_memory_stats(self, conversation_id: str) -> Dict[str, Any]:
        """获取记忆统计信息"""
        try:
            with sqlite3.connect(self.current_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT messages FROM conversation_history 
                    WHERE conversation_id = ?
                ''', (conversation_id,))
                
                result = cursor.fetchone()
                if result and result[0]:
                    messages = json.loads(result[0])
                    
                    # 统计信息
                    total_messages = len(messages)
                    deleted_messages = len([m for m in messages if m.get("deleted")])
                    important_messages = len([m for m in messages if m.get("important")])
                    memory_summaries = len([m for m in messages if m.get("is_memory_summary")])
                    active_messages = total_messages - deleted_messages
                    
                    # 估算token数量（简单估算）
                    total_tokens = sum(len(str(m.get("content", "")).split()) * 1.3 for m in messages if not m.get("deleted"))
                    
                    stats = {
                        "success": True,
                        "total_messages": total_messages,
                        "active_messages": active_messages,
                        "deleted_messages": deleted_messages,
                        "important_messages": important_messages,
                        "memory_summaries": memory_summaries,
                        "estimated_tokens": int(total_tokens)
                    }
                    
                    print(f"📊 记忆统计: 总消息{total_messages}, 活跃{active_messages}, 已删除{deleted_messages}")
                    return stats
                else:
                    return {"success": False, "error": "未找到对话记录"}
                    
        except Exception as e:
            return {"success": False, "error": f"获取统计信息失败: {str(e)}"}

def main():
    """测试记忆管理功能"""
    # 这里可以添加测试代码
    print("记忆管理模块已加载")

if __name__ == "__main__":
    main() 