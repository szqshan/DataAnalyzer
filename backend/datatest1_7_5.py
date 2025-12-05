# P1精简版数据库分析器 - 多表支持版本
# 版本: 2.1.0 - 支持多个CSV文件上传和分析

from anthropic import Anthropic
import sqlite3
import pandas as pd
import os
from datetime import datetime
import json
import re
from typing import Dict, List, Optional, Any
import numpy as np

def convert_to_json_serializable(obj):
    """将包含numpy类型的对象转换为JSON可序列化的格式"""
    if isinstance(obj, dict):
        return {key: convert_to_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_serializable(item) for item in obj]
    elif isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif pd.isna(obj):
        return None
    else:
        return obj

class DatabaseAnalyzer:
    """P1精简版数据库分析器类 - 专注多表CSV分析功能"""
    
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
        
        self.client = Anthropic(**client_params)
        self.model_name = model_name
        self.current_db_path = None
        self.current_table_name = None  # 保持兼容性
        self.conversation_tables = []  # 当前对话中的所有表
        
        # 定义工具
        self.tools = [
            {
                "name": "query_database",
                "description": "执行SQL查询获取数据库信息，支持多表查询",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": "要执行的SQL查询语句，可以查询多个表"
                        }
                    },
                    "required": ["sql"]
                }
            },
            {
                "name": "get_table_info",
                "description": "获取当前对话中所有表的结构信息和样本数据",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
    
    def _generate_table_name(self, filename: str) -> str:
        """
        基于文件名生成唯一的表名
        
        Args:
            filename: 原始文件名
            
        Returns:
            清理后的表名
        """
        # 移除文件扩展名
        base_name = os.path.splitext(filename)[0]
        
        # 清理文件名，只保留字母、数字、中文和下划线
        cleaned_name = re.sub(r'[^\w\u4e00-\u9fff]', '_', base_name)
        cleaned_name = re.sub(r'_+', '_', cleaned_name)
        cleaned_name = cleaned_name.strip('_')
        
        # 如果名称为空或太短，使用默认名称
        if not cleaned_name or len(cleaned_name) < 2:
            cleaned_name = "data_table"
        
        # 确保表名不以数字开头（SQLite要求）
        if cleaned_name and cleaned_name[0].isdigit():
            cleaned_name = f"table_{cleaned_name}"
        
        # 添加时间戳确保唯一性
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        table_name = f"{cleaned_name}_{timestamp}"
        
        # 确保表名不超过SQLite限制
        if len(table_name) > 60:
            truncated_name = cleaned_name[:30]
            if truncated_name and truncated_name[0].isdigit():
                truncated_name = f"t_{truncated_name[1:]}"
            table_name = f"{truncated_name}_{timestamp}"
        
        # 最后检查：确保表名符合SQLite标识符规范
        if table_name and not (table_name[0].isalpha() or table_name[0] == '_'):
            table_name = f"table_{table_name}"
        
        return table_name
    
    def add_table_to_conversation(self, table_name: str, filename: str, columns: List[str], row_count: int):
        """
        将新表添加到当前对话的表列表中
        
        Args:
            table_name: 表名
            filename: 原始文件名
            columns: 列名列表
            row_count: 行数
        """
        table_info = {
            "table_name": table_name,
            "original_filename": filename,
            "columns": columns,
            "row_count": row_count,
            "created_at": datetime.now().isoformat(),
            "description": f"从文件 {filename} 导入的数据表"
        }
        
        # 检查是否已存在同名表，如果存在则更新
        existing_index = None
        for i, table in enumerate(self.conversation_tables):
            if table["table_name"] == table_name:
                existing_index = i
                break
        
        if existing_index is not None:
            self.conversation_tables[existing_index] = table_info
            print(f"📋 更新表信息: {table_name}")
        else:
            self.conversation_tables.append(table_info)
            print(f"📋 新增表信息: {table_name}")
        
        # 为了兼容性，设置current_table_name为最新的表
        self.current_table_name = table_name
        
        print(f"📊 当前对话共有 {len(self.conversation_tables)} 个数据表")
        
    def get_conversation_tables_summary(self) -> str:
        """
        获取当前对话中所有表的摘要信息
        
        Returns:
            表摘要字符串
        """
        if not self.conversation_tables:
            return "当前对话中没有数据表"
        
        summary = f"当前对话中共有 {len(self.conversation_tables)} 个数据表：\n"
        for i, table in enumerate(self.conversation_tables, 1):
            summary += f"{i}. 表名: {table['table_name']}\n"
            summary += f"   来源文件: {table['original_filename']}\n"
            summary += f"   列数: {len(table['columns'])}\n"
            summary += f"   行数: {table['row_count']}\n"
            summary += f"   创建时间: {table['created_at'][:19]}\n\n"
        
        return summary
    
    def get_conversation_tables_info(self) -> List[Dict[str, Any]]:
        """
        获取当前对话中所有表的详细信息（用于API接口）
        
        Returns:
            表信息数组
        """
        if not self.conversation_tables:
            return []
        
        tables_info = []
        for table in self.conversation_tables:
            table_info = {
                "table_name": table["table_name"],
                "original_filename": table["original_filename"],
                "row_count": table["row_count"],
                "column_count": len(table["columns"]),
                "columns": table["columns"],
                "created_at": table["created_at"],
                "description": table.get("description", f"数据表 {table['table_name']}")
            }
            tables_info.append(table_info)
        
        return convert_to_json_serializable(tables_info)
        
    def import_csv_to_sqlite(self, csv_file_path, table_name, db_path="analysis_db.db"):
        """从CSV文件创建SQLite表并导入数据 - 支持多表共存"""
        try:
            print(f"📥 开始导入CSV文件: {csv_file_path}")
            print(f"📊 目标数据库: {db_path}")
            print(f"📋 目标表名: {table_name}")
            
            if not os.path.exists(csv_file_path):
                print(f"❌ 文件不存在: {csv_file_path}")
                return {"success": False, "message": f"文件不存在: {csv_file_path}"}
            
            # 读取CSV文件
            print("📖 正在读取CSV文件...")
            try:
                # 尝试多种编码
                encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig', 'latin1']
                df = None
                used_encoding = None
                
                for encoding in encodings:
                    try:
                        df = pd.read_csv(csv_file_path, encoding=encoding)
                        used_encoding = encoding
                        print(f"✅ 使用编码 {encoding} 成功读取CSV文件")
                        break
                    except UnicodeDecodeError:
                        continue
                
                if df is None:
                    raise ValueError("无法使用常见编码读取CSV文件")
                    
                print(f"✅ 文件读取成功，共 {len(df)} 行 × {len(df.columns)} 列")
                
            except Exception as e:
                print(f"❌ 文件读取失败: {str(e)}")
                return {"success": False, "message": f"文件读取失败: {str(e)}"}
            
            # 清理列名
            df.columns = [self._clean_column_name(col) for col in df.columns]
            
            # 连接到SQLite数据库
            print(f"🔌 正在连接数据库: {db_path}")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 检查表是否已存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            table_exists = cursor.fetchone() is not None
            
            if table_exists:
                print(f"🔄 表 {table_name} 已存在，将替换数据...")
                cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
            else:
                print(f"🆕 创建新表: {table_name}")
            
            # 创建新表并导入数据
            print("📝 正在导入数据...")
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            
            # 获取导入的行数
            print("🔢 正在统计导入行数...")
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            rows_count = cursor.fetchone()[0]
            
            conn.commit()
            conn.close()
            
            # 保存当前数据库信息
            self.current_db_path = db_path
            
            # 获取原始文件名
            original_filename = os.path.basename(csv_file_path)
            
            # 添加到对话表列表
            self.add_table_to_conversation(table_name, original_filename, list(df.columns), rows_count)
            
            print(f"✅ 导入完成，共导入 {rows_count} 行数据")
            
            result = {
                "success": True,
                "message": f"成功导入 {rows_count} 行数据到表 '{table_name}'",
                "rows_imported": int(rows_count),
                "columns": list(df.columns),
                "table_name": table_name,
                "total_tables": len(self.conversation_tables),
                "file_format": ".csv"
            }
            
            return convert_to_json_serializable(result)
            
        except Exception as e:
            print(f"❌ 导入失败: {str(e)}")
            return {"success": False, "message": f"导入失败: {str(e)}"}
    
    def _clean_column_name(self, col_name):
        """清理列名"""
        cleaned = str(col_name).strip()
        cleaned = re.sub(r'[^\w\u4e00-\u9fff]', '_', cleaned)
        cleaned = re.sub(r'_+', '_', cleaned)
        cleaned = cleaned.strip('_')
        return cleaned or 'unnamed_column'

    def get_table_schema(self):
        """获取数据库中所有表的结构信息"""
        if not self.current_db_path:
            return "未连接到数据库"
        
        try:
            conn = sqlite3.connect(self.current_db_path)
            cursor = conn.cursor()
            
            # 获取所有用户数据表（排除系统表）
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name != '_db_info'
                ORDER BY name
            """)
            tables = cursor.fetchall()
            
            if not tables:
                conn.close()
                return "数据库中没有数据表"
            
            all_tables_info = []
            
            for table_row in tables:
                table_name = table_row[0]
                
                # 获取表结构
                schema_info = cursor.execute(f"PRAGMA table_info(`{table_name}`)").fetchall()
                
                # 获取样本数据
                sample_data = cursor.execute(f"SELECT * FROM `{table_name}` LIMIT 3").fetchall()
                column_names = [description[0] for description in cursor.description]
                
                # 获取行数
                row_count = cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`").fetchone()[0]
                
                # 从conversation_tables中获取更多信息
                table_meta = None
                for table_info in self.conversation_tables:
                    if table_info["table_name"] == table_name:
                        table_meta = table_info
                        break
                
                table_schema = {
                    "table_name": table_name,
                    "original_filename": table_meta["original_filename"] if table_meta else "未知",
                    "description": table_meta["description"] if table_meta else f"数据表 {table_name}",
                    "columns": [{"name": col[1], "type": col[2]} for col in schema_info],
                    "row_count": row_count,
                    "sample_data": [dict(zip(column_names, row)) for row in sample_data],
                    "created_at": table_meta["created_at"] if table_meta else "未知"
                }
                
                all_tables_info.append(table_schema)
            
            conn.close()
            
            # 构建综合信息
            result = {
                "database_path": self.current_db_path,
                "total_tables": len(all_tables_info),
                "tables": all_tables_info,
                "summary": self.get_conversation_tables_summary()
            }
            
            return result
            
        except Exception as e:
            return f"获取表结构失败: {str(e)}"

    def clear_conversation_tables(self):
        """清空当前对话的表列表（新对话时调用）"""
        self.conversation_tables = []
        self.current_table_name = None
        print("🧹 已清空对话表列表")
    
    def _sync_tables_from_database(self):
        """
        从数据库中同步表列表到conversation_tables
        用于切换对话时重新加载表信息
        """
        if not self.current_db_path:
            return
        
        try:
            conn = sqlite3.connect(self.current_db_path)
            cursor = conn.cursor()
            
            # 获取所有用户数据表
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name != '_db_info'
                ORDER BY name
            """)
            tables = cursor.fetchall()
            
            # 清空现有列表
            self.conversation_tables = []
            
            for table_row in tables:
                table_name = table_row[0]
                
                # 获取表信息
                cursor.execute(f"PRAGMA table_info(`{table_name}`)")
                columns_info = cursor.fetchall()
                columns = [col[1] for col in columns_info]
                
                cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                row_count = cursor.fetchone()[0]
                
                # 尝试从表名推断原始文件名
                original_filename = "未知文件"
                if "_" in table_name:
                    # 移除时间戳部分
                    parts = table_name.split("_")
                    if len(parts) >= 2:
                        # 假设最后一个或两个部分是时间戳
                        name_parts = parts[:-1] if len(parts[-1]) == 6 else parts[:-2]
                        original_filename = "_".join(name_parts) + ".csv"
                
                table_info = {
                    "table_name": table_name,
                    "original_filename": original_filename,
                    "columns": columns,
                    "row_count": row_count,
                    "created_at": "未知",  # 切换对话时无法获取准确的创建时间
                    "description": f"数据表 {table_name}"
                }
                
                self.conversation_tables.append(table_info)
            
            conn.close()
            
            # 设置current_table_name为最新的表（如果有的话）
            if self.conversation_tables:
                self.current_table_name = self.conversation_tables[-1]["table_name"]
            
            print(f"🔄 已同步 {len(self.conversation_tables)} 个表到对话列表")
            
        except Exception as e:
            print(f"⚠️ 同步表列表失败: {e}")
            self.conversation_tables = []
        
    def query_database(self, sql):
        """执行SQL查询 - 支持多表查询"""
        if not self.current_db_path:
            return {"error": "未连接到数据库"}
        
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
                    "success": True,
                    "columns": columns,
                    "data": results,
                    "row_count": len(results),
                    "execution_time": execution_time,
                    "sql": sql
                }
            else:
                conn.commit()
                result_data = {
                    "success": True,
                    "message": f"SQL执行成功，影响行数: {cursor.rowcount}",
                    "execution_time": execution_time,
                    "sql": sql
                }
            
            conn.close()
            return result_data
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "sql": sql
            }
    
    def execute_tool(self, tool_name, tool_input):
        """执行工具调用"""
        if tool_name == "query_database":
            return self.query_database(tool_input["sql"])
        elif tool_name == "get_table_info":
            return self.get_table_schema()
        else:
            return {"error": f"未知工具: {tool_name}"}
    
    def _clear_analysis_db(self, db_path):
        """清空分析数据库（新对话时调用）"""
        try:
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # 获取所有用户创建的表
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name != '_db_info'
                """)
                tables = cursor.fetchall()
                
                # 删除所有用户表
                for table in tables:
                    cursor.execute(f"DROP TABLE IF EXISTS `{table[0]}`")
                    print(f"🗑️ 删除表: {table[0]}")
                
                conn.commit()
                conn.close()
                print(f"🧹 已清空数据库: {db_path}")
                
        except Exception as e:
            print(f"⚠️ 清空数据库失败: {e}")
    
    def analyze_with_claude(self, query, conversation_id=None):
        """使用Claude进行数据分析"""
        try:
            # 构建系统提示词
            system_prompt = f"""你是一个专业的数据分析师，专门帮助用户分析SQLite数据库中的数据。

当前数据库信息：
{self.get_conversation_tables_summary()}

你有以下工具可以使用：
1. query_database: 执行SQL查询获取数据
2. get_table_info: 获取表结构信息

请根据用户的问题，使用合适的工具进行数据分析，并提供清晰、准确的分析结果。
支持多表查询，可以使用JOIN、UNION等SQL操作进行跨表分析。

注意：
- 在SQL查询中使用反引号包围表名，如 `table_name`
- 提供具体的数据洞察和建议
- 如果需要多个查询，请分步骤进行
- 确保查询结果的准确性和完整性
"""
            
            # 构建消息
            messages = [
                {
                    "role": "user",
                    "content": query
                }
            ]
            
            # 调用Claude API
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=4000,
                temperature=0.1,
                system=system_prompt,
                messages=messages,
                tools=self.tools
            )
            
            # 处理响应
            result = {
                "response": response.content[0].text if response.content else "",
                "tool_calls": [],
                "conversation_id": conversation_id
            }
            
            # 处理工具调用
            if hasattr(response, 'tool_calls') and response.tool_calls:
                for tool_call in response.tool_calls:
                    tool_result = self.execute_tool(tool_call.name, tool_call.input)
                    result["tool_calls"].append({
                        "tool": tool_call.name,
                        "input": tool_call.input,
                        "result": tool_result
                    })
            
            return result
            
        except Exception as e:
            return {
                "error": f"分析失败: {str(e)}",
                "conversation_id": conversation_id
            }
    
    def delete_table(self, table_name: str) -> Dict[str, Any]:
        """
        删除指定的数据表
        
        Args:
            table_name: 要删除的表名
            
        Returns:
            包含操作结果的字典
        """
        if not self.current_db_path:
            return {
                "success": False,
                "message": "未连接到数据库"
            }
        
        if not table_name:
            return {
                "success": False,
                "message": "表名不能为空"
            }
        
        try:
            conn = sqlite3.connect(self.current_db_path)
            cursor = conn.cursor()
            
            # 首先检查表是否存在
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name = ? AND name NOT LIKE 'sqlite_%' AND name != '_db_info'
            """, (table_name,))
            
            table_exists = cursor.fetchone()
            if not table_exists:
                conn.close()
                return {
                    "success": False,
                    "message": f"表 '{table_name}' 不存在"
                }
            
            # 获取表的行数（用于返回删除信息）
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            row_count = cursor.fetchone()[0]
            
            # 删除表
            cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
            conn.commit()
            
            # 从conversation_tables列表中移除该表
            self.conversation_tables = [
                table for table in self.conversation_tables 
                if table["table_name"] != table_name
            ]
            
            # 如果删除的是当前表，更新current_table_name
            if self.current_table_name == table_name:
                if self.conversation_tables:
                    self.current_table_name = self.conversation_tables[-1]["table_name"]
                else:
                    self.current_table_name = None
            
            conn.close()
            
            print(f"🗑️ 已删除表: {table_name} (包含 {row_count} 行数据)")
            
            return {
                "success": True,
                "message": f"表 '{table_name}' 删除成功",
                "deleted_table": table_name,
                "deleted_rows": row_count,
                "remaining_tables": len(self.conversation_tables)
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"删除表失败: {str(e)}"
            }