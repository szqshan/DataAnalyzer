#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API，定位UNIQUE constraint failed: conversation_history.conversation_id问题
"""
import requests
import json
import time

BASE_URL = "http://localhost:5000/api"
USER = {"user_id": "debug_user_001", "username": "DebugUser"}
HEADERS = {
    "Content-Type": "application/json",
    "X-User-ID": USER["user_id"],
    "X-Username": USER["username"]
}

def print_json(title, data):
    print(f"\n==== {title} ====")
    print(json.dumps(data, ensure_ascii=False, indent=2))

def create_conversation():
    resp = requests.post(f"{BASE_URL}/conversations/create", headers=HEADERS, json={
        "conversation_name": "Debug对话",
        "description": "测试UNIQUE约束"
    })
    data = resp.json()
    print_json("创建新对话", data)
    return data.get('conversation', {}).get('conversation_id')

def get_conversation_detail(conv_id):
    resp = requests.get(f"{BASE_URL}/conversations/{conv_id}", headers=HEADERS)
    data = resp.json()
    print_json(f"对话详情({conv_id})", data)
    return data

def analyze(conv_id, query):
    # 直接调用分析接口，模拟多轮
    resp = requests.post(f"{BASE_URL}/analyze-stream", headers=HEADERS, json={
        "query": query,
        "conversation_id": conv_id
    }, stream=True)
    print(f"\n==== 分析请求({conv_id}) ====")
    for line in resp.iter_lines():
        if line:
            try:
                data = json.loads(line.decode('utf-8').replace('data: ', ''))
                print(data)
            except Exception as e:
                print(f"[流解析异常] {e} {line}")

def main():
    print("[1] 创建新对话...")
    conv_id = create_conversation()
    if not conv_id:
        print("创建对话失败，无法继续")
        return
    time.sleep(1)
    print("[2] 获取对话详情...")
    get_conversation_detail(conv_id)
    time.sleep(1)
    print("[3] 第一次分析请求...")
    analyze(conv_id, "请给我一个整体报告")
    time.sleep(1)
    print("[4] 第二次分析请求（同一对话）...")
    analyze(conv_id, "我要各学院分布情况")
    time.sleep(1)
    print("[5] 再次获取对话详情...")
    get_conversation_detail(conv_id)
    print("[6] 再次创建同名对话，测试ID冲突...")
    create_conversation()

if __name__ == "__main__":
    main() 