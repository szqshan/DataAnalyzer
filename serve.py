#!/usr/bin/env python3
"""
启动Flask应用程序的脚本，提供更多的调试信息和错误处理
"""

import os
import sys
from pathlib import Path
import subprocess
import time
import webbrowser
import threading

# 尝试导入dotenv
try:
    from dotenv import load_dotenv
    print("✅ 已加载dotenv模块")
    # 尝试加载.env文件
    load_dotenv()
    print("✅ 已尝试加载.env文件")
except ImportError:
    print("⚠️ dotenv模块未安装，将不会加载.env文件")
    print("   可以使用 pip install python-dotenv 安装")
except Exception as e:
    print(f"⚠️ 加载.env文件时出错: {e}")

# 检查API密钥
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    print("❌ 错误: 未找到ANTHROPIC_API_KEY环境变量")
    print("   请设置ANTHROPIC_API_KEY环境变量后再运行")
    sys.exit(1)
elif not api_key.startswith("sk-"):
    print("❌ 错误: ANTHROPIC_API_KEY格式不正确")
    print("   API密钥应以'sk-'开头")
    sys.exit(1)
else:
    print(f"✅ API密钥配置正确: {api_key[:5]}...{api_key[-4:]}")

# 创建必要的目录
print("\n📁 创建必要的目录...")
directories = ["uploads", "reports", "data", "logs"]
for directory in directories:
    Path(directory).mkdir(exist_ok=True)
    print(f"   - {directory}/: {'✅ 已创建' if Path(directory).exists() else '❌ 创建失败'}")

# 设置Flask环境变量
os.environ["FLASK_APP"] = "backend/app.py"
os.environ["FLASK_ENV"] = "development"
os.environ["FLASK_DEBUG"] = "1"

# 打印服务器信息
print("\n🚀 启动服务器...")
print("=" * 60)
print("📡 服务器地址: http://localhost:5000/")
print("🔍 API端点: http://localhost:5000/api/health")
print("📊 前端界面: http://localhost:5000/")
print("=" * 60)
print("\n💡 使用说明:")
print("1. 访问 http://localhost:5000/ 打开应用")
print("2. 如果浏览器没有自动打开，请手动复制上面的地址")
print("3. 按 Ctrl+C 停止服务器")
print("=" * 60)

def open_browser():
    """在新线程中打开浏览器，避免阻塞主线程"""
    time.sleep(2)  # 等待服务器启动
    try:
        print("\n🌐 正在自动打开浏览器...")
        webbrowser.open("http://localhost:5000/")
    except Exception as e:
        print(f"⚠️ 无法自动打开浏览器: {e}")
        print("   请手动访问 http://localhost:5000/")

# 启动浏览器线程
browser_thread = threading.Thread(target=open_browser)
browser_thread.daemon = True
browser_thread.start()

# 启动Flask服务器
try:
    subprocess.run([
        sys.executable, "-m", "flask", "run",
        "--host=0.0.0.0",
        "--port=5000",
        "--no-debugger"
    ], check=True)
except KeyboardInterrupt:
    print("\n👋 服务器已停止")
except Exception as e:
    print(f"\n❌ 服务器启动失败: {e}")
    print("请检查是否有其他程序占用了5000端口")
    print("可以尝试使用不同的端口，例如:")
    print("   FLASK_RUN_PORT=5001 python serve.py")
    sys.exit(1) 