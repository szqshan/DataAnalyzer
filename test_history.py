#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试历史记录功能
"""

import sys
import os
from pathlib import Path

# 添加backend目录到Python路径
sys.path.append(str(Path(__file__).parent / 'backend'))

from conversation_history import ConversationHistoryManager
from user_middleware import user_manager

def test_history_manager():
    """测试历史记录管理器"""
    print("🧪 开始测试历史记录管理器...")
    
    # 创建测试用户
    test_user_id = "test_user_history"
    test_username = "测试用户"
    
    # 获取用户路径
    user_paths = user_manager.get_user_paths(test_user_id)
    
    # 创建历史记录管理器
    history_manager = ConversationHistoryManager(user_paths)
    
    # 测试数据
    test_user_data = {
        'user_id': test_user_id,
        'username': test_username
    }
    
    test_query = "分析数据的基本统计信息"
    test_system_prompt = "你是专业的数据分析师..."
    test_db_path = "/path/to/test.db"
    test_table_name = "test_table"
    
    try:
        # 1. 测试开始对话
        print("📝 测试开始对话...")
        conversation_id = history_manager.start_conversation(
            test_user_data, test_query, test_system_prompt, 
            test_db_path, test_table_name
        )
        print(f"✅ 对话ID: {conversation_id}")
        
        # 2. 测试更新消息
        print("📝 测试更新消息...")
        test_messages = [
            {"role": "user", "content": test_system_prompt},
            {"role": "assistant", "content": [{"type": "text", "text": "我来帮您分析数据..."}]}
        ]
        history_manager.update_conversation_messages(conversation_id, test_messages)
        print("✅ 消息更新成功")
        
        # 3. 测试更新工具调用
        print("🔧 测试更新工具调用...")
        test_tool_calls = [
            {
                "tool_name": "get_table_info",
                "tool_input": {"table_name": "test_table"},
                "tool_result": {"columns": ["id", "name", "value"]},
                "execution_time": "2024-01-01T12:00:00"
            }
        ]
        history_manager.update_tool_calls(conversation_id, test_tool_calls)
        print("✅ 工具调用更新成功")
        
        # 4. 测试完成对话
        print("✅ 测试完成对话...")
        history_manager.complete_conversation(
            conversation_id, 'completed', '分析完成，数据统计正常', 3
        )
        print("✅ 对话完成")
        
        # 5. 测试获取对话历史
        print("📚 测试获取对话历史...")
        conversations = history_manager.get_conversation_history(test_user_id, 10, 0)
        print(f"✅ 获取到 {len(conversations)} 条对话记录")
        
        # 6. 测试获取对话详情
        print("📋 测试获取对话详情...")
        conversation_detail = history_manager.get_conversation_detail(conversation_id)
        if conversation_detail:
            print(f"✅ 对话详情: {conversation_detail['user_query']}")
        else:
            print("❌ 获取对话详情失败")
        
        # 7. 测试获取统计信息
        print("📊 测试获取统计信息...")
        stats = history_manager.get_conversation_stats(test_user_id)
        print(f"✅ 统计信息: {stats}")
        
        # 8. 测试获取最近对话
        print("🕒 测试获取最近对话...")
        recent_conversations = history_manager.get_recent_conversations(test_user_id, 5)
        print(f"✅ 最近对话: {len(recent_conversations)} 条")
        
        print("\n🎉 所有测试通过！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_history_manager() 