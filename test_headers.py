#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试请求头传递
"""

import requests
import json

def test_headers():
    """测试请求头传递"""
    base_url = "http://localhost:5000"
    
    # 测试1: 使用正确的请求头
    print("🧪 测试1: 使用正确的请求头")
    headers = {
        'Content-Type': 'application/json',
        'X-User-ID': 'test_user_001',
        'X-Username': '%E6%B5%8B%E8%AF%95%E7%94%A8%E6%88%B7'  # 测试用户（URL编码）
    }
    
    try:
        response = requests.get(f"{base_url}/api/status", headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"测试1失败: {e}")
    
    # 测试2: 使用英文用户名
    print("\n🧪 测试2: 使用英文用户名")
    headers = {
        'Content-Type': 'application/json',
        'X-User-ID': 'test_user_001',
        'X-Username': 'test_user'
    }
    
    try:
        response = requests.get(f"{base_url}/api/status", headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"测试2失败: {e}")
    
    # 测试3: 不使用URL编码
    print("\n🧪 测试3: 不使用URL编码")
    headers = {
        'Content-Type': 'application/json',
        'X-User-ID': 'test_user_001',
        'X-Username': '测试用户'
    }
    
    try:
        response = requests.get(f"{base_url}/api/status", headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"测试3失败: {e}")

if __name__ == "__main__":
    test_headers() 