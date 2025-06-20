#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试对话流程 - 验证删除自动创建对话逻辑后的系统行为
"""

import requests
import json
import time

# 测试配置
BASE_URL = "http://localhost:5000/api"
TEST_USER = {
    "user_id": "test_user_flow",
    "username": "FlowTestUser"
}

def get_headers():
    """获取请求头"""
    return {
        "Content-Type": "application/json",
        "X-User-ID": TEST_USER["user_id"],
        "X-Username": TEST_USER["username"]
    }

def test_conversation_flow():
    """测试对话流程"""
    print("🧪 开始测试对话流程...")
    
    # 1. 检查系统状态
    print("\n1. 检查系统状态...")
    response = requests.get(f"{BASE_URL}/status", headers=get_headers())
    print(f"状态检查结果: {response.status_code}")
    if response.status_code == 200:
        status_data = response.json()
        print(f"系统就绪: {status_data.get('system_ready')}")
        print(f"数据库连接: {status_data.get('database_connected')}")
    
    # 2. 尝试直接分析（应该失败，因为没有当前对话）
    print("\n2. 尝试直接分析（应该失败）...")
    try:
        response = requests.post(
            f"{BASE_URL}/analyze-stream",
            headers=get_headers(),
            json={"query": "分析数据的基本统计信息"},
            stream=True
        )
        
        if response.status_code == 200:
            print("❌ 错误：直接分析应该失败，但成功了")
            # 读取流式响应
            for line in response.iter_lines():
                if line:
                    data = json.loads(line.decode('utf-8').replace('data: ', ''))
                    if data.get('type') == 'error':
                        print(f"✅ 正确：收到错误消息: {data.get('message')}")
                        break
        else:
            print(f"✅ 正确：直接分析失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"✅ 正确：直接分析抛出异常: {e}")
    
    # 3. 创建新对话
    print("\n3. 创建新对话...")
    response = requests.post(
        f"{BASE_URL}/conversations/create",
        headers=get_headers(),
        json={
            "conversation_name": "测试对话",
            "description": "用于测试的对话"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            conversation_id = data['conversation']['conversation_id']
            print(f"✅ 对话创建成功: {conversation_id}")
            
            # 4. 再次尝试分析（应该成功）
            print("\n4. 再次尝试分析（应该成功）...")
            try:
                response = requests.post(
                    f"{BASE_URL}/analyze-stream",
                    headers=get_headers(),
                    json={"query": "告诉我你有哪些数据"},
                    stream=True
                )
                
                if response.status_code == 200:
                    print("✅ 分析请求成功，开始接收流式响应...")
                    for line in response.iter_lines():
                        if line:
                            try:
                                data = json.loads(line.decode('utf-8').replace('data: ', ''))
                                if data.get('type') == 'status':
                                    print(f"状态: {data.get('message')}")
                                elif data.get('type') == 'ai_response':
                                    print(f"AI回复: {data.get('content')}", end='')
                                elif data.get('type') == 'error':
                                    print(f"错误: {data.get('message')}")
                                    break
                            except json.JSONDecodeError:
                                continue
                else:
                    print(f"❌ 分析失败，状态码: {response.status_code}")
            except Exception as e:
                print(f"❌ 分析异常: {e}")
        else:
            print(f"❌ 对话创建失败: {data.get('message')}")
    else:
        print(f"❌ 对话创建请求失败，状态码: {response.status_code}")
    
    # 5. 获取对话列表
    print("\n5. 获取对话列表...")
    response = requests.get(f"{BASE_URL}/conversations/list", headers=get_headers())
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            conversations = data.get('conversations', [])
            print(f"✅ 获取到 {len(conversations)} 个对话")
            for conv in conversations:
                print(f"  - {conv['conversation_name']} (ID: {conv['conversation_id']})")
        else:
            print(f"❌ 获取对话列表失败: {data.get('message')}")
    else:
        print(f"❌ 获取对话列表请求失败，状态码: {response.status_code}")

if __name__ == "__main__":
    print("🚀 启动对话流程测试...")
    print(f"测试用户: {TEST_USER['username']} ({TEST_USER['user_id']})")
    print(f"API地址: {BASE_URL}")
    print("=" * 50)
    
    try:
        test_conversation_flow()
        print("\n" + "=" * 50)
        print("✅ 测试完成！")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc() 