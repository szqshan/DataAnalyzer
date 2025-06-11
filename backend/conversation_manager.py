# conversation_manager.py - 终极修复版，专门处理实际AI响应格式
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

class ConversationManager:
    """终极修复版对话管理器 - 针对实际AI响应格式优化"""
    
    def __init__(self, user_paths: Dict[str, Path]):
        """
        初始化对话管理器
        
        Args:
            user_paths: 用户路径字典，包含各种目录路径
        """
        self.user_paths = user_paths
        self.current_conversation_id = None
        self.ai_complete_response = ""  # 存储完整AI响应
        
        print("📚 HTML报告管理器已初始化（终极版）")
    
    def start_new_conversation(self, user_query: str, user_info: Dict[str, str]) -> str:
        """
        开始新的对话
        
        Args:
            user_query: 用户查询
            user_info: 用户信息
            
        Returns:
            conversation_id: 对话ID
        """
        conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_conversation_id = conversation_id
        self.ai_complete_response = ""  # 重置响应内容
        
        print(f"🆕 开始新对话: {conversation_id}")
        return conversation_id
    
    def add_ai_response_chunk(self, content: str, chunk_type: str = 'text'):
        """
        添加AI响应片段（用于流式输出）
        
        Args:
            content: 响应内容片段
            chunk_type: 片段类型 (text/html/status)
        """
        # 只收集文本内容，用于HTML提取
        if chunk_type == 'text':
            self.ai_complete_response += content
    
    def complete_conversation(self, status: str = 'completed'):
        """
        完成当前对话并提取保存HTML
        
        Args:
            status: 完成状态 (completed/error/interrupted)
        """
        if not self.current_conversation_id:
            return None
        
        print(f"✅ 对话完成: {self.current_conversation_id}")
        
        # 🔥 保存完整响应到调试文件
        self._save_debug_response()
        
        # 🔥 关键：提取并保存HTML内容
        html_content = self.extract_html_content()
        if html_content:
            html_file_path = self.save_html_report(html_content)
            print(f"📊 HTML报告已保存到: {html_file_path}")
            return {'html_report_path': str(html_file_path)}
        else:
            print("⚠️ 未找到HTML内容")
            return None
    
    def _save_debug_response(self):
        """保存完整AI响应用于调试"""
        try:
            debug_dir = self.user_paths['user_dir'] / 'debug'
            debug_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            debug_file = debug_dir / f'ai_response_{timestamp}.txt'
            
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(f"AI响应长度: {len(self.ai_complete_response)} 字符\n")
                f.write("=" * 50 + "\n")
                f.write(self.ai_complete_response)
            
            print(f"🐛 调试文件已保存: {debug_file}")
        except Exception as e:
            print(f"⚠️ 保存调试文件失败: {e}")
    
    def extract_html_content(self) -> Optional[str]:
        """🔥 终极HTML提取算法 - 基于实际AI响应格式"""
        if not self.ai_complete_response:
            print("❌ AI响应内容为空")
            return None
        
        text = self.ai_complete_response
        print(f"🔍 AI响应总长度: {len(text)} 字符")
        
        # 🔥 策略1: 寻找完整的HTML文档（不在代码块中）
        # 这是最常见的情况，AI直接输出HTML
        print("🔍 策略1: 查找直接输出的HTML文档")
        
        # 查找所有可能的HTML开始位置
        html_start_positions = []
        
        # 查找DOCTYPE声明
        for match in re.finditer(r'<!DOCTYPE\s+html>', text, re.IGNORECASE):
            html_start_positions.append(('DOCTYPE', match.start()))
        
        # 查找HTML标签（没有DOCTYPE的情况）
        for match in re.finditer(r'<html[^>]*>', text, re.IGNORECASE):
            html_start_positions.append(('HTML_TAG', match.start()))
        
        print(f"找到 {len(html_start_positions)} 个可能的HTML开始位置")
        
        # 查找所有HTML结束位置
        html_end_positions = []
        for match in re.finditer(r'</html>', text, re.IGNORECASE):
            html_end_positions.append(match.end())
        
        print(f"找到 {len(html_end_positions)} 个HTML结束位置")
        
        # 🔥 尝试每种开始和结束位置的组合
        best_html = None
        best_score = 0
        
        for start_type, start_pos in html_start_positions:
            for end_pos in html_end_positions:
                if end_pos > start_pos:
                    candidate_html = text[start_pos:end_pos]
                    score = self._score_html_candidate(candidate_html)
                    
                    print(f"🔍 候选HTML: {start_type} {start_pos}-{end_pos}, 长度={len(candidate_html)}, 评分={score}")
                    
                    if score > best_score:
                        best_html = candidate_html
                        best_score = score
        
        if best_html and best_score > 5:  # 设置最低评分阈值
            print(f"✅ 找到最佳HTML候选，评分: {best_score}")
            return self._clean_html_content(best_html)
        
        # 🔥 策略2: 查找代码块中的HTML
        print("🔍 策略2: 查找代码块中的HTML")
        code_block_patterns = [
            r'```html\s*(<!DOCTYPE html.*?</html>)\s*```',
            r'```html\s*(<html.*?</html>)\s*```',
            r'```\s*(<!DOCTYPE html.*?</html>)\s*```',
            r'```\s*(<html.*?</html>)\s*```'
        ]
        
        for pattern in code_block_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                html_content = match.group(1)
                score = self._score_html_candidate(html_content)
                if score > 5:
                    print(f"✅ 在代码块中找到HTML，评分: {score}")
                    return self._clean_html_content(html_content)
        
        print("❌ 未能找到有效的HTML内容")
        return None
    
    def _score_html_candidate(self, html_content: str) -> int:
        """为HTML候选内容评分，分数越高越可能是完整的HTML报告"""
        if not html_content:
            return 0
        
        score = 0
        html_lower = html_content.lower()
        
        # 基础结构评分
        if '<!doctype html>' in html_lower:
            score += 2
        if '<html' in html_lower and '</html>' in html_lower:
            score += 2
        if '<head' in html_lower and '</head>' in html_lower:
            score += 1
        if '<body' in html_lower and '</body>' in html_lower:
            score += 1
        
        # 内容丰富度评分
        if '<style' in html_lower:
            score += 1
        if '<table' in html_lower:
            score += 1
        if '<div' in html_lower:
            score += 1
        if 'class=' in html_lower:
            score += 1
        
        # 长度评分
        if len(html_content) > 1000:
            score += 1
        if len(html_content) > 5000:
            score += 1
        if len(html_content) > 10000:
            score += 1
        
        # 报告特征评分
        report_keywords = ['分析报告', '数据分析', '统计', '项目', '报告', 'report', 'analysis']
        for keyword in report_keywords:
            if keyword in html_lower:
                score += 1
                break
        
        return score
    
    def _clean_html_content(self, html_content: str) -> str:
        """清理HTML内容"""
        # 移除多余的空白行
        cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', html_content)
        
        # 确保有DOCTYPE声明
        cleaned = cleaned.strip()
        if not cleaned.startswith('<!DOCTYPE'):
            if cleaned.startswith('<html'):
                cleaned = '<!DOCTYPE html>\n' + cleaned
        
        return cleaned
    
    def save_html_report(self, html_content: str) -> Optional[Path]:
        """保存HTML报告到文件 - 增强版"""
        try:
            if not html_content:
                return None
            
            # 确保报告目录存在
            reports_dir = self.user_paths['reports_dir']
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成报告文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            html_file = reports_dir / f'analysis_report_{timestamp}.html'
            
            # 🔥 清理和验证HTML内容
            cleaned_html = self._clean_html_content(html_content)
            
            # 保存文件
            with open(html_file, 'w', encoding='utf-8', newline='') as f:
                f.write(cleaned_html)
            
            # 同时保存为最新报告
            latest_report = reports_dir / 'latest_analysis_report.html'
            with open(latest_report, 'w', encoding='utf-8', newline='') as f:
                f.write(cleaned_html)
            
            # 验证文件保存成功
            if html_file.exists():
                file_size = html_file.stat().st_size
                print(f"📊 HTML报告保存成功: {html_file}")
                print(f"📊 文件大小: {file_size} 字节")
                
                # 🔥 额外验证：读取并验证保存的内容
                with open(html_file, 'r', encoding='utf-8') as f:
                    saved_content = f.read()
                
                if self._validate_saved_html(saved_content):
                    print("✅ 保存的HTML文件验证通过")
                    return html_file
                else:
                    print("❌ 保存的HTML文件验证失败")
                    return None
            else:
                print("❌ HTML文件保存失败")
                return None
                
        except Exception as e:
            print(f"❌ 保存HTML报告失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _validate_saved_html(self, html_content: str) -> bool:
        """验证保存的HTML文件内容"""
        if not html_content or len(html_content) < 200:
            print(f"❌ 保存的HTML内容过短: {len(html_content)} 字符")
            return False
        
        html_lower = html_content.lower()
        
        # 检查基本结构
        required_elements = ['<html', '</html>', '<head', '<body']
        missing = [elem for elem in required_elements if elem not in html_lower]
        
        if missing:
            print(f"❌ 保存的HTML缺少元素: {missing}")
            return False
        
        # 检查是否有实际内容
        content_indicators = ['<table', '<div', '<h1', '<h2', '<h3', '<p']
        has_content = any(indicator in html_lower for indicator in content_indicators)
        
        if not has_content:
            print("❌ 保存的HTML没有实际内容")
            return False
        
        print("✅ 保存的HTML内容验证通过")
        return True
    
    def get_html_file_path(self) -> Optional[str]:
        """获取最新HTML报告的文件路径"""
        try:
            latest_report = self.user_paths['reports_dir'] / 'latest_analysis_report.html'
            if latest_report.exists() and latest_report.stat().st_size > 100:
                return str(latest_report)
        except Exception as e:
            print(f"❌ 获取HTML文件路径失败: {e}")
        return None
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """获取简化的状态摘要"""
        return {
            'current_conversation_active': self.current_conversation_id is not None,
            'latest_html_report': self.get_html_file_path()
        }