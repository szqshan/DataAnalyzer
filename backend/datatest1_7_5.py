# P1精简版数据库分析器 - 清理调试输出
# 版本: 3.1.0 - P1阶段精简版 - 多表支持

from anthropic import Anthropic
import sqlite3
import pandas as pd
import os
from datetime import datetime
import json
import re
from typing import Dict, List, Optional, Any
try:
    from .data_processor import DataProcessor
except ImportError:
    from data_processor import DataProcessor

class DatabaseAnalyzer:
    """P1精简版数据库分析器类 - 专注核心数据处理功能，支持多表管理"""
    
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
        self.conversation_tables = []  # 新增：当前对话中的所有表
        self.data_processor = DataProcessor()  # 新增：数据处理器
        
        # 定义工具 - 使用正确的格式
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
        
        # 添加时间戳确保唯一性
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        table_name = f"{cleaned_name}_{timestamp}"
        
        # 确保表名不超过SQLite限制（通常为64字符）
        if len(table_name) > 60:
            table_name = f"{cleaned_name[:30]}_{timestamp}"
        
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
        
    def import_file_to_sqlite(self, file_path, table_name, db_path="analysis_db.db", processing_options=None):
        """从多种格式文件创建SQLite表并导入数据 - 支持多表共存和数据处理"""
        try:
            print(f"📥 开始导入文件: {file_path}")
            print(f"📊 目标数据库: {db_path}")
            print(f"📋 目标表名: {table_name}")
            
            if not os.path.exists(file_path):
                print(f"❌ 文件不存在: {file_path}")
                return {"success": False, "message": f"文件不存在: {file_path}"}
            
            # 检测文件格式
            try:
                file_format = self.data_processor.detect_file_format(file_path)
                print(f"📋 检测到文件格式: {file_format}")
            except ValueError as e:
                print(f"❌ {str(e)}")
                return {"success": False, "message": str(e)}
            
            # 读取文件
            print("📖 正在读取文件...")
            try:
                df = self.data_processor.read_file(file_path)
                print(f"✅ 文件读取成功，共 {len(df)} 行 × {len(df.columns)} 列")
            except Exception as e:
                print(f"❌ 文件读取失败: {str(e)}")
                return {"success": False, "message": f"文件读取失败: {str(e)}"}
            
            # 数据质量评估
            print("🔍 开始数据质量评估...")
            quality_report = self.data_processor.assess_data_quality(df)
            
            # 数据清洗（如果启用）
            cleaning_log = None
            if processing_options is None:
                processing_options = {"enable_cleaning": True}
            
            if processing_options.get("enable_cleaning", True):
                print("🧹 开始数据清洗...")
                cleaning_options = processing_options.get("cleaning_options", {})
                df, cleaning_log = self.data_processor.clean_data(df, cleaning_options)
                print(f"✅ 数据清洗完成")
            
            # 连接到SQLite数据库
            print(f"🔌 正在连接数据库: {db_path}")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 检查表是否已存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            table_exists = cursor.fetchone() is not None
            
            if table_exists:
                print(f"🔄 表 {table_name} 已存在，将替换数据...")
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            else:
                print(f"🆕 创建新表: {table_name}")
            
            # 创建新表并导入数据
            print("📝 正在导入数据...")
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            
            # 获取导入的行数
            print("🔢 正在统计导入行数...")
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            rows_count = cursor.fetchone()[0]
            
            conn.commit()
            conn.close()
            
            # 保存当前数据库信息
            self.current_db_path = db_path
            
            # 获取原始文件名
            original_filename = os.path.basename(file_path)
            
            # 添加到对话表列表
            self.add_table_to_conversation(table_name, original_filename, list(df.columns), rows_count)
            
            print(f"✅ 导入完成，共导入 {rows_count} 行数据")
            
            # 生成处理报告
            processing_report = None
            if cleaning_log:
                processing_report = self.data_processor.generate_processing_report(quality_report, cleaning_log)
            
            return {
                "success": True,
                "message": f"成功导入 {rows_count} 行数据到表 '{table_name}'",
                "rows_imported": rows_count,
                "columns": list(df.columns),
                "table_name": table_name,
                "total_tables": len(self.conversation_tables),
                "file_format": file_format,
                "quality_report": quality_report,
                "cleaning_log": cleaning_log,
                "processing_report": processing_report
            }
            
        except Exception as e:
            print(f"❌ 导入失败: {str(e)}")
            return {"success": False, "message": f"导入失败: {str(e)}"}
    
    def import_csv_to_sqlite(self, csv_file_path, table_name, db_path="analysis_db.db"):
        """保持向后兼容性的CSV导入方法"""
        return self.import_file_to_sqlite(csv_file_path, table_name, db_path)
    
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
                schema_info = cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
                
                # 获取样本数据
                sample_data = cursor.execute(f"SELECT * FROM {table_name} LIMIT 3").fetchall()
                column_names = [description[0] for description in cursor.description]
                
                # 获取行数
                row_count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                
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
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns_info = cursor.fetchall()
                columns = [col[1] for col in columns_info]
                
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
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
                    "columns": columns,
                    "data": results,
                    "row_count": len(results),
                    "sql_executed": sql,
                    "execution_time": execution_time,
                    "query_type": "SELECT",
                    "data_preview": results[:5] if results else [],
                    "available_tables": [table["table_name"] for table in self.conversation_tables]
                }
                
                conn.close()
                return result_data
            else:
                conn.commit()
                conn.close()
                return {
                    "message": "查询执行成功", 
                    "sql_executed": sql, 
                    "execution_time": execution_time,
                    "query_type": "NON_SELECT",
                    "available_tables": [table["table_name"] for table in self.conversation_tables]
                }
                
        except Exception as e:
            return {
                "error": f"查询执行失败: {str(e)}", 
                "sql_attempted": sql,
                "execution_time": 0,
                "query_type": "ERROR",
                "available_tables": [table["table_name"] for table in self.conversation_tables]
            }
    
    def execute_tool(self, tool_name, tool_input):
        """执行工具调用"""
        try:
            if tool_name == "query_database":
                sql = tool_input.get("sql", "")
                if not sql:
                    return {"error": "SQL参数为空", "query_type": "ERROR"}
                # 危险SQL检测（修正版）
                sql_lower = sql.lower().replace('\n', ' ').strip()
                # 检查SELECT * FROM
                if re.search(r"select\s+\*\s+from", sql_lower):
                    # 如果没有LIMIT则危险
                    if "limit" not in sql_lower:
                        return {
                            "error": f"⚠️ 检测到你的SQL命令为: {sql}\n该命令会返回大量数据，极易导致token超限和系统崩溃。请改用统计、采样或加LIMIT的方式查询。",
                            "query_type": "DANGEROUS_SQL"
                        }
                    # 有LIMIT但limit值过大也危险
                    m = re.search(r"limit\s+(\d+)", sql_lower)
                    if m and int(m.group(1)) > 100:
                        return {
                            "error": f"⚠️ 检测到你的SQL命令为: {sql}\nLIMIT值过大，极易导致token超限和系统崩溃。建议LIMIT不超过100。",
                            "query_type": "DANGEROUS_SQL"
                        }
                # 其它危险模式
                dangerous_patterns = [
                    r"into\s+outfile",  # 导出
                    r"copy.+to",  # COPY TO
                    r"union",  # UNION
                ]
                for pattern in dangerous_patterns:
                    if re.search(pattern, sql_lower):
                        return {
                            "error": f"⚠️ 检测到你的SQL命令为: {sql}\n该命令存在高风险操作，已被拦截。",
                            "query_type": "DANGEROUS_SQL"
                        }
                return self.query_database(sql)
            
            elif tool_name == "get_table_info":
                result = self.get_table_schema()
                return {
                    "table_info": result,
                    "query_type": "TABLE_INFO",
                    "execution_time": 0.001
                }
            
            else:
                return {"error": f"未知工具: {tool_name}", "query_type": "ERROR"}
        except Exception as e:
            return {
                "error": f"工具执行错误: {str(e)}",
                "query_type": "ERROR",
                "execution_time": 0
            }