#!/usr/bin/env python3
"""
智能数据库分析系统启动脚本 - 修复版
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

# 🔥 关键修复：加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()  # 加载 .env 文件
    print("✅ .env 文件已加载")
except ImportError:
    print("⚠️  python-dotenv 未安装，无法加载 .env 文件")
except Exception as e:
    print(f"⚠️  加载 .env 文件失败: {e}")

def check_requirements():
    """检查环境要求"""
    print("🔍 检查环境要求...")
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        return False
    
    # 检查必要的包
    required_packages = ['flask', 'anthropic', 'pandas']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少必要的包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    print("✅ 环境检查通过")
    return True

def check_api_key():
    """检查API密钥"""
    print("🔑 检查API密钥...")
    
    # 检查 .env 文件是否存在
    env_file = Path(".env")
    if env_file.exists():
        print(f"✅ 找到 .env 文件: {env_file.absolute()}")
        
        # 读取 .env 文件内容（用于调试）
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'ANTHROPIC_API_KEY' in content:
                    print("✅ .env 文件中包含 ANTHROPIC_API_KEY")
                else:
                    print("❌ .env 文件中未找到 ANTHROPIC_API_KEY")
                    return False
        except Exception as e:
            print(f"❌ 读取 .env 文件失败: {e}")
    else:
        print("⚠️  未找到 .env 文件")
    
    # 检查环境变量
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ 环境变量中未找到 ANTHROPIC_API_KEY")
        print("\n🔧 解决方案:")
        print("1. 检查 .env 文件格式:")
        print("   ANTHROPIC_API_KEY=sk-your-key-here")
        print("   (注意：等号两边不要有空格，不要用引号)")
        print("\n2. 或手动设置环境变量:")
        print("   Windows PowerShell: $env:ANTHROPIC_API_KEY='your_key_here'")
        print("   Windows CMD: set ANTHROPIC_API_KEY=your_key_here")
        print("   macOS/Linux: export ANTHROPIC_API_KEY='your_key_here'")
        return False
    
    # 验证密钥格式
    if not api_key.startswith('sk-'):
        print("❌ API密钥格式不正确，应该以 'sk-' 开头")
        return False
    
    print(f"✅ API密钥已配置 (长度: {len(api_key)} 字符)")
    return True

def create_directories():
    """创建必要的目录"""
    print("📁 创建项目目录...")
    
    directories = [
        'uploads',
        'reports', 
        'data',
        'logs'
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        dir_path.mkdir(exist_ok=True)
        print(f"  ✅ {directory}/ 目录已创建")
    
    print("✅ 目录创建完成")

def check_project_structure():
    """检查项目结构"""
    print("📋 检查项目结构...")
    
    required_files = [
        'backend/app.py',
        'backend/datatest1_7_5.py', 
        'frontend/index.html'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ 缺少必要文件: {missing_files}")
        print("请确保按照部署指南创建所有必要文件")
        return False
    
    print("✅ 项目结构检查通过")
    return True

def start_backend():
    """启动后端服务"""
    print("🔧 启动后端服务...")
    
    # 设置环境变量
    os.environ['FLASK_APP'] = 'backend/app.py'
    os.environ['FLASK_ENV'] = 'development'
    
    try:
        # 确保 backend 目录在 Python 路径中
        backend_path = Path('backend').absolute()
        if str(backend_path) not in sys.path:
            sys.path.insert(0, str(backend_path))
        
        # 启动Flask应用
        from backend.app import app
        
        print("✅ 后端服务启动成功")
        print("📡 API地址: http://localhost:5000/api")
        
        return app
    
    except ImportError as e:
        print(f"❌ 导入后端模块失败: {e}")
        print("请检查 backend/app.py 文件是否存在")
        return None
    except Exception as e:
        print(f"❌ 后端启动失败: {e}")
        return None

def open_frontend():
    """打开前端界面"""
    print("🌐 准备打开前端界面...")
    
    frontend_path = Path("frontend/index.html").absolute()
    
    if not frontend_path.exists():
        print("❌ 前端文件不存在: frontend/index.html")
        return False
    
    try:
        # 等待后端启动
        time.sleep(2)
        
        # 打开浏览器
        webbrowser.open(f'file://{frontend_path}')
        print("✅ 前端界面已打开")
        print(f"📱 前端地址: file://{frontend_path}")
        return True
    
    except Exception as e:
        print(f"❌ 打开前端失败: {e}")
        print(f"请手动打开: {frontend_path}")
        return False

def main():
    """主启动函数"""
    print("🤖 智能数据库分析系统 v2.1")
    print("=" * 60)
    
    # 显示当前工作目录
    print(f"📂 当前目录: {Path.cwd()}")
    
    # 环境检查
    if not check_requirements():
        input("按回车键退出...")
        sys.exit(1)
    
    if not check_api_key():
        input("按回车键退出...")
        sys.exit(1)
    
    # 项目结构检查
    if not check_project_structure():
        input("按回车键退出...")
        sys.exit(1)
    
    # 创建目录
    create_directories()
    
    # 启动后端
    app = start_backend()
    if not app:
        input("按回车键退出...")
        sys.exit(1)
    
    # 打开前端
    open_frontend()
    
    print("\n" + "=" * 60)
    print("🎉 系统启动完成!")
    print("📱 前端界面: file:///.../frontend/index.html")
    print("🔧 后端API: http://localhost:5000/api")
    print("📊 健康检查: http://localhost:5000/api/health")
    print("\n💡 使用说明:")
    print("  1. 在前端界面上传CSV文件")
    print("  2. 使用自然语言描述分析需求")
    print("  3. 查看生成的HTML分析报告")
    print("  4. 导出和分享分析结果")
    print("\n按 Ctrl+C 停止服务")
    print("=" * 60)
    
    try:
        # 启动Flask应用
        app.run(
            host=os.getenv('HOST', '0.0.0.0'),
            port=int(os.getenv('PORT', 5000)),
            debug=True,
            use_reloader=False  # 避免重复启动
        )
    except KeyboardInterrupt:
        print("\n👋 服务已停止，再见!")
    except Exception as e:
        print(f"\n❌ 服务运行错误: {e}")

if __name__ == "__main__":
    main()