# conversation_history.py - 对话历史记录管理器
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

class ConversationHistoryManager:
    """对话历史记录管理器 - 存储用户查询历史"""
    
    def __init__(self, user_paths: Dict[str, Path]):
        """
        初始化历史记录管理器
        
        Args:
            user_paths: 用户路径字典，包含各种目录路径
        """
        self.user_paths = user_paths
        self.db_path = user_paths['user_dir'] / 'conversation_history.db'
        self._init_database()
        
        print("📚 对话历史记录管理器已初始化")
    
    def _init_database(self):
        """初始化数据库表结构"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建对话历史表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS conversation_history (
                        conversation_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        username TEXT NOT NULL,
                        start_time TEXT NOT NULL,
                        end_time TEXT,
                        status TEXT NOT NULL,
                        user_query TEXT NOT NULL,
                        system_prompt TEXT,
                        database_path TEXT,
                        table_name TEXT,
                        messages TEXT,  -- JSON格式存储
                        tool_calls TEXT,  -- JSON格式存储
                        analysis_summary TEXT,
                        total_iterations INTEGER DEFAULT 0,
                        final_status TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 创建索引
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_user_id ON conversation_history(user_id)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_start_time ON conversation_history(start_time)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_status ON conversation_history(status)
                ''')
                
                conn.commit()
                print(f"✅ 对话历史数据库初始化完成: {self.db_path}")
                
        except Exception as e:
            print(f"❌ 初始化对话历史数据库失败: {e}")
            raise
    
    def start_conversation(self, user_data: Dict[str, str], user_query: str, 
                          system_prompt: str, database_path: str, table_name: str) -> str:
        """
        开始新的对话记录
        
        Args:
            user_data: 用户信息
            user_query: 用户查询
            system_prompt: 系统提示词
            database_path: 数据库路径
            table_name: 表名
            
        Returns:
            conversation_id: 对话ID
        """
        conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"
        start_time = datetime.now().isoformat()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO conversation_history 
                    (conversation_id, user_id, username, start_time, status, 
                     user_query, system_prompt, database_path, table_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    conversation_id,
                    user_data['user_id'],
                    user_data['username'],
                    start_time,
                    'started',
                    user_query,
                    system_prompt,
                    database_path,
                    table_name
                ))
                
                conn.commit()
                print(f"🆕 开始新对话记录: {conversation_id}")
                return conversation_id
                
        except Exception as e:
            print(f"❌ 创建对话记录失败: {e}")
            raise
    
    def update_conversation_messages(self, conversation_id: str, messages: List[Dict[str, Any]]):
        """
        更新对话消息历史
        
        Args:
            conversation_id: 对话ID
            messages: 消息历史列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                messages_json = json.dumps(messages, ensure_ascii=False, indent=2)
                
                cursor.execute('''
                    UPDATE conversation_history 
                    SET messages = ?
                    WHERE conversation_id = ?
                ''', (messages_json, conversation_id))
                
                conn.commit()
                print(f"📝 更新对话消息: {conversation_id}")
                
        except Exception as e:
            print(f"❌ 更新对话消息失败: {e}")
    
    def update_tool_calls(self, conversation_id: str, tool_calls: List[Dict[str, Any]]):
        """
        更新工具调用记录
        
        Args:
            conversation_id: 对话ID
            tool_calls: 工具调用列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                tool_calls_json = json.dumps(tool_calls, ensure_ascii=False, indent=2)
                
                cursor.execute('''
                    UPDATE conversation_history 
                    SET tool_calls = ?
                    WHERE conversation_id = ?
                ''', (tool_calls_json, conversation_id))
                
                conn.commit()
                print(f"🔧 更新工具调用记录: {conversation_id}")
                
        except Exception as e:
            print(f"❌ 更新工具调用记录失败: {e}")
    
    def complete_conversation(self, conversation_id: str, status: str = 'completed', 
                            analysis_summary: str = None, total_iterations: int = 0):
        """
        完成对话记录
        
        Args:
            conversation_id: 对话ID
            status: 完成状态 (completed/error/interrupted)
            analysis_summary: 分析结果摘要
            total_iterations: 总迭代次数
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                end_time = datetime.now().isoformat()
                
                cursor.execute('''
                    UPDATE conversation_history 
                    SET end_time = ?, status = ?, analysis_summary = ?, 
                        total_iterations = ?, final_status = ?
                    WHERE conversation_id = ?
                ''', (end_time, status, analysis_summary, total_iterations, status, conversation_id))
                
                conn.commit()
                print(f"✅ 完成对话记录: {conversation_id} - {status}")
                
        except Exception as e:
            print(f"❌ 完成对话记录失败: {e}")
    
    def get_conversation_history(self, user_id: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取用户对话历史
        
        Args:
            user_id: 用户ID
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            对话历史列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT conversation_id, username, start_time, end_time, status,
                           user_query, analysis_summary, total_iterations, final_status
                    FROM conversation_history 
                    WHERE user_id = ?
                    ORDER BY start_time DESC
                    LIMIT ? OFFSET ?
                ''', (user_id, limit, offset))
                
                rows = cursor.fetchall()
                
                conversations = []
                for row in rows:
                    conversations.append({
                        'conversation_id': row[0],
                        'username': row[1],
                        'start_time': row[2],
                        'end_time': row[3],
                        'status': row[4],
                        'user_query': row[5],
                        'analysis_summary': row[6],
                        'total_iterations': row[7],
                        'final_status': row[8]
                    })
                
                return conversations
                
        except Exception as e:
            print(f"❌ 获取对话历史失败: {e}")
            return []
    
    def get_conversation_detail(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        获取对话详情
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            对话详情字典
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM conversation_history 
                    WHERE conversation_id = ?
                ''', (conversation_id,))
                
                row = cursor.fetchone()
                
                if row:
                    # 获取列名
                    columns = [description[0] for description in cursor.description]
                    
                    # 构建结果字典
                    result = dict(zip(columns, row))
                    
                    # 解析JSON字段
                    if result.get('messages'):
                        result['messages'] = json.loads(result['messages'])
                    if result.get('tool_calls'):
                        result['tool_calls'] = json.loads(result['tool_calls'])
                    
                    return result
                
                return None
                
        except Exception as e:
            print(f"❌ 获取对话详情失败: {e}")
            return None
    
    def get_recent_conversations(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        获取最近的对话记录（用于上下文）
        
        Args:
            user_id: 用户ID
            limit: 限制数量
            
        Returns:
            最近的对话列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT conversation_id, user_query, analysis_summary, start_time
                    FROM conversation_history 
                    WHERE user_id = ? AND status = 'completed'
                    ORDER BY start_time DESC
                    LIMIT ?
                ''', (user_id, limit))
                
                rows = cursor.fetchall()
                
                conversations = []
                for row in rows:
                    conversations.append({
                        'conversation_id': row[0],
                        'user_query': row[1],
                        'analysis_summary': row[2],
                        'start_time': row[3]
                    })
                
                return conversations
                
        except Exception as e:
            print(f"❌ 获取最近对话失败: {e}")
            return []
    
    def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """
        删除对话记录
        
        Args:
            conversation_id: 对话ID
            user_id: 用户ID（用于验证权限）
            
        Returns:
            是否删除成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    DELETE FROM conversation_history 
                    WHERE conversation_id = ? AND user_id = ?
                ''', (conversation_id, user_id))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    print(f"🗑️ 删除对话记录: {conversation_id}")
                    return True
                else:
                    print(f"⚠️ 未找到对话记录或权限不足: {conversation_id}")
                    return False
                
        except Exception as e:
            print(f"❌ 删除对话记录失败: {e}")
            return False
    
    def get_conversation_stats(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户对话统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            统计信息字典
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 总对话数
                cursor.execute('''
                    SELECT COUNT(*) FROM conversation_history WHERE user_id = ?
                ''', (user_id,))
                total_conversations = cursor.fetchone()[0]
                
                # 完成的对话数
                cursor.execute('''
                    SELECT COUNT(*) FROM conversation_history 
                    WHERE user_id = ? AND status = 'completed'
                ''', (user_id,))
                completed_conversations = cursor.fetchone()[0]
                
                # 最近的对话时间
                cursor.execute('''
                    SELECT MAX(start_time) FROM conversation_history WHERE user_id = ?
                ''', (user_id,))
                last_conversation = cursor.fetchone()[0]
                
                return {
                    'total_conversations': total_conversations,
                    'completed_conversations': completed_conversations,
                    'success_rate': (completed_conversations / total_conversations * 100) if total_conversations > 0 else 0,
                    'last_conversation': last_conversation
                }
                
        except Exception as e:
            print(f"❌ 获取对话统计失败: {e}")
            return {
                'total_conversations': 0,
                'completed_conversations': 0,
                'success_rate': 0,
                'last_conversation': None
            } 