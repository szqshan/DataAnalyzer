#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试智能分析功能
验证AI是否能正确判断是否需要查询数据库
"""

import requests
import json
from urllib.parse import quote
import time

def test_smart_analysis():
    """测试智能分析功能"""
    base_url = "http://localhost:5000/api"
    
    # 测试用户信息
    test_user_id = "test_smart_user"
    test_username = "智能测试用户"
    
    headers = {
        'Content-Type': 'application/json',
        'X-User-ID': test_user_id,
        'X-Username': quote(test_username)
    }
    
    print("🧪 开始测试智能分析功能...")
    
    # 测试查询列表
    test_queries = [
        "分析数据的基本统计信息",
        "再次分析数据的基本统计信息",  # 重复查询，应该使用历史信息
        "数据中有多少个不同的学院？",  # 新查询，需要调用工具
        "刚才分析的统计信息是什么？",  # 询问历史结果，不需要查询
        "分析各学院的项目数量分布"  # 新查询，需要调用工具
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 测试 {i}: {query}")
        print("=" * 50)
        
        try:
            # 发送分析请求
            response = requests.post(
                f"{base_url}/analyze-stream",
                headers=headers,
                json={"query": query},
                stream=True
            )
            
            if response.status_code == 200:
                print("✅ 分析请求成功")
                
                # 处理流式响应
                tool_calls_count = 0
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            try:
                                data = json.loads(line_str[6:])
                                if data.get('type') == 'status':
                                    print(f"📊 {data['message']}")
                                elif data.get('type') == 'tool_result':
                                    tool_calls_count += 1
                                    print(f"🔧 工具调用: {data['tool']}")
                                elif data.get('type') == 'ai_response':
                                    # 只显示前100个字符
                                    content = data['content'][:100]
                                    if len(data['content']) > 100:
                                        content += "..."
                                    print(f"🤖 AI回复: {content}")
                            except json.JSONDecodeError:
                                continue
                
                print(f"📈 本次分析共调用工具 {tool_calls_count} 次")
                
            else:
                print(f"❌ 分析请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
        
        # 等待一下再进行下一次测试
        time.sleep(2)
    
    print("\n🎉 智能分析测试完成！")
    print("\n📋 测试总结:")
    print("- 重复查询应该减少工具调用")
    print("- 询问历史结果应该直接回答")
    print("- 新查询应该正常调用工具")

if __name__ == "__main__":
    test_smart_analysis() 