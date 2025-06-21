import pandas as pd
import numpy as np
import os
import re
import json
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
import warnings
warnings.filterwarnings('ignore')

class DataProcessor:
    """数据处理和清洗模块"""
    
    def __init__(self):
        self.supported_formats = ['.csv', '.xlsx', '.xls', '.json', '.tsv', '.txt']
        self.quality_report = {}
        self.cleaning_log = []
        
    def detect_file_format(self, file_path: str) -> str:
        """检测文件格式"""
        _, ext = os.path.splitext(file_path.lower())
        if ext in self.supported_formats:
            return ext
        else:
            raise ValueError(f"不支持的文件格式: {ext}。支持的格式: {', '.join(self.supported_formats)}")
    
    def read_file(self, file_path: str, **kwargs) -> pd.DataFrame:
        """智能读取各种格式的文件"""
        try:
            file_format = self.detect_file_format(file_path)
            print(f"📖 检测到文件格式: {file_format}")
            
            if file_format == '.csv':
                # 尝试多种编码
                encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig', 'latin1']
                for encoding in encodings:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding, **kwargs)
                        print(f"✅ 使用编码 {encoding} 成功读取CSV文件")
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise ValueError("无法使用常见编码读取CSV文件")
                    
            elif file_format in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path, **kwargs)
                print(f"✅ 成功读取Excel文件")
                
            elif file_format == '.json':
                df = pd.read_json(file_path, **kwargs)
                print(f"✅ 成功读取JSON文件")
                
            elif file_format == '.tsv':
                df = pd.read_csv(file_path, sep='\t', **kwargs)
                print(f"✅ 成功读取TSV文件")
                
            elif file_format == '.txt':
                # 尝试检测分隔符
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline()
                
                if '\t' in first_line:
                    df = pd.read_csv(file_path, sep='\t', **kwargs)
                elif '|' in first_line:
                    df = pd.read_csv(file_path, sep='|', **kwargs)
                else:
                    df = pd.read_csv(file_path, **kwargs)
                print(f"✅ 成功读取TXT文件")
            
            print(f"📊 文件读取完成: {len(df)} 行 × {len(df.columns)} 列")
            return df
            
        except Exception as e:
            print(f"❌ 文件读取失败: {str(e)}")
            raise
    
    def assess_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """评估数据质量"""
        print("🔍 开始数据质量评估...")
        
        quality_report = {
            "basic_info": {
                "rows": len(df),
                "columns": len(df.columns),
                "memory_usage": df.memory_usage(deep=True).sum(),
                "file_size_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2)
            },
            "column_analysis": {},
            "data_quality_issues": {
                "missing_values": {},
                "duplicate_rows": 0,
                "data_type_issues": [],
                "outliers": {},
                "inconsistent_formats": {}
            },
            "recommendations": [],
            "overall_score": 0
        }
        
        # 基础统计
        total_cells = len(df) * len(df.columns)
        missing_cells = df.isnull().sum().sum()
        
        # 列分析
        for col in df.columns:
            col_info = {
                "dtype": str(df[col].dtype),
                "non_null_count": df[col].count(),
                "null_count": df[col].isnull().sum(),
                "null_percentage": round(df[col].isnull().sum() / len(df) * 100, 2),
                "unique_count": df[col].nunique(),
                "unique_percentage": round(df[col].nunique() / len(df) * 100, 2)
            }
            
            # 数值列统计
            if df[col].dtype in ['int64', 'float64']:
                col_info.update({
                    "mean": df[col].mean(),
                    "std": df[col].std(),
                    "min": df[col].min(),
                    "max": df[col].max(),
                    "median": df[col].median()
                })
                
                # 检测异常值（使用IQR方法）
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)][col]
                
                if len(outliers) > 0:
                    quality_report["data_quality_issues"]["outliers"][col] = {
                        "count": len(outliers),
                        "percentage": round(len(outliers) / len(df) * 100, 2),
                        "bounds": {"lower": lower_bound, "upper": upper_bound}
                    }
            
            # 文本列分析
            elif df[col].dtype == 'object':
                col_info.update({
                    "most_common": df[col].value_counts().head(3).to_dict() if len(df[col].dropna()) > 0 else {},
                    "avg_length": df[col].astype(str).str.len().mean() if len(df[col].dropna()) > 0 else 0
                })
                
                # 检测格式不一致
                if col.lower() in ['email', '邮箱', 'phone', '电话', 'date', '日期']:
                    inconsistent = self._check_format_consistency(df[col], col)
                    if inconsistent:
                        quality_report["data_quality_issues"]["inconsistent_formats"][col] = inconsistent
            
            quality_report["column_analysis"][col] = col_info
            
            # 记录缺失值问题
            if col_info["null_percentage"] > 0:
                quality_report["data_quality_issues"]["missing_values"][col] = {
                    "count": col_info["null_count"],
                    "percentage": col_info["null_percentage"]
                }
        
        # 重复行检测
        duplicate_count = df.duplicated().sum()
        quality_report["data_quality_issues"]["duplicate_rows"] = {
            "count": duplicate_count,
            "percentage": round(duplicate_count / len(df) * 100, 2)
        }
        
        # 数据类型问题检测
        for col in df.columns:
            if df[col].dtype == 'object':
                # 检查是否应该是数值类型
                numeric_convertible = pd.to_numeric(df[col], errors='coerce').notna().sum()
                if numeric_convertible > len(df) * 0.8:  # 80%以上可转换为数值
                    quality_report["data_quality_issues"]["data_type_issues"].append({
                        "column": col,
                        "issue": "可能应该是数值类型",
                        "convertible_percentage": round(numeric_convertible / len(df) * 100, 2)
                    })
        
        # 生成建议
        quality_report["recommendations"] = self._generate_recommendations(quality_report)
        
        # 计算总体质量分数
        quality_report["overall_score"] = self._calculate_quality_score(quality_report, total_cells, missing_cells)
        
        self.quality_report = quality_report
        print(f"✅ 数据质量评估完成，总体评分: {quality_report['overall_score']}/100")
        
        return quality_report
    
    def _check_format_consistency(self, series: pd.Series, col_name: str) -> Dict[str, Any]:
        """检查格式一致性"""
        if col_name.lower() in ['email', '邮箱']:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            valid_emails = series.dropna().str.match(email_pattern).sum()
            total_emails = len(series.dropna())
            if total_emails > 0 and valid_emails / total_emails < 0.8:
                return {
                    "valid_count": valid_emails,
                    "total_count": total_emails,
                    "valid_percentage": round(valid_emails / total_emails * 100, 2),
                    "issue": "邮箱格式不一致"
                }
        
        elif col_name.lower() in ['phone', '电话']:
            # 简单的电话号码检查
            phone_pattern = r'^[\d\-\+\(\)\s]{7,}$'
            valid_phones = series.dropna().str.match(phone_pattern).sum()
            total_phones = len(series.dropna())
            if total_phones > 0 and valid_phones / total_phones < 0.8:
                return {
                    "valid_count": valid_phones,
                    "total_count": total_phones,
                    "valid_percentage": round(valid_phones / total_phones * 100, 2),
                    "issue": "电话格式不一致"
                }
        
        return None
    
    def _generate_recommendations(self, quality_report: Dict[str, Any]) -> List[str]:
        """生成数据清洗建议"""
        recommendations = []
        
        # 缺失值建议
        missing_issues = quality_report["data_quality_issues"]["missing_values"]
        if missing_issues:
            high_missing_cols = [col for col, info in missing_issues.items() if info["percentage"] > 50]
            if high_missing_cols:
                recommendations.append(f"考虑删除缺失值超过50%的列: {', '.join(high_missing_cols)}")
            
            moderate_missing_cols = [col for col, info in missing_issues.items() if 10 < info["percentage"] <= 50]
            if moderate_missing_cols:
                recommendations.append(f"对缺失值较多的列进行填充处理: {', '.join(moderate_missing_cols)}")
        
        # 重复行建议
        if quality_report["data_quality_issues"]["duplicate_rows"]["count"] > 0:
            recommendations.append("删除重复行以提高数据质量")
        
        # 数据类型建议
        type_issues = quality_report["data_quality_issues"]["data_type_issues"]
        if type_issues:
            recommendations.append("转换数据类型以提高分析效率")
        
        # 异常值建议
        outliers = quality_report["data_quality_issues"]["outliers"]
        if outliers:
            recommendations.append("检查并处理异常值")
        
        # 格式一致性建议
        format_issues = quality_report["data_quality_issues"]["inconsistent_formats"]
        if format_issues:
            recommendations.append("标准化数据格式")
        
        return recommendations
    
    def _calculate_quality_score(self, quality_report: Dict[str, Any], total_cells: int, missing_cells: int) -> int:
        """计算数据质量分数"""
        score = 100
        
        # 缺失值扣分
        missing_percentage = missing_cells / total_cells * 100
        score -= min(missing_percentage * 0.5, 30)  # 最多扣30分
        
        # 重复行扣分
        duplicate_percentage = quality_report["data_quality_issues"]["duplicate_rows"]["percentage"]
        score -= min(duplicate_percentage * 0.3, 15)  # 最多扣15分
        
        # 数据类型问题扣分
        type_issues_count = len(quality_report["data_quality_issues"]["data_type_issues"])
        score -= min(type_issues_count * 5, 20)  # 最多扣20分
        
        # 异常值扣分
        outliers_count = len(quality_report["data_quality_issues"]["outliers"])
        score -= min(outliers_count * 3, 15)  # 最多扣15分
        
        # 格式问题扣分
        format_issues_count = len(quality_report["data_quality_issues"]["inconsistent_formats"])
        score -= min(format_issues_count * 5, 20)  # 最多扣20分
        
        return max(int(score), 0)
    
    def clean_data(self, df: pd.DataFrame, cleaning_options: Dict[str, Any] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """智能数据清洗"""
        print("🧹 开始数据清洗...")
        
        if cleaning_options is None:
            cleaning_options = {
                "remove_duplicates": True,
                "handle_missing": "auto",  # auto, drop, fill
                "fix_data_types": True,
                "remove_outliers": False,
                "standardize_text": True,
                "missing_threshold": 50  # 缺失值超过此百分比的列将被删除
            }
        
        cleaned_df = df.copy()
        cleaning_log = {
            "original_shape": df.shape,
            "operations": [],
            "final_shape": None,
            "summary": {}
        }
        
        # 1. 删除重复行
        if cleaning_options.get("remove_duplicates", True):
            before_count = len(cleaned_df)
            cleaned_df = cleaned_df.drop_duplicates()
            removed_count = before_count - len(cleaned_df)
            if removed_count > 0:
                cleaning_log["operations"].append(f"删除了 {removed_count} 行重复数据")
                print(f"🗑️ 删除了 {removed_count} 行重复数据")
        
        # 2. 处理缺失值
        missing_handling = cleaning_options.get("handle_missing", "auto")
        missing_threshold = cleaning_options.get("missing_threshold", 50)
        
        for col in cleaned_df.columns:
            missing_percentage = cleaned_df[col].isnull().sum() / len(cleaned_df) * 100
            
            if missing_percentage > missing_threshold:
                if missing_handling == "auto" or missing_handling == "drop_columns":
                    cleaned_df = cleaned_df.drop(columns=[col])
                    cleaning_log["operations"].append(f"删除缺失值过多的列: {col} ({missing_percentage:.1f}%)")
                    print(f"🗑️ 删除缺失值过多的列: {col}")
                    continue
            
            if missing_percentage > 0:
                if missing_handling == "auto":
                    # 智能填充
                    if cleaned_df[col].dtype in ['int64', 'float64']:
                        # 数值列用中位数填充
                        fill_value = cleaned_df[col].median()
                        cleaned_df[col] = cleaned_df[col].fillna(fill_value)
                        cleaning_log["operations"].append(f"用中位数填充列 {col} 的缺失值")
                    else:
                        # 文本列用众数填充
                        mode_value = cleaned_df[col].mode()
                        if len(mode_value) > 0:
                            cleaned_df[col] = cleaned_df[col].fillna(mode_value[0])
                            cleaning_log["operations"].append(f"用众数填充列 {col} 的缺失值")
                        else:
                            cleaned_df[col] = cleaned_df[col].fillna("未知")
                            cleaning_log["operations"].append(f"用'未知'填充列 {col} 的缺失值")
                elif missing_handling == "drop":
                    before_count = len(cleaned_df)
                    cleaned_df = cleaned_df.dropna(subset=[col])
                    removed_count = before_count - len(cleaned_df)
                    if removed_count > 0:
                        cleaning_log["operations"].append(f"删除了列 {col} 中有缺失值的 {removed_count} 行")
        
        # 3. 修复数据类型
        if cleaning_options.get("fix_data_types", True):
            for col in cleaned_df.columns:
                if cleaned_df[col].dtype == 'object':
                    # 尝试转换为数值类型
                    numeric_series = pd.to_numeric(cleaned_df[col], errors='coerce')
                    if numeric_series.notna().sum() > len(cleaned_df) * 0.8:
                        cleaned_df[col] = numeric_series
                        cleaning_log["operations"].append(f"将列 {col} 转换为数值类型")
                        print(f"🔄 将列 {col} 转换为数值类型")
                    
                    # 尝试转换为日期类型
                    elif col.lower() in ['date', '日期', 'time', '时间', 'created', 'updated']:
                        try:
                            date_series = pd.to_datetime(cleaned_df[col], errors='coerce')
                            if date_series.notna().sum() > len(cleaned_df) * 0.8:
                                cleaned_df[col] = date_series
                                cleaning_log["operations"].append(f"将列 {col} 转换为日期类型")
                                print(f"📅 将列 {col} 转换为日期类型")
                        except:
                            pass
        
        # 4. 标准化文本
        if cleaning_options.get("standardize_text", True):
            for col in cleaned_df.columns:
                if cleaned_df[col].dtype == 'object':
                    # 去除首尾空格
                    cleaned_df[col] = cleaned_df[col].astype(str).str.strip()
                    
                    # 统一大小写（如果是英文且值较少）
                    if cleaned_df[col].nunique() < len(cleaned_df) * 0.1:  # 如果唯一值少于10%
                        if cleaned_df[col].str.contains(r'^[a-zA-Z\s]+$', na=False).any():
                            original_values = cleaned_df[col].unique()
                            cleaned_df[col] = cleaned_df[col].str.title()
                            new_values = cleaned_df[col].unique()
                            if len(original_values) != len(new_values):
                                cleaning_log["operations"].append(f"标准化列 {col} 的文本格式")
        
        # 5. 清理列名
        original_columns = list(cleaned_df.columns)
        cleaned_df.columns = [self._clean_column_name(col) for col in cleaned_df.columns]
        if list(cleaned_df.columns) != original_columns:
            cleaning_log["operations"].append("清理了列名格式")
            print("🧹 清理了列名格式")
        
        cleaning_log["final_shape"] = cleaned_df.shape
        cleaning_log["summary"] = {
            "rows_removed": df.shape[0] - cleaned_df.shape[0],
            "columns_removed": df.shape[1] - cleaned_df.shape[1],
            "operations_count": len(cleaning_log["operations"])
        }
        
        self.cleaning_log = cleaning_log
        print(f"✅ 数据清洗完成: {df.shape} → {cleaned_df.shape}")
        
        return cleaned_df, cleaning_log
    
    def _clean_column_name(self, col_name: str) -> str:
        """清理列名"""
        cleaned = str(col_name).strip()
        # 保留中文、英文、数字和下划线
        cleaned = re.sub(r'[^\w\u4e00-\u9fff]', '_', cleaned)
        # 合并多个下划线
        cleaned = re.sub(r'_+', '_', cleaned)
        # 去除首尾下划线
        cleaned = cleaned.strip('_')
        return cleaned or 'unnamed_column'
    
    def generate_processing_report(self, quality_report: Dict[str, Any], cleaning_log: Dict[str, Any]) -> Dict[str, Any]:
        """生成数据处理报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "data_quality": quality_report,
            "cleaning_operations": cleaning_log,
            "summary": {
                "original_quality_score": quality_report.get("overall_score", 0),
                "processing_operations": len(cleaning_log.get("operations", [])),
                "data_reduction": {
                    "rows": cleaning_log.get("summary", {}).get("rows_removed", 0),
                    "columns": cleaning_log.get("summary", {}).get("columns_removed", 0)
                }
            },
            "recommendations_implemented": [],
            "remaining_issues": []
        }
        
        # 分析已实施的建议
        operations = cleaning_log.get("operations", [])
        recommendations = quality_report.get("recommendations", [])
        
        for rec in recommendations:
            if any(op in rec for op in ["删除重复", "删除缺失", "转换", "标准化"]):
                if any(similar_op in ' '.join(operations) for similar_op in ["删除", "转换", "标准化"]):
                    report["recommendations_implemented"].append(rec)
                else:
                    report["remaining_issues"].append(rec)
        
        return report
    
    def preview_data(self, df: pd.DataFrame, n_rows: int = 10) -> Dict[str, Any]:
        """预览数据"""
        preview = {
            "shape": df.shape,
            "columns": list(df.columns),
            "dtypes": df.dtypes.to_dict(),
            "head": df.head(n_rows).to_dict('records'),
            "tail": df.tail(n_rows).to_dict('records'),
            "sample": df.sample(min(n_rows, len(df))).to_dict('records') if len(df) > n_rows else [],
            "basic_stats": {}
        }
        
        # 基础统计信息
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            preview["basic_stats"]["numeric"] = df[numeric_cols].describe().to_dict()
        
        text_cols = df.select_dtypes(include=['object']).columns
        if len(text_cols) > 0:
            preview["basic_stats"]["text"] = {}
            for col in text_cols:
                preview["basic_stats"]["text"][col] = {
                    "unique_count": df[col].nunique(),
                    "most_common": df[col].value_counts().head(5).to_dict()
                }
        
        return preview 