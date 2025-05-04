from openai import OpenAI
from dotenv import load_dotenv
import os
import requests
import textwrap

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Nếu các bạn lấy dùng TogetherAI
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    # Làm theo hướng dẫn trong bài, truy cập https://console.groq.com/keys để lấy API Key nha
    api_key=OPENAI_API_KEY,
)

user_input = input("Enter the URL to summarize: ")

url = f"https://r.jina.ai/{user_input}"
headers = {
    "Authorization": "Bearer jina_fc717192e5aa4e0494fbbf199454e7bfigBI1Z_Hptc8eB2YXrDGMSNRxHmc"
}

response = requests.get(url, headers=headers)
content = response.text

chunks = textwrap.wrap(content, 4000)
summaries = []

for chunk in chunks:
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"""# Role
Bạn là một chuyên gia tóm tắt nội dung chuyên nghiệp

# Task
Tóm tắt nội dung sau đây thành 2-3 câu ngắn gọn, súc tích

# Constraint
- Giữ nguyên ngôn ngữ gốc của nội dung
- Tập trung vào thông tin quan trọng nhất
- Không thêm thông tin không có trong nội dung gốc
- Giữ nguyên các thuật ngữ chuyên môn
- Đảm bảo tính chính xác của thông tin
- Sử dụng ngôn ngữ tự nhiên, dễ hiểu

Nội dung cần tóm tắt:
{chunk}""",
            }
        ],
        model="gemma2-9b-it",
    )
    summary = chat_completion.choices[0].message.content
    summaries.append(summary)

final_summary = "\n".join(summaries)

print("Summary: ", final_summary)
