#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话管理API测试脚本
"""

import requests
import json

def test_conversation_api():
    """测试对话管理API"""
    base_url = "http://localhost:5000"
    headers = {
        'Content-Type': 'application/json',
        'X-User-ID': 'test_user_001',
        'X-Username': '%E6%B5%8B%E8%AF%95%E7%94%A8%E6%88%B7'  # 测试用户（URL编码）
    }
    
    print("🧪 开始测试对话管理API...")
    
    # 1. 测试创建新对话
    print("\n1. 测试创建新对话")
    try:
        response = requests.post(
            f"{base_url}/api/conversations/create",
            headers=headers,
            json={
                'conversation_name': '测试对话1',
                'description': '这是一个测试对话'
            }
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"创建对话失败: {e}")
    
    # 2. 测试获取对话列表
    print("\n2. 测试获取对话列表")
    try:
        response = requests.get(
            f"{base_url}/api/conversations/list",
            headers=headers
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"获取对话列表失败: {e}")
    
    # 3. 测试获取当前对话
    print("\n3. 测试获取当前对话")
    try:
        response = requests.get(
            f"{base_url}/api/conversations/current",
            headers=headers
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"获取当前对话失败: {e}")
    
    print("\n✅ 对话管理API测试完成")

if __name__ == "__main__":
    test_conversation_api() 