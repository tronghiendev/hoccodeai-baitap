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

messages = [{"role": "user", "content": "Tóm tắt nội dung trang web https://tuoitre.vn/cac-nha-khoa-hoc-nga-bao-tu-manh-nhat-20-nam-sap-do-bo-trai-dat-2024051020334196.htm"}]

print("Bước 1: Gửi message lên cho LLM")
pprint(messages)

response = client.chat.completions.create(
    model=COMPLETION_MODEL,
    messages=messages,
    tools=tools
)

print("Bước 2: LLM đọc và phân tích ngữ cảnh LLM")
pprint(response)

print("Bước 3: Lấy kết quả từ LLM")
tool_call = response.choices[0].message.tool_calls[0]

pprint(tool_call)
arguments = json.loads(tool_call.function.arguments)

print("Bước 4: Chạy function view_website ở máy mình")

if tool_call.function.name == 'view_website':
    website_content = view_website(
        arguments.get('url'))
    print(f"Kết quả bước 4: {website_content}")

    print("Bước 5: Gửi kết quả lên cho LLM")
    messages.append(response.choices[0].message)
    messages.append({
        "role": "tool",
        "content": website_content,
        "tool_call_id": tool_call.id
    })

    pprint(messages)

    final_response = client.chat.completions.create(
        model=COMPLETION_MODEL,
        messages=messages
        # Ở đây không có tools cũng không sao, vì ta không cần gọi nữa
    )
    print(
        f"Kết quả cuối cùng từ LLM: {final_response.choices[0].message.content}.")
