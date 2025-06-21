# conversation_history.py - 对话历史记录管理器
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import uuid
import logging

class ConversationHistoryManager:
    """对话历史记录管理器 - 存储用户查询历史"""
    
    def __init__(self, user_paths: Dict[str, Path], user_id: str):
        """
        初始化历史记录管理器
        
        Args:
            user_paths: 用户路径字典，包含各种目录路径
            user_id: 用户ID
        """
        self.user_paths = user_paths
        self.user_id = user_id
        self.current_conversation_id = None
        self.ai_complete_response = ""  # 存储完整AI响应
        
        # 多对话管理相关
        self.conversations_meta_file = user_paths['user_dir'] / f"{user_id}_conversations.json"
        self._init_database()
        self._load_conversations_meta()
        
        # 确保当前对话ID正确设置
        if self.conversations_meta.get('current_conversation_id'):
            # 验证当前对话是否仍然存在
            current_id = self.conversations_meta['current_conversation_id']
            if current_id in self.conversations_meta['conversations']:
                self.current_conversation_id = current_id
                # 设置数据库路径
                conv_info = self.conversations_meta['conversations'][current_id]
                self.db_path = Path(conv_info['history_path'])
            else:
                # 当前对话不存在，清除它
                self.conversations_meta['current_conversation_id'] = None
                self._save_conversations_meta()
        
        logging.info(f"📚 对话历史记录管理器已初始化（多对话版）")
    
    def _load_conversations_meta(self):
        """加载对话元数据"""
        try:
            if self.conversations_meta_file.exists():
                with open(self.conversations_meta_file, 'r', encoding='utf-8') as f:
                    self.conversations_meta = json.load(f)
            else:
                self.conversations_meta = {
                    "conversations": {},
                    "current_conversation_id": None,
                    "last_updated": datetime.now().isoformat()
                }
        except Exception as e:
            logging.error(f"加载对话元数据时出错: {e}")
            self.conversations_meta = {
                "conversations": {},
                "current_conversation_id": None,
                "last_updated": datetime.now().isoformat()
            }
    
    def _save_conversations_meta(self):
        """保存对话元数据"""
        try:
            self.conversations_meta["last_updated"] = datetime.now().isoformat()
            with open(self.conversations_meta_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversations_meta, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"保存对话元数据时出错: {e}")
    
    def create_new_conversation(self, user_data: Dict[str, str], conversation_name: str = None, description: str = None, analyzer=None) -> Dict[str, Any]:
        """
        创建新的对话
        
        Args:
            user_data: 用户信息
            conversation_name: 对话名称（可选）
            description: 对话描述（可选）
            analyzer: 数据分析器实例（可选，用于清空表列表）
            
        Returns:
            新对话信息
        """
        try:
            # 清除analysis.db中的旧数据
            self._clear_analysis_db()
            
            # 如果提供了analyzer，清空其表列表
            if analyzer:
                analyzer.clear_conversation_tables()
            
            # 生成对话ID和时间戳
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            conversation_id = f"conv_{timestamp}"
            
            # 生成文件路径
            user_id = user_data['user_id']
            db_filename = f"{user_id}_{timestamp}_{conversation_id}.db"
            history_filename = f"{user_id}_{timestamp}_{conversation_id}_history.db"
            
            db_path = self.user_paths['user_dir'] / db_filename
            history_path = self.user_paths['user_dir'] / history_filename
            
            # 创建对话信息
            conversation_info = {
                "conversation_id": conversation_id,
                "conversation_name": conversation_name or f"对话 {len(self.conversations_meta['conversations']) + 1}",
                "description": description or "",
                "created_time": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
                "status": "active",
                "db_path": str(db_path),
                "history_path": str(history_path),
                "message_count": 0,
                "user_id": user_id,
                "username": user_data['username']
            }
            
            # 初始化数据库文件
            self._init_conversation_database(history_path)
            
            # 更新元数据
            self.conversations_meta['conversations'][conversation_id] = conversation_info
            self.conversations_meta['current_conversation_id'] = conversation_id
            self._save_conversations_meta()
            
            # 设置当前对话
            self.current_conversation_id = conversation_id
            self.db_path = history_path
            
            logging.info(f"新对话创建成功: {conversation_id}")
            return conversation_info
            
        except Exception as e:
            logging.error(f"创建新对话时出错: {e}")
            raise
    
    def get_conversations_list(self, user_id: str) -> List[Dict[str, Any]]:
        """
        获取用户对话列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            对话列表
        """
        try:
            conversations = []
            for conv_id, conv_info in self.conversations_meta['conversations'].items():
                if conv_info['user_id'] == user_id:
                    # 获取消息数量
                    if Path(conv_info['history_path']).exists():
                        try:
                            with sqlite3.connect(conv_info['history_path']) as conn:
                                cursor = conn.cursor()
                                cursor.execute('SELECT COUNT(*) FROM conversation_history')
                                conv_info['message_count'] = cursor.fetchone()[0]
                        except:
                            conv_info['message_count'] = 0
                    
                    conversations.append(conv_info)
            
            # 按最后活动时间排序
            conversations.sort(key=lambda x: x['last_activity'], reverse=True)
            return conversations
            
        except Exception as e:
            logging.error(f"获取对话列表时出错: {e}")
            return []
    
    def switch_conversation(self, conversation_id: str, user_id: str) -> bool:
        """
        切换到指定对话
        
        Args:
            conversation_id: 对话ID
            user_id: 用户ID
            
        Returns:
            是否切换成功
        """
        try:
            if conversation_id not in self.conversations_meta['conversations']:
                return False
            
            conv_info = self.conversations_meta['conversations'][conversation_id]
            if conv_info['user_id'] != user_id:
                return False
            
            # 更新最后活动时间
            conv_info['last_activity'] = datetime.now().isoformat()
            
            # 切换对话
            self.current_conversation_id = conversation_id
            self.db_path = Path(conv_info['history_path'])
            self.conversations_meta['current_conversation_id'] = conversation_id
            
            # 保存元数据
            self._save_conversations_meta()
            
            logging.info(f"切换对话成功: {conversation_id}")
            return True
            
        except Exception as e:
            logging.error(f"切换对话时出错: {e}")
            return False
    
    def get_current_conversation_info(self) -> Optional[Dict[str, Any]]:
        """获取当前对话信息，包含消息历史"""
        if self.current_conversation_id and self.current_conversation_id in self.conversations_meta['conversations']:
            conv_info = self.conversations_meta['conversations'][self.current_conversation_id].copy()
            
            # 从数据库加载消息历史
            try:
                if hasattr(self, 'db_path') and self.db_path and Path(self.db_path).exists():
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute('''
                            SELECT messages FROM conversation_history 
                            WHERE conversation_id = ?
                        ''', (self.current_conversation_id,))
                        result = cursor.fetchone()
                        
                        if result and result[0]:
                            conv_info['messages'] = json.loads(result[0])
                            logging.info(f"📚 已加载 {len(conv_info['messages'])} 条消息历史")
                        else:
                            conv_info['messages'] = []
                            logging.info(f"📚 当前对话暂无消息历史")
                else:
                    conv_info['messages'] = []
                    logging.warning(f"📚 数据库路径不存在，无法加载消息历史")
            except Exception as e:
                logging.error(f"❌ 加载消息历史失败: {e}")
                conv_info['messages'] = []
            
            return conv_info
        return None
    
    def _init_conversation_database(self, db_path: Path):
        """初始化对话数据库"""
        try:
            with sqlite3.connect(db_path) as conn:
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
                
        except Exception as e:
            logging.error(f"初始化对话数据库时出错: {e}")
            raise
    
    def _init_database(self):
        """初始化数据库表结构 - 兼容旧版本"""
        # 这个方法现在主要用于兼容性，实际初始化在_create_new_conversation中完成
        pass
    
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
        # 如果没有当前对话，创建一个新的
        if not self.current_conversation_id:
            self.create_new_conversation(user_data)
        
        conversation_id = self.current_conversation_id
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
                return conversation_id
                
        except Exception as e:
            logging.error(f"开始新对话时出错: {e}")
            raise
    
    def update_conversation_messages(self, conversation_id: str, messages: list):
        """
        更新对话消息历史，所有消息content字段都应为数组结构
        """
        try:
            # 兼容旧数据，自动转换
            for msg in messages:
                if isinstance(msg.get("content"), str):
                    msg["content"] = [{"type": "text", "text": msg["content"]}]
                elif not isinstance(msg.get("content"), list):
                    msg["content"] = [{"type": "text", "text": str(msg["content"]) }]
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                messages_json = json.dumps(messages, ensure_ascii=False, indent=2)
                cursor.execute('''UPDATE conversation_history SET messages = ? WHERE conversation_id = ?''', (messages_json, conversation_id))
                conn.commit()
        except Exception as e:
            logging.error(f"更新对话消息历史时出错: {e}")
    
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
                
        except Exception as e:
            logging.error(f"更新工具调用记录时出错: {e}")
    
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
                
        except Exception as e:
            logging.error(f"完成对话记录时出错: {e}")
    
    def get_conversation_history(self, user_id: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取用户对话历史记录
        
        Args:
            user_id: 用户ID
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            对话历史记录列表
        """
        try:
            # 获取所有对话的历史记录
            all_history = []
            
            for conv_id, conv_info in self.conversations_meta['conversations'].items():
                if conv_info['user_id'] == user_id and Path(conv_info['history_path']).exists():
                    try:
                        with sqlite3.connect(conv_info['history_path']) as conn:
                            cursor = conn.cursor()
                            
                            cursor.execute('''
                                SELECT conversation_id, user_id, username, start_time, end_time,
                                       status, user_query, system_prompt, database_path, table_name,
                                       messages, tool_calls, analysis_summary, total_iterations,
                                       final_status, created_at
                                FROM conversation_history
                                ORDER BY start_time DESC
                            ''')
                            
                            rows = cursor.fetchall()
                            for row in rows:
                                all_history.append({
                                    'conversation_id': row[0],
                                    'user_id': row[1],
                                    'username': row[2],
                                    'start_time': row[3],
                                    'end_time': row[4],
                                    'status': row[5],
                                    'user_query': row[6],
                                    'system_prompt': row[7],
                                    'database_path': row[8],
                                    'table_name': row[9],
                                    'messages': json.loads(row[10]) if row[10] else [],
                                    'tool_calls': json.loads(row[11]) if row[11] else [],
                                    'analysis_summary': row[12],
                                    'total_iterations': row[13],
                                    'final_status': row[14],
                                    'created_at': row[15],
                                    'conversation_name': conv_info['conversation_name'],
                                    'conversation_description': conv_info['description']
                                })
                    except Exception as e:
                        continue
            
            # 按开始时间排序并分页
            all_history.sort(key=lambda x: x['start_time'], reverse=True)
            return all_history[offset:offset + limit]
            
        except Exception as e:
            logging.error(f"获取对话历史记录时出错: {e}")
            return []
    
    def get_conversation_detail(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        获取特定对话的详细信息
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            对话详细信息
        """
        try:
            if conversation_id not in self.conversations_meta['conversations']:
                return None
            
            conv_info = self.conversations_meta['conversations'][conversation_id]
            history_path = Path(conv_info['history_path'])
            
            if not history_path.exists():
                return None
            
            with sqlite3.connect(history_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT conversation_id, user_id, username, start_time, end_time,
                           status, user_query, system_prompt, database_path, table_name,
                           messages, tool_calls, analysis_summary, total_iterations,
                           final_status, created_at
                    FROM conversation_history
                    WHERE conversation_id = ?
                ''', (conversation_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'conversation_id': row[0],
                        'user_id': row[1],
                        'username': row[2],
                        'start_time': row[3],
                        'end_time': row[4],
                        'status': row[5],
                        'user_query': row[6],
                        'system_prompt': row[7],
                        'database_path': row[8],
                        'table_name': row[9],
                        'messages': json.loads(row[10]) if row[10] else [],
                        'tool_calls': json.loads(row[11]) if row[11] else [],
                        'analysis_summary': row[12],
                        'total_iterations': row[13],
                        'final_status': row[14],
                        'created_at': row[15],
                        'conversation_name': conv_info['conversation_name'],
                        'conversation_description': conv_info['description']
                    }
            
            return None
            
        except Exception as e:
            logging.error(f"获取对话详细信息时出错: {e}")
            return None
    
    def get_recent_conversations(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        获取用户最近的对话记录
        
        Args:
            user_id: 用户ID
            limit: 限制数量
            
        Returns:
            最近对话记录列表
        """
        try:
            # 获取所有对话的最近记录
            all_recent = []
            
            for conv_id, conv_info in self.conversations_meta['conversations'].items():
                if conv_info['user_id'] == user_id and Path(conv_info['history_path']).exists():
                    try:
                        with sqlite3.connect(conv_info['history_path']) as conn:
                            cursor = conn.cursor()
                            
                            cursor.execute('''
                                SELECT conversation_id, user_query, start_time, status, 
                                       analysis_summary, total_iterations
                                FROM conversation_history
                                ORDER BY start_time DESC
                                LIMIT 1
                            ''')
                            
                            row = cursor.fetchone()
                            if row:
                                all_recent.append({
                                    'conversation_id': row[0],
                                    'user_query': row[1],
                                    'start_time': row[2],
                                    'status': row[3],
                                    'analysis_summary': row[4],
                                    'total_iterations': row[5],
                                    'conversation_name': conv_info['conversation_name'],
                                    'conversation_description': conv_info['description'],
                                    'last_activity': conv_info['last_activity']
                                })
                    except Exception as e:
                        continue
            
            # 按最后活动时间排序
            all_recent.sort(key=lambda x: x['last_activity'], reverse=True)
            return all_recent[:limit]
            
        except Exception as e:
            logging.error(f"获取最近对话记录时出错: {e}")
            return []
    
    def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """
        删除对话
        
        Args:
            conversation_id: 对话ID
            user_id: 用户ID
            
        Returns:
            是否删除成功
        """
        try:
            if conversation_id not in self.conversations_meta['conversations']:
                return False
            
            conv_info = self.conversations_meta['conversations'][conversation_id]
            if conv_info['user_id'] != user_id:
                return False
            
            # 如果删除的是当前对话，先清空当前对话状态，释放文件占用
            if self.current_conversation_id == conversation_id:
                self.current_conversation_id = None
                self.db_path = None
                self.conversations_meta['current_conversation_id'] = None
                logging.info(f"清空当前对话状态，准备删除: {conversation_id}")
            
            # 强制关闭可能的数据库连接
            import gc
            gc.collect()
            
            # 删除数据库文件
            history_path = Path(conv_info['history_path'])
            if history_path.exists():
                try:
                    history_path.unlink()
                    logging.info(f"删除历史数据库文件: {history_path}")
                except PermissionError as e:
                    logging.warning(f"无法删除历史数据库文件 {history_path}: {e}")
                    # 如果无法删除，尝试重命名为.deleted后缀
                    try:
                        deleted_path = history_path.with_suffix('.deleted')
                        history_path.rename(deleted_path)
                        logging.info(f"文件重命名为: {deleted_path}")
                    except Exception as rename_error:
                        logging.error(f"重命名文件也失败: {rename_error}")
            
            # 删除数据库文件（如果存在）
            db_path = Path(conv_info['db_path'])
            if db_path.exists():
                try:
                    db_path.unlink()
                    logging.info(f"删除数据库文件: {db_path}")
                except PermissionError as e:
                    logging.warning(f"无法删除数据库文件 {db_path}: {e}")
                    # 如果无法删除，尝试重命名为.deleted后缀
                    try:
                        deleted_path = db_path.with_suffix('.deleted')
                        db_path.rename(deleted_path)
                        logging.info(f"文件重命名为: {deleted_path}")
                    except Exception as rename_error:
                        logging.error(f"重命名文件也失败: {rename_error}")
            
            # 从元数据中删除
            del self.conversations_meta['conversations'][conversation_id]
            
            # 保存元数据
            self._save_conversations_meta()
            
            logging.info(f"对话删除成功: {conversation_id}")
            return True
            
        except Exception as e:
            logging.error(f"删除对话时出错: {e}")
            return False
    
    def get_conversation_stats(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户对话统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            统计信息
        """
        try:
            total_conversations = 0
            total_messages = 0
            completed_conversations = 0
            error_conversations = 0
            
            for conv_id, conv_info in self.conversations_meta['conversations'].items():
                if conv_info['user_id'] == user_id:
                    total_conversations += 1
                    
                    if Path(conv_info['history_path']).exists():
                        try:
                            with sqlite3.connect(conv_info['history_path']) as conn:
                                cursor = conn.cursor()
                                
                                # 统计消息数量
                                cursor.execute('SELECT COUNT(*) FROM conversation_history')
                                message_count = cursor.fetchone()[0]
                                total_messages += message_count
                                
                                # 统计状态
                                cursor.execute('''
                                    SELECT status, COUNT(*) 
                                    FROM conversation_history 
                                    GROUP BY status
                                ''')
                                
                                for status, count in cursor.fetchall():
                                    if status == 'completed':
                                        completed_conversations += count
                                    elif status in ['error', 'interrupted']:
                                        error_conversations += count
                        except Exception as e:
                            continue
            
            return {
                'total_conversations': total_conversations,
                'total_messages': total_messages,
                'completed_conversations': completed_conversations,
                'error_conversations': error_conversations,
                'success_rate': (completed_conversations / total_conversations * 100) if total_conversations > 0 else 0
            }
            
        except Exception as e:
            logging.error(f"获取对话统计信息时出错: {e}")
            return {
                'total_conversations': 0,
                'total_messages': 0,
                'completed_conversations': 0,
                'error_conversations': 0,
                'success_rate': 0
            }

    def append_message(self, conversation_id: str, role: str, content, timestamp: str = None):
        """
        向指定对话追加一条消息，自动生成唯一ID
        Args:
            conversation_id: 对话ID
            role: 消息角色（user/assistant/tool）
            content: 消息内容（数组或字符串）
            timestamp: 时间戳（可选）
        """
        try:
            if not timestamp:
                from datetime import datetime
                timestamp = datetime.now().isoformat()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''SELECT messages FROM conversation_history WHERE conversation_id = ?''', (conversation_id,))
                row = cursor.fetchone()
                if row:
                    messages = json.loads(row[0]) if row[0] else []
                else:
                    messages = []
                # 生成唯一ID
                msg_id = str(uuid.uuid4())
                # 统一content为数组结构
                if isinstance(content, str):
                    content_arr = [{"type": "text", "text": content}]
                elif isinstance(content, list):
                    content_arr = content
                else:
                    content_arr = [{"type": "text", "text": str(content)}]
                new_msg = {
                    "id": msg_id,
                    "role": role,
                    "content": content_arr,
                    "timestamp": timestamp
                }
                messages.append(new_msg)
                messages_json = json.dumps(messages, ensure_ascii=False, indent=2)
                cursor.execute('''UPDATE conversation_history SET messages = ? WHERE conversation_id = ?''', (messages_json, conversation_id))
                conn.commit()
                return msg_id
        except Exception as e:
            logging.error(f"向指定对话追加一条消息时出错: {e}")
            return None

    def edit_message(self, conversation_id: str, message_id: str, new_content):
        """
        编辑指定消息内容，支持富文本结构
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''SELECT messages FROM conversation_history WHERE conversation_id = ?''', (conversation_id,))
                row = cursor.fetchone()
                if row:
                    messages = json.loads(row[0]) if row[0] else []
                else:
                    messages = []
                for msg in messages:
                    if msg["id"] == message_id:
                        # 只支持编辑第一个text段
                        if isinstance(new_content, str):
                            for block in msg["content"]:
                                if block["type"] == "text":
                                    block["text"] = new_content
                                    break
                        elif isinstance(new_content, list):
                            msg["content"] = new_content
                        else:
                            for block in msg["content"]:
                                if block["type"] == "text":
                                    block["text"] = str(new_content)
                                    break
                        break
                messages_json = json.dumps(messages, ensure_ascii=False, indent=2)
                cursor.execute('''UPDATE conversation_history SET messages = ? WHERE conversation_id = ?''', (messages_json, conversation_id))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"编辑指定消息内容时出错: {e}")
            return False

    def delete_message(self, conversation_id: str, message_id: str):
        """
        撤回/删除指定消息
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''SELECT messages FROM conversation_history WHERE conversation_id = ?''', (conversation_id,))
                row = cursor.fetchone()
                if row:
                    messages = json.loads(row[0]) if row[0] else []
                else:
                    messages = []
                messages = [msg for msg in messages if msg["id"] != message_id]
                messages_json = json.dumps(messages, ensure_ascii=False, indent=2)
                cursor.execute('''UPDATE conversation_history SET messages = ? WHERE conversation_id = ?''', (messages_json, conversation_id))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"撤回/删除指定消息时出错: {e}")
            return False 
    
    def _clear_analysis_db(self):
        """
        重置analysis.db文件
        在创建新对话时调用，确保数据隔离
        """
        try:
            import sqlite3
            import os
            
            # 获取analysis.db路径
            analysis_db_path = self.user_paths['db_path']
            
            logging.info(f"🧹 正在重置analysis.db文件: {analysis_db_path}")
            
            # 方法1: 如果文件存在，先删除它
            if analysis_db_path.exists():
                try:
                    os.remove(analysis_db_path)
                    logging.info("✅ 已删除旧的analysis.db文件")
                except Exception as e:
                    logging.warning(f"⚠️ 删除旧文件失败: {e}")
                    # 如果删除失败，尝试清空所有表
                    try:
                        with sqlite3.connect(analysis_db_path) as conn:
                            cursor = conn.cursor()
                            
                            # 获取所有表名
                            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                            tables = cursor.fetchall()
                            
                            if tables:
                                logging.info(f"🗑️ 正在删除 {len(tables)} 个表")
                                
                                # 删除所有用户数据表
                                for table in tables:
                                    table_name = table[0]
                                    try:
                                        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                                        logging.info(f"✅ 已删除表: {table_name}")
                                    except Exception as e:
                                        logging.warning(f"⚠️ 删除表 {table_name} 时出错: {e}")
                                
                                conn.commit()
                                logging.info("🎉 表清除完成")
                    except Exception as e:
                        logging.error(f"❌ 清空表失败: {e}")
            
            # 方法2: 创建一个全新的空数据库文件
            try:
                with sqlite3.connect(analysis_db_path) as conn:
                    cursor = conn.cursor()
                    # 创建一个简单的元数据表来标记数据库已初始化
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS _db_info (
                            key TEXT PRIMARY KEY,
                            value TEXT,
                            created_at TEXT DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    cursor.execute('''
                        INSERT OR REPLACE INTO _db_info (key, value) 
                        VALUES ('reset_time', ?)
                    ''', (datetime.now().isoformat(),))
                    conn.commit()
                
                logging.info("🎉 analysis.db重置完成，新对话数据已隔离")
                
            except Exception as e:
                logging.error(f"❌ 创建新数据库失败: {e}")
                    
        except Exception as e:
            logging.error(f"❌ 重置analysis.db时出错: {e}")
            # 不抛出异常，避免影响对话创建