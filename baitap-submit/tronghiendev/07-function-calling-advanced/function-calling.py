from pprint import pprint
import json
from openai import OpenAI
import os
from dotenv import load_dotenv
import requests
import inspect
from pydantic import TypeAdapter

load_dotenv()

# Bài 2: Implement hàm `view_website`, sử dụng `requests` và JinaAI để đọc markdown từ URL
def view_website(url: str):
    """Convert a webpage to markdown using JinaAI Reader API"""
    try:
        # Make request to JinaAI Reader API
        response = requests.get(f"https://r.jina.ai/{url}")
        response.raise_for_status()  # Raise exception for bad status codes
        
        # Return the markdown content
        return response.text
    except requests.RequestException as e:
        return f"Error fetching website content: {str(e)}"


# Bài 1: Thay vì tự viết object `tools`, hãy xem lại bài trước, sửa code và dùng `inspect` và `TypeAdapter` để define `tools`
tools = [
    {
        "type": "function",
        "function": {
            "name": "view_website",
            "description": inspect.getdoc(view_website),
            "parameters": TypeAdapter(view_website).json_schema(),
        }
    }
]

# https://platform.openai.com/api-keys
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)
COMPLETION_MODEL = "gemma2-9b-it"

messages = [
    {"role": "system", "content": """# Role
Bạn là một trợ lý AI chuyên nghiệp trong việc tóm tắt nội dung website. Bạn có khả năng đọc và phân tích nội dung từ các trang web và tạo ra những bản tóm tắt ngắn gọn, dễ hiểu.

# Task
- Đọc và phân tích nội dung website được cung cấp
- Tạo bản tóm tắt ngắn gọn, tập trung vào thông tin quan trọng nhất
- Đảm bảo tóm tắt dễ hiểu và hữu ích cho người đọc

# Format
Bản tóm tắt nên:
- Ngắn gọn, súc tích
- Tập trung vào thông tin chính
- Được viết bằng tiếng Việt
- Có cấu trúc rõ ràng, dễ đọc
    """},
    {"role": "user", "content": "Tóm tắt nội dung trang web https://tuoitre.vn/cac-nha-khoa-hoc-nga-bao-tu-manh-nhat-20-nam-sap-do-bo-trai-dat-2024051020334196.htm"},
]

response = client.chat.completions.create(
    model=COMPLETION_MODEL,
    messages=messages,
    tools=tools
)

tool_call = response.choices[0].message.tool_calls[0]

arguments = json.loads(tool_call.function.arguments)

if tool_call.function.name == 'view_website':
    website_content = view_website(
        arguments.get('url'))

    messages.append(response.choices[0].message)
    messages.append({
        "role": "tool",
        "content": json.dumps({"result": website_content}),
        "tool_call_id": tool_call.id
    })

    final_response = client.chat.completions.create(
        model=COMPLETION_MODEL,
        messages=messages
        # Ở đây không có tools cũng không sao, vì ta không cần gọi nữa
    )
    
    print(
        f"Kết quả cuối cùng từ LLM: {final_response.choices[0].message.content}.")
