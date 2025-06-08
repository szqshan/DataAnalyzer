# test_env.py
from dotenv import load_dotenv
import os

print("测试 .env 文件加载...")
load_dotenv()

api_key = os.getenv('ANTHROPIC_API_KEY')
print(f"API Key: {api_key[:10]}...{api_key[-5:] if api_key else 'None'}")

if api_key:
    print("✅ API密钥加载成功")
else:
    print("❌ API密钥加载失败")