#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试历史记录API
"""

import requests
import json
from urllib.parse import quote

def test_history_api():
    """测试历史记录API"""
    base_url = "http://localhost:5000/api"
    
    # 测试用户信息
    test_user_id = "test_user_api"
    test_username = "API测试用户"
    
    headers = {
        'Content-Type': 'application/json',
        'X-User-ID': test_user_id,
        'X-Username': quote(test_username)  # URL编码处理中文
    }
    
    print("🧪 开始测试历史记录API...")
    
    try:
        # 1. 测试健康检查
        print("🏥 测试健康检查...")
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 健康检查通过: {data['service']} v{data['version']}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return
        
        # 2. 测试获取对话统计
        print("📊 测试获取对话统计...")
        response = requests.get(f"{base_url}/conversations/stats", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 统计信息: {data['stats']}")
        else:
            print(f"❌ 获取统计失败: {response.status_code}")
        
        # 3. 测试获取对话历史
        print("📚 测试获取对话历史...")
        response = requests.get(f"{base_url}/conversations?limit=5&offset=0", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 对话历史: {len(data['conversations'])} 条记录")
        else:
            print(f"❌ 获取历史失败: {response.status_code}")
        
        # 4. 测试获取最近对话
        print("🕒 测试获取最近对话...")
        response = requests.get(f"{base_url}/conversations/recent?limit=3", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 最近对话: {len(data['conversations'])} 条记录")
        else:
            print(f"❌ 获取最近对话失败: {response.status_code}")
        
        print("\n🎉 API测试完成！")
        
    except Exception as e:
        print(f"❌ API测试失败: {e}")

if __name__ == "__main__":
    test_history_api() 