#!/usr/bin/env python3
"""
智能数据库分析系统服务器启动脚本
"""

import os
import sys
from pathlib import Path

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()  # 加载 .env 文件
    print("✅ .env 文件已加载")
except ImportError:
    print("⚠️  python-dotenv 未安装，无法加载 .env 文件")
except Exception as e:
    print(f"⚠️  加载 .env 文件失败: {e}")

# 检查API密钥
api_key = os.getenv('ANTHROPIC_API_KEY')
if not api_key:
    print("❌ 环境变量中未找到 ANTHROPIC_API_KEY")
    print("\n🔧 解决方案:")
    print("1. 检查 .env 文件格式:")
    print("   ANTHROPIC_API_KEY=sk-your-key-here")
    sys.exit(1)

# 验证密钥格式
if not api_key.startswith('sk-'):
    print("❌ API密钥格式不正确，应该以 'sk-' 开头")
    sys.exit(1)

print(f"✅ API密钥已配置 (长度: {len(api_key)} 字符)")

# 创建必要的目录
directories = ['uploads', 'reports', 'data', 'logs']
for directory in directories:
    dir_path = Path(directory)
    dir_path.mkdir(exist_ok=True)
    print(f"  ✅ {directory}/ 目录已创建")

print("✅ 目录创建完成")

# 设置环境变量
os.environ['FLASK_APP'] = 'backend/app.py'
os.environ['FLASK_ENV'] = 'development'

print("\n🚀 启动服务器...")
print("📡 服务地址: http://localhost:5000")
print("📱 前端界面: http://localhost:5000/")
print("🔧 API地址: http://localhost:5000/api")
print("📊 健康检查: http://localhost:5000/api/health")
print("\n💡 使用说明:")
print("  1. 在浏览器中访问 http://localhost:5000/")
print("  2. 上传CSV文件并进行分析")
print("\n按 Ctrl+C 停止服务")
print("=" * 60)

# 导入并运行Flask应用
sys.path.insert(0, str(Path('.').absolute()))
from backend.app import app

if __name__ == '__main__':
    app.run(
        host=os.getenv('HOST', '0.0.0.0'),
        port=int(os.getenv('PORT', 5000)),
        debug=True
    ) 