#!/usr/bin/env python3
"""
测试前后端连接的脚本
"""

import os
import sys
import requests
import time
import webbrowser
from pathlib import Path

def print_header(title):
    """打印格式化的标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_backend_health():
    """测试后端健康状态"""
    print_header("测试后端健康状态")
    
    endpoints = [
        "http://localhost:5000/health",
        "http://localhost:5000/api/health",
        "http://127.0.0.1:5000/health",
        "http://127.0.0.1:5000/api/health"
    ]
    
    for endpoint in endpoints:
        try:
            print(f"尝试连接: {endpoint}")
            response = requests.get(endpoint, timeout=3)
            if response.status_code == 200:
                print(f"✅ 连接成功 ({endpoint})")
                print(f"   响应: {response.json()}")
                return True
            else:
                print(f"❌ 连接失败 ({endpoint}): {response.status_code} {response.reason}")
        except Exception as e:
            print(f"❌ 连接错误 ({endpoint}): {str(e)}")
    
    print("❌ 所有连接尝试均失败")
    return False

def test_frontend_files():
    """测试前端文件是否存在"""
    print_header("测试前端文件")
    
    frontend_dir = Path("frontend")
    required_files = ["index.html", "api.js", "user_manager.js"]
    
    if not frontend_dir.exists():
        print(f"❌ 前端目录不存在: {frontend_dir.absolute()}")
        return False
    
    all_ok = True
    for file in required_files:
        file_path = frontend_dir / file
        if file_path.exists():
            print(f"✅ 文件存在: {file_path}")
        else:
            print(f"❌ 文件不存在: {file_path}")
            all_ok = False
    
    return all_ok

def test_static_file_serving():
    """测试静态文件服务"""
    print_header("测试静态文件服务")
    
    endpoints = [
        "http://localhost:5000/",
        "http://localhost:5000/index.html",
        "http://localhost:5000/api.js",
        "http://localhost:5000/user_manager.js"
    ]
    
    for endpoint in endpoints:
        try:
            print(f"尝试访问: {endpoint}")
            response = requests.get(endpoint, timeout=3)
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                content_length = len(response.content)
                print(f"✅ 访问成功: {endpoint}")
                print(f"   内容类型: {content_type}")
                print(f"   内容长度: {content_length} 字节")
            else:
                print(f"❌ 访问失败: {response.status_code} {response.reason}")
        except Exception as e:
            print(f"❌ 访问错误: {str(e)}")
    
    return True

def open_browser_with_debug():
    """打开浏览器并启用开发者工具"""
    print_header("打开浏览器进行测试")
    
    url = "http://localhost:5000/"
    print(f"正在打开浏览器访问: {url}")
    print("请在浏览器中按F12打开开发者工具，查看控制台输出")
    
    try:
        webbrowser.open(url)
        return True
    except Exception as e:
        print(f"❌ 无法打开浏览器: {str(e)}")
        return False

def main():
    """主函数"""
    print("\n🔍 开始测试前后端连接...")
    
    # 测试后端健康状态
    backend_ok = test_backend_health()
    
    # 测试前端文件
    frontend_ok = test_frontend_files()
    
    # 测试静态文件服务
    if backend_ok:
        static_ok = test_static_file_serving()
    else:
        print("⚠️ 后端连接失败，跳过静态文件服务测试")
        static_ok = False
    
    # 打印总结
    print_header("测试结果总结")
    print(f"后端健康状态: {'✅ 正常' if backend_ok else '❌ 异常'}")
    print(f"前端文件状态: {'✅ 正常' if frontend_ok else '❌ 异常'}")
    print(f"静态文件服务: {'✅ 正常' if static_ok else '❌ 异常或未测试'}")
    
    # 提供解决方案
    if not backend_ok:
        print("\n🔧 解决方案:")
        print("1. 确保服务器已启动: python serve.py")
        print("2. 检查端口5000是否被占用")
        print("3. 检查防火墙设置是否阻止了连接")
    
    if not frontend_ok:
        print("\n🔧 解决方案:")
        print("1. 确保前端文件存在于frontend目录中")
        print("2. 检查文件权限是否正确")
    
    # 打开浏览器进行测试
    if backend_ok and frontend_ok:
        open_browser_with_debug()
    
    print("\n测试完成!")

if __name__ == "__main__":
    main() 