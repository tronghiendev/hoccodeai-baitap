from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Nếu các bạn lấy dùng TogetherAI
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    # Làm theo hướng dẫn trong bài, truy cập https://console.groq.com/keys để lấy API Key nha
    api_key=OPENAI_API_KEY,
)

user_input = input("type your question: ")

stream = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": user_input,
        }
    ],
    model="gemma2-9b-it",
    stream=True
)

for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="")
