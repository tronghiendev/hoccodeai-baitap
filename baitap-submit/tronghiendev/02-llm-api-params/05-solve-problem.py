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

user_input = input("What is your problem? ")

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": f"""# Role
Bạn là một chuyên gia lập trình Python chuyên nghiệp

# Task
Viết code Python để giải quyết bài toán sau

# Constraint
- Chỉ output code Python thuần túy, không có bất kỳ markdown formatting nào (không có ```python, ```, hay bất kỳ ký tự đặc biệt nào)
- Code phải đầy đủ và có thể chạy được ngay
- Import đầy đủ các thư viện cần thiết
- Code phải có đầy đủ các phần:
  + Import thư viện
  + Định nghĩa hàm/chức năng
  + Phần chạy chính
- Đảm bảo code chạy được và cho kết quả chính xác
- Sử dụng các best practices của Python
- Xử lý đầy đủ các trường hợp input
- KHÔNG giải thích thêm
- KHÔNG thêm bất kỳ text nào ngoài code Python
- Thêm comments đầy đủ cho code:
  + Docstring cho mỗi hàm/method
  + Comments giải thích logic phức tạp
  + Comments cho các biến quan trọng
  + Comments cho các phần xử lý đặc biệt
  + Comments theo chuẩn Python (PEP 257)
- Xử lý exception đầy đủ:
  + Try-except cho các thao tác có thể gây lỗi
  + Xử lý các loại exception phổ biến (ValueError, TypeError, ZeroDivisionError, v.v.)
  + Thông báo lỗi rõ ràng và thân thiện với người dùng
  + Log lỗi khi cần thiết
  + Có cơ chế retry khi phù hợp
  + Đảm bảo chương trình không crash khi có lỗi

Bài toán cần giải:
{user_input}""",
        }
    ],
    model="gemma2-9b-it",
)

# Lấy nội dung và loại bỏ markdown formatting nếu có
content = chat_completion.choices[0].message.content
content = content.replace("```python", "").replace("```", "").strip()

out_file = f"final.py"
with open(out_file, "w", encoding="utf-8") as file:
    file.write(content)

print(f"Code saved to {out_file}")
