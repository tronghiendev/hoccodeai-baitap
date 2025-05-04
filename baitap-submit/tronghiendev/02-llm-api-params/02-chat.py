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

messages = [
    {
        "role": "system",
        "content": "You are a helpful assistant that can answer questions and help with tasks.",
    },
    {
        "role": "assistant",
        "content": "Hello, I'm a helpful assistant. How can I help you today?",
    }
]

for message in messages:
    if message['role'] != 'system':
        print(f"{message['role']}: {message['content']}")

while True:
    user_input = input("user: ")

    messages.append({
        "role": "user",
        "content": user_input,
    })

    print("assistant: ", end="")

    stream = client.chat.completions.create(
        messages=messages,
        model="gemma2-9b-it",
        stream=True
    )

    for chunk in stream:
        print(chunk.choices[0].delta.content or "", end="")

    print()
