#!/usr/bin/env python3
"""
后端连接测试脚本 - 快速诊断问题
"""

import requests
import json
import time
import subprocess
import sys
from pathlib import Path

def test_port_5000():
    """测试5000端口是否可访问"""
    print("🔍 测试端口5000...")
    
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex(('localhost', 5000))
        sock.close()
        
        if result == 0:
            print("✅ 端口5000可以访问")
            return True
        else:
            print("❌ 端口5000无法访问")
            return False
            
    except Exception as e:
        print(f"❌ 端口测试失败: {e}")
        return False

def test_basic_connection():
    """基础连接测试"""
    print("\n🔍 测试基础HTTP连接...")
    
    try:
        response = requests.get('http://localhost:5000/api/health', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 健康检查成功!")
            print(f"   状态: {data.get('status')}")
            print(f"   版本: {data.get('version')}")
            print(f"   服务: {data.get('service')}")
            return True
        else:
            print(f"❌ 健康检查失败: HTTP {response.status_code}")
            print(f"   响应: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接被拒绝 - 后端服务未启动")
        return False
    except requests.exceptions.Timeout:
        print("❌ 连接超时")
        return False
    except Exception as e:
        print(f"❌ 连接异常: {e}")
        return False

def test_user_api():
    """测试用户API"""
    print("\n🔍 测试用户API...")
    
    headers = {
        'X-User-ID': 'test_user_001',
        'X-Username': '测试用户',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get('http://localhost:5000/api/status', headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 用户API测试成功!")
            print(f"   系统就绪: {data.get('system_ready')}")
            print(f"   数据库连接: {data.get('database_connected')}")
            print(f"   用户: {data.get('user_info', {}).get('username')}")
            return True
        else:
            print(f"❌ 用户API失败: HTTP {response.status_code}")
            print(f"   响应: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ 用户API异常: {e}")
        return False

def check_flask_process():
    """检查Flask进程"""
    print("\n🔍 检查Flask进程...")
    
    try:
        # Windows
        if sys.platform == 'win32':
            result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
            if ':5000' in result.stdout:
                print("✅ 检测到5000端口被使用")
                lines = result.stdout.split('\n')
                for line in lines:
                    if ':5000' in line and 'LISTENING' in line:
                        print(f"   {line.strip()}")
                return True
            else:
                print("❌ 5000端口未被占用")
                return False
        else:
            # Linux/Mac
            result = subprocess.run(['lsof', '-i', ':5000'], capture_output=True, text=True)
            if result.stdout:
                print("✅ 检测到5000端口被使用")
                print(f"   {result.stdout}")
                return True
            else:
                print("❌ 5000端口未被占用")
                return False
                
    except Exception as e:
        print(f"⚠️  进程检查失败: {e}")
        return False

def check_file_structure():
    """检查文件结构"""
    print("\n🔍 检查关键文件...")
    
    required_files = {
        'backend/app.py': '后端主文件',
        'backend/user_middleware.py': '用户中间件',
        'backend/datatest1_7_5.py': '数据分析器',
        '.env': '环境配置文件'
    }
    
    missing_files = []
    for file_path, description in required_files.items():
        if Path(file_path).exists():
            size = Path(file_path).stat().st_size
            print(f"✅ {description}: {file_path} ({size:,} 字节)")
        else:
            print(f"❌ {description}: {file_path} - 文件不存在")
            missing_files.append(file_path)
    
    return len(missing_files) == 0

def check_environment():
    """检查环境变量"""
    print("\n🔍 检查环境配置...")
    
    import os
    from dotenv import load_dotenv
    
    # 加载.env文件
    load_dotenv()
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if api_key:
        print(f"✅ ANTHROPIC_API_KEY 已设置 (长度: {len(api_key)})")
        if api_key.startswith('sk-'):
            print("✅ API密钥格式正确")
            return True
        else:
            print("❌ API密钥格式不正确")
            return False
    else:
        print("❌ ANTHROPIC_API_KEY 未设置")
        return False

def provide_solutions():
    """提供解决方案"""
    print("\n" + "="*60)
    print("🔧 问题解决方案:")
    print("="*60)
    
    print("\n1. 如果端口5000未被占用:")
    print("   - 确保Flask服务已启动: python start.py")
    print("   - 检查是否有报错信息")
    print("   - 手动启动: cd backend && python app.py")
    
    print("\n2. 如果API连接失败:")
    print("   - 检查防火墙设置")
    print("   - 确认Flask监听地址: 0.0.0.0:5000")
    print("   - 尝试使用 127.0.0.1:5000 而不是 localhost:5000")
    
    print("\n3. 如果用户API失败:")
    print("   - 检查用户中间件是否正确导入")
    print("   - 确认数据目录权限")
    print("   - 查看后端控制台错误日志")
    
    print("\n4. 如果环境配置问题:")
    print("   - 检查.env文件格式: ANTHROPIC_API_KEY=sk-your-key")
    print("   - 重新安装依赖: pip install -r requirements.txt")
    print("   - 手动设置环境变量")

def main():
    """主诊断函数"""
    print("🚀 智能数据库分析系统 - 后端连接诊断工具")
    print("="*60)
    
    all_tests_passed = True
    
    # 1. 检查文件结构
    if not check_file_structure():
        all_tests_passed = False
    
    # 2. 检查环境配置
    if not check_environment():
        all_tests_passed = False
    
    # 3. 检查Flask进程
    if not check_flask_process():
        all_tests_passed = False
    
    # 4. 测试端口
    if not test_port_5000():
        all_tests_passed = False
    
    # 5. 测试基础连接
    if not test_basic_connection():
        all_tests_passed = False
    
    # 6. 测试用户API
    if not test_user_api():
        all_tests_passed = False
    
    print("\n" + "="*60)
    if all_tests_passed:
        print("🎉 所有测试通过！后端服务正常运行")
        print("💡 如果前端仍有问题，请检查浏览器控制台错误")
    else:
        print("❌ 检测到问题，请参考以下解决方案")
        provide_solutions()
    
    print("="*60)

if __name__ == "__main__":
    main()