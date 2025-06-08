import os
from dotenv import load_dotenv
from anthropic import Anthropic

# 加载 .env 文件
load_dotenv()

client = Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
    base_url=os.environ.get("BASE_URL")
)

message = client.messages.create(
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": "Hello, who are you?",
        }
    ],
    model="claude-sonnet-4-20250514",
)
print(message.content)