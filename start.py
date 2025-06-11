#!/usr/bin/env python3
"""
智能数据库分析系统启动脚本 - 精简版
版本: 3.0.0 - P0阶段精简版
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path
import platform

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
except Exception:
    pass

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Python版本必须 >= 3.7")
        return False
    return True

def check_requirements():
    """检查环境要求"""
    required_packages = ['flask', 'anthropic', 'pandas', 'flask_cors']
    
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
    
    return True

def check_api_key():
    """检查API密钥"""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ 未找到 ANTHROPIC_API_KEY 环境变量")
        print("请在 .env 文件中设置: ANTHROPIC_API_KEY=sk-your-key-here")
        return False
    
    if not api_key.startswith('sk-'):
        print("❌ API密钥格式不正确，应该以 'sk-' 开头")
        return False
    
    return True

def check_project_structure():
    """检查项目结构"""
    required_files = [
        'backend/user_middleware.py',
        'backend/datatest1_7_5.py',
        'frontend/index.html',
        'frontend/api.js'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ 缺少必要文件: {missing_files}")
        return False
    
    return True

def create_directories():
    """创建必要的目录"""
    directories = ['data', 'logs']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)

def start_backend():
    """启动后端服务"""
    # 确保 backend 目录在 Python 路径中
    backend_path = Path('backend').absolute()
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
    
    try:
        os.chdir('backend')
        
        if not Path('app.py').exists():
            print("❌ backend/app.py 文件不存在")
            return None
        
        # 导入Flask应用
        from app import app
        return app
    
    except Exception as e:
        print(f"❌ 后端启动失败: {e}")
        return None

def open_frontend():
    """打开前端界面"""
    # 回到根目录
    os.chdir('..')
    
    frontend_path = Path("frontend/index.html").absolute()
    
    if not frontend_path.exists():
        print("❌ 前端文件不存在: frontend/index.html")
        return False
    
    try:
        # 等待后端启动
        time.sleep(2)
        
        # 打开浏览器
        webbrowser.open(f'file://{frontend_path}')
        return True
    
    except Exception as e:
        print(f"❌ 打开前端失败: {e}")
        return False

def main():
    """主启动函数"""
    print("🤖 智能数据库分析系统启动中...")
    
    # 快速检查
    if not check_python_version():
        input("按回车键退出...")
        return
    
    if not check_requirements():
        input("按回车键退出...")
        return
    
    if not check_api_key():
        input("按回车键退出...")
        return
    
    if not check_project_structure():
        input("按回车键退出...")
        return
    
    # 创建目录
    create_directories()
    
    # 启动后端
    app = start_backend()
    if not app:
        input("按回车键退出...")
        return
    
    # 打开前端
    open_frontend()
    
    print("✅ 系统启动完成!")
    print("📱 前端: http://localhost:8080 或查看浏览器")
    print("🔧 后端: http://localhost:5000/api")
    print("\n按 Ctrl+C 停止服务")
    print("-" * 50)
    
    try:
        # 启动Flask应用 - 静默模式
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        
        app.run(
            host=os.getenv('HOST', '0.0.0.0'),
            port=int(os.getenv('PORT', 5000)),
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"\n❌ 服务运行错误: {e}")

if __name__ == "__main__":
    main()