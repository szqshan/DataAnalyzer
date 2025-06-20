# P1精简版数据库分析器 - 清理调试输出
# 版本: 3.1.0 - P1阶段精简版

from anthropic import Anthropic
import sqlite3
import pandas as pd
import os
from datetime import datetime
import json
import re
from typing import Dict, List, Optional, Any

class DatabaseAnalyzer:
    """P1精简版数据库分析器类 - 专注核心数据处理功能"""
    
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
        self.current_table_name = None
        
        # 定义工具 - 使用正确的格式
        self.tools = [
            {
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
                "name": "get_table_info",
                "description": "获取表的结构信息和样本数据",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
        
    def import_csv_to_sqlite(self, csv_file_path, table_name, db_path="analysis_db.db"):
        """从CSV文件创建SQLite表并导入数据"""
        try:
            print(f"📥 开始导入CSV文件: {csv_file_path}")
            print(f"📊 目标数据库: {db_path}")
            print(f"📋 目标表名: {table_name}")
            
            if not os.path.exists(csv_file_path):
                print(f"❌ CSV文件不存在: {csv_file_path}")
                return {"success": False, "message": f"CSV文件不存在: {csv_file_path}"}
            
            # 读取CSV文件
            print("📖 正在读取CSV文件...")
            df = pd.read_csv(csv_file_path, encoding='utf-8')
            print(f"✅ CSV文件读取成功，共 {len(df)} 行")
            
            # 清理列名
            print("🧹 正在清理列名...")
            df.columns = [self._clean_column_name(col) for col in df.columns]
            print(f"✅ 列名清理完成: {list(df.columns)}")
            
            # 连接到SQLite数据库
            print(f"🔌 正在连接数据库: {db_path}")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 删除已存在的表并创建新表
            print(f"🗑️ 正在准备表 {table_name}...")
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            print("📝 正在创建新表...")
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            
            # 获取导入的行数
            print("🔢 正在统计导入行数...")
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            rows_count = cursor.fetchone()[0]
            
            conn.commit()
            conn.close()
            
            # 保存当前数据库信息
            self.current_db_path = db_path
            self.current_table_name = table_name
            
            print(f"✅ 导入完成，共导入 {rows_count} 行数据")
            
            return {
                "success": True,
                "message": f"成功导入 {rows_count} 行数据到表 '{table_name}'",
                "rows_imported": rows_count,
                "columns": list(df.columns)
            }
            
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
                
                conn.close()
                return result_data
            else:
                conn.commit()
                conn.close()
                return {
                    "message": "查询执行成功", 
                    "sql_executed": sql, 
                    "execution_time": execution_time,
                    "query_type": "NON_SELECT"
                }
                
        except Exception as e:
            return {
                "error": f"查询执行失败: {str(e)}", 
                "sql_attempted": sql,
                "execution_time": 0,
                "query_type": "ERROR"
            }
    
    def execute_tool(self, tool_name, tool_input):
        """执行工具调用"""
        try:
            if tool_name == "query_database":
                sql = tool_input.get("sql", "")
                if not sql:
                    return {"error": "SQL参数为空", "query_type": "ERROR"}
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