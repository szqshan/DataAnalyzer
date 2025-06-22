#!/usr/bin/env python3
# start_memory_service.py - 记忆管理服务启动脚本
# 功能：独立启动记忆管理API服务

import os
import sys
from pathlib import Path

# 添加backend目录到Python路径
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def main():
    """启动记忆管理服务"""
    print("🧠 DataAnalyzer 记忆管理服务")
    print("=" * 50)
    
    try:
        # 导入记忆管理API
        from memory_api import run_memory_api
        
        # 配置服务参数
        host = os.getenv('MEMORY_HOST', 'localhost')
        port = int(os.getenv('MEMORY_PORT', 5002))
        debug = os.getenv('MEMORY_DEBUG', 'False').lower() == 'true'
        
        print(f"🚀 启动配置:")
        print(f"   主机: {host}")
        print(f"   端口: {port}")
        print(f"   调试模式: {debug}")
        print("=" * 50)
        
        # 启动服务
        run_memory_api(host=host, port=port, debug=debug)
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保所有依赖已正确安装")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 记忆管理服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 