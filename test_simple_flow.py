#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试 - 验证删除自动创建对话逻辑后的系统行为
"""

import requests
import json

# 测试配置
BASE_URL = "http://localhost:5000/api"
TEST_USER = {
    "user_id": "test_user_simple",
    "username": "SimpleTestUser"
}

def get_headers():
    """获取请求头"""
    return {
        "Content-Type": "application/json",
        "X-User-ID": TEST_USER["user_id"],
        "X-Username": TEST_USER["username"]
    }

def test_no_auto_conversation():
    """测试没有自动创建对话的行为"""
    print("🧪 测试删除自动创建对话逻辑...")
    
    # 1. 尝试直接分析（应该失败）
    print("\n1. 尝试直接分析（应该失败）...")
    try:
        response = requests.post(
            f"{BASE_URL}/analyze-stream",
            headers=get_headers(),
            json={"query": "分析数据的基本统计信息"},
            stream=True
        )
        
        if response.status_code == 200:
            print("✅ 分析请求成功，检查是否返回错误消息...")
            error_found = False
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode('utf-8').replace('data: ', ''))
                        if data.get('type') == 'error':
                            print(f"✅ 正确：收到错误消息: {data.get('message')}")
                            error_found = True
                            break
                    except json.JSONDecodeError:
                        continue
            
            if not error_found:
                print("❌ 错误：应该收到错误消息但没有收到")
        else:
            print(f"✅ 正确：直接分析失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"✅ 正确：直接分析抛出异常: {e}")
    
    # 2. 创建新对话
    print("\n2. 创建新对话...")
    response = requests.post(
        f"{BASE_URL}/conversations/create",
        headers=get_headers(),
        json={
            "conversation_name": "Test Conversation",
            "description": "Test conversation for validation"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            conversation_id = data['conversation']['conversation_id']
            print(f"✅ 对话创建成功: {conversation_id}")
            
            # 3. 再次尝试分析（应该成功）
            print("\n3. 再次尝试分析（应该成功）...")
            try:
                response = requests.post(
                    f"{BASE_URL}/analyze-stream",
                    headers=get_headers(),
                    json={"query": "Tell me what data you have"},
                    stream=True
                )
                
                if response.status_code == 200:
                    print("✅ 分析请求成功，开始接收流式响应...")
                    success_found = False
                    for line in response.iter_lines():
                        if line:
                            try:
                                data = json.loads(line.decode('utf-8').replace('data: ', ''))
                                if data.get('type') == 'status':
                                    print(f"状态: {data.get('message')}")
                                    if "开始智能分析数据" in data.get('message', ''):
                                        success_found = True
                                elif data.get('type') == 'ai_response':
                                    print(f"AI回复: {data.get('content')}", end='')
                                elif data.get('type') == 'error':
                                    print(f"错误: {data.get('message')}")
                                    break
                            except json.JSONDecodeError:
                                continue
                    
                    if success_found:
                        print("\n✅ 验证成功：删除自动创建对话逻辑后，系统行为正确")
                    else:
                        print("\n❌ 验证失败：没有收到预期的成功消息")
                else:
                    print(f"❌ 分析失败，状态码: {response.status_code}")
            except Exception as e:
                print(f"❌ 分析异常: {e}")
        else:
            print(f"❌ 对话创建失败: {data.get('message')}")
    else:
        print(f"❌ 对话创建请求失败，状态码: {response.status_code}")

if __name__ == "__main__":
    print("🚀 启动简单测试...")
    print(f"测试用户: {TEST_USER['username']} ({TEST_USER['user_id']})")
    print(f"API地址: {BASE_URL}")
    print("=" * 50)
    
    try:
        test_no_auto_conversation()
        print("\n" + "=" * 50)
        print("✅ 测试完成！")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc() 