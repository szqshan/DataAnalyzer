import sqlite3
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from prompts import Prompts

class TemplateManager:
    """模板管理器 - 负责报告模板的生成、存储和管理"""
    
    def __init__(self, user_paths: Dict[str, Path], user_id: str, analyzer=None):
        self.user_paths = user_paths
        self.user_id = user_id
        self.analyzer = analyzer  # 需要 DatabaseAnalyzer 实例来调用 AI
        self.db_path = user_paths['user_dir'] / "templates.db"
        self._init_database()
        
    def _init_database(self):
        """初始化模板数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS report_templates (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        description TEXT,
                        vue_template TEXT NOT NULL,
                        data_schema TEXT NOT NULL,
                        chart_config TEXT,
                        source_conversation_id TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
        except Exception as e:
            logging.error(f"初始化模板数据库失败: {e}")
            
    def generate_template_from_report(self, html_content: str, conversation_context: str = "") -> Dict[str, Any]:
        """
        从现有的 HTML 报告生成 Vue 模板和 JSON Schema
        
        Args:
            html_content: 原始 HTML 报告内容
            conversation_context: 对话上下文（帮助 AI 理解数据含义）
            
        Returns:
            包含 vue_template, data_schema, name, description 的字典
        """
        if not self.analyzer:
            raise ValueError("TemplateManager 需要 DatabaseAnalyzer 实例才能生成模板")
            
        try:
            # 1. 构建 Prompt
            system_prompt = Prompts.TEMPLATE_EXTRACTION_SYSTEM_PROMPT
            
            user_message = f"""
请分析以下 HTML 报告，将其转换为 Vue 模板和 JSON 数据结构定义。

HTML 报告内容:
{html_content}

上下文信息:
{conversation_context}

请严格按照 System Prompt 的要求返回 JSON 格式结果。
"""
            
            # 2. 调用 AI
            # 使用非流式调用，因为我们需要完整的 JSON
            messages = [{"role": "user", "content": user_message}]
            
            response = self.analyzer.client.messages.create(
                model=self.analyzer.model_name,
                max_tokens=4000,
                temperature=0.1, # 降低随机性，保证结构准确
                system=system_prompt,
                messages=messages
            )
            
            ai_content = response.content[0].text
            
            # 3. 解析 JSON
            # AI 可能会返回 markdown 代码块，需要清理
            json_str = ai_content.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.startswith("```"):
                json_str = json_str[3:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
                
            template_data = json.loads(json_str.strip())
            
            return template_data
            
        except Exception as e:
            logging.error(f"生成模板失败: {e}")
            raise
            
    def save_template(self, template_data: Dict[str, Any], source_conversation_id: str = None) -> str:
        """保存模板到数据库"""
        try:
            template_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO report_templates 
                    (id, user_id, name, description, vue_template, data_schema, chart_config, source_conversation_id, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    template_id,
                    self.user_id,
                    template_data.get('name', '未命名模板'),
                    template_data.get('description', ''),
                    template_data.get('vue_template', ''),
                    json.dumps(template_data.get('data_schema', {}), ensure_ascii=False),
                    json.dumps(template_data.get('chart_config', {}), ensure_ascii=False),
                    source_conversation_id,
                    now,
                    now
                ))
                conn.commit()
                
            return template_id
            
        except Exception as e:
            logging.error(f"保存模板失败: {e}")
            raise

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """获取指定模板"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM report_templates WHERE id = ? AND user_id = ?', (template_id, self.user_id))
                row = cursor.fetchone()
                
                if row:
                    return {
                        'id': row['id'],
                        'name': row['name'],
                        'description': row['description'],
                        'vue_template': row['vue_template'],
                        'data_schema': json.loads(row['data_schema']),
                        'chart_config': json.loads(row['chart_config']) if row['chart_config'] else {},
                        'created_at': row['created_at']
                    }
                return None
        except Exception as e:
            logging.error(f"获取模板失败: {e}")
            return None

    def list_templates(self) -> List[Dict[str, Any]]:
        """列出用户的所有模板"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT id, name, description, created_at FROM report_templates WHERE user_id = ? ORDER BY created_at DESC', (self.user_id,))
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
        except Exception as e:
            logging.error(f"列出模板失败: {e}")
            return []

    def delete_template(self, template_id: str) -> bool:
        """删除模板"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM report_templates WHERE id = ? AND user_id = ?', (template_id, self.user_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"删除模板失败: {e}")
            return False
