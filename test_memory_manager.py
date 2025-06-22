#!/usr/bin/env python3
# test_memory_manager.py - 记忆管理功能测试脚本
# 功能：测试记忆管理器的各项功能

import sys
import os
import json
import requests
from pathlib import Path

# 添加backend目录到Python路径
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def test_memory_api():
    """测试记忆管理API"""
    base_url = "http://localhost:5002"
    
    # 测试用户信息
    test_user = {
        "userId": "test_user_001",
        "username": "TestUser",
        "apiKey": "sk-test-key-here"  # 需要替换为真实的API密钥
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-User-ID': test_user['userId'],
        'X-Username': test_user['username'],
        'X-API-Key': test_user['apiKey']
    }
    
    print("🧠 记忆管理API测试")
    print("=" * 50)
    
    # 1. 健康检查
    print("1. 测试健康检查...")
    try:
        response = requests.get(f"{base_url}/memory/health")
        if response.status_code == 200:
            print("✅ 健康检查通过")
            print(f"   响应: {response.json()}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return
    
    # 2. 获取对话列表
    print("\n2. 测试获取对话列表...")
    try:
        response = requests.post(f"{base_url}/memory/conversations", 
                               headers=headers, 
                               json={})
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                conversations = data.get('conversations', [])
                print(f"✅ 找到 {len(conversations)} 个对话")
                for conv in conversations[:3]:  # 只显示前3个
                    print(f"   - {conv['conversation_name']} ({conv['conversation_id']})")
                
                # 如果有对话，测试记忆分析
                if conversations:
                    test_conversation_id = conversations[0]['conversation_id']
                    print(f"\n3. 测试记忆分析 (对话: {test_conversation_id})...")
                    
                    # 先获取统计信息
                    stats_response = requests.post(f"{base_url}/memory/stats",
                                                 headers=headers,
                                                 json={"conversation_id": test_conversation_id})
                    if stats_response.status_code == 200:
                        stats = stats_response.json()
                        if stats['success']:
                            print(f"✅ 统计信息获取成功:")
                            print(f"   总消息数: {stats.get('total_messages')}")
                            print(f"   活跃消息: {stats.get('active_messages')}")
                            print(f"   已删除消息: {stats.get('deleted_messages')}")
                            print(f"   重要消息: {stats.get('important_messages')}")
                            print(f"   预估token: {stats.get('estimated_tokens')}")
                        else:
                            print(f"❌ 统计信息获取失败: {stats['message']}")
                    
                    # 注意：记忆分析需要真实的API密钥，这里只做接口测试
                    print(f"\n⚠️  记忆分析需要有效的API密钥，当前使用测试密钥")
                    print(f"   如需完整测试，请在test_user中设置真实的API密钥")
                    
                else:
                    print("   暂无对话记录可供测试")
            else:
                print(f"❌ 获取对话列表失败: {data['message']}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_memory_manager_directly():
    """直接测试记忆管理器（需要真实API密钥）"""
    print("\n🔧 直接测试记忆管理器")
    print("=" * 50)
    
    # 检查是否有真实的API密钥
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key or api_key.startswith('sk-test'):
        print("⚠️  需要设置真实的ANTHROPIC_API_KEY环境变量")
        print("   export ANTHROPIC_API_KEY=sk-your-real-key-here")
        return
    
    try:
        from memory_manager import MemoryManager
        
        # 创建记忆管理器
        memory_manager = MemoryManager(api_key)
        print("✅ 记忆管理器创建成功")
        
        # 这里可以添加更多直接测试
        print("   记忆管理器已准备就绪，可以进行实际测试")
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
    except Exception as e:
        print(f"❌ 创建失败: {e}")

def show_usage():
    """显示使用说明"""
    print("📖 记忆管理测试使用说明")
    print("=" * 50)
    print("1. 启动记忆管理服务:")
    print("   python start_memory_service.py")
    print()
    print("2. 运行API测试:")
    print("   python test_memory_manager.py")
    print()
    print("3. 环境变量配置:")
    print("   ANTHROPIC_API_KEY=sk-your-key-here")
    print("   MEMORY_HOST=localhost")
    print("   MEMORY_PORT=5002")
    print()
    print("4. API接口:")
    print("   POST /memory/analyze - 分析对话记忆")
    print("   POST /memory/stats - 获取记忆统计")
    print("   POST /memory/conversations - 获取对话列表")
    print("   GET  /memory/health - 健康检查")

def main():
    """主测试函数"""
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        show_usage()
        return
    
    print("🧠 DataAnalyzer 记忆管理测试")
    print("=" * 50)
    
    # 测试API接口
    test_memory_api()
    
    # 直接测试记忆管理器
    test_memory_manager_directly()
    
    print("\n" + "=" * 50)
    print("测试完成！")
    print("如需查看使用说明，请运行: python test_memory_manager.py --help")

if __name__ == "__main__":
    main() 