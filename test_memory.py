from backend.datatest1_7_5 import ConversationMemory

# 创建记忆实例
mem = ConversationMemory("test_memory.json")

# 测试字典输入
print("测试1: 字典输入")
mem.save_context(
    {"input": "测试查询", "tools": [{"tool_name": "test_tool", "input": {"param": "value"}, "result": {"success": True}}]}, 
    {"output": "测试响应", "messages": [{"role": "user", "content": "测试查询"}, {"role": "assistant", "content": "测试响应"}]}
)

# 测试字符串输入
print("\n测试2: 字符串输入")
mem.save_context("测试字符串查询", "测试字符串响应")

print("\n测试完成，检查test_memory.json文件") 