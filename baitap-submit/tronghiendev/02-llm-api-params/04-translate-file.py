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

user_input = input("Enter the file to translate: ")
target_language = input("Enter the target language: ")

# Extract just the filename from the full path
input_filename = os.path.basename(user_input)
base_name = os.path.splitext(input_filename)[0]

with open(user_input, "r") as file:
    content = file.read()

chunks = textwrap.wrap(content, 4000)
translated_chunks = []

for chunk in chunks:
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"""# Role
Bạn là một chuyên gia dịch thuật chuyên nghiệp

# Task
Dịch nội dung sau đây sang {target_language}

# Constraint
- Dịch chính xác nội dung gốc
- Giữ nguyên ý nghĩa và ngữ cảnh
- Bảo toàn các thuật ngữ chuyên môn
- Sử dụng ngôn ngữ tự nhiên, phù hợp với văn phong của {target_language}
- Không thêm hoặc bớt thông tin
- Đảm bảo tính nhất quán trong toàn bộ văn bản
- Chú ý đến các thành ngữ, tục ngữ và cách diễn đạt đặc thù
- Giữ nguyên định dạng văn bản (đoạn văn, dấu câu)

Nội dung cần dịch:
{chunk}""",
            }
        ],
        model="gemma2-9b-it",
    )
    translated_chunk = chat_completion.choices[0].message.content
    translated_chunks.append(translated_chunk)

final_translation = "\n".join(translated_chunks)

out_file = f"translated_{base_name}.txt"
with open(out_file, "w", encoding="utf-8") as file:
    file.write(final_translation)

print(f"Translation saved to {out_file}")
