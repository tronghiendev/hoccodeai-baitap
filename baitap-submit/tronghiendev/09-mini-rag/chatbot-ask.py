# 2. Thay vì hardcode `doc = wiki.page('Hayao_Miyazaki').text`, sử dụng function calling để:
#   - Lấy thông tin cần tìm từ câu hỏi
#   - Dùng `wiki.page` để lấy thông tin về
#   - Sử dụng RAG để có kết quả trả lời đúng.

from wikipediaapi import Wikipedia
from openai import OpenAI
import chromadb
from chromadb.utils import embedding_functions
import os
from dotenv import load_dotenv
import inspect
from pydantic import TypeAdapter
import json
import urllib.parse
import unicodedata

# Load environment variables
load_dotenv()

# Ở đây, ta dùng `PersistentClient` để lưu trữ dữ liệu trong một file trong thư mục `./data`.
client = chromadb.PersistentClient(path="./data")
client.heartbeat()

# Mặc định, chroma DB sử dụng `all-MiniLM-L6-v2` của Sentence Transformers
# mà mình đã hướng dẫn ở bài trước để tạo embeddings.
embedding_function = embedding_functions.DefaultEmbeddingFunction()

def memory(page_name: str):
    """
    Lấy thông tin từ Wikipedia và lưu vào ChromaDB
    :param page_name: Tên trang Wikipedia cần lấy thông tin
    :return: Tên collection đã tạo
    """
    wiki = Wikipedia('HocCodeAI/0.0 (https://hoccodeai.com)', 'en')
    doc = wiki.page(page_name).text

    # Chia nhỏ văn bản một cách đơn giản
    paragraphs = doc.split('\n\n')
    
    # Chuyển đổi tên thành không dấu và thay thế khoảng trắng
    collection_name = unicodedata.normalize('NFKD', page_name).encode('ASCII', 'ignore').decode('ASCII').replace(" ", "_")
    
    try:
        collection = client.get_collection(name=collection_name)
    except chromadb.errors.NotFoundError:
        collection = client.create_collection(name=collection_name,
                                        embedding_function=embedding_function)
        # Lưu trữ các đoạn văn bản trong collection
        for index, paragraph in enumerate(paragraphs):
            collection.add(documents=[paragraph], ids=[str(index)])
    
    return {"collection_name": collection_name}

def query_data(collection_name: str, query: str):
    """
    Truy vấn thông tin từ ChromaDB
    :param collection_name: Tên collection ChromaDB cần truy vấn
    :param query: Câu truy vấn
    :return: Kết quả truy vấn
    """
    collection = client.get_collection(name=collection_name)
    q = collection.query(query_texts=[query], n_results=3)

    return {"documents": q["documents"][0]}

tools = [
    {
        "type": "function",
        "function": {
            "name": "memory",
            "description": inspect.getdoc(memory),
            "parameters": TypeAdapter(memory).json_schema(),
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_data",
            "description": inspect.getdoc(query_data),
            "parameters": TypeAdapter(query_data).json_schema(),
        }
    }
]

FUNCTION_MAP = {
    "memory": memory,
    "query_data": query_data
}

messages = [
    {
        "role": "system",
        "content": """# Role
Bạn là một trợ lý phân tích nhân vật chuyên nghiệp, tập trung vào việc phân tích người nổi tiếng, nghệ sĩ và nhân vật công chúng. Chuyên môn của bạn là cung cấp thông tin chi tiết, chính xác và có cấu trúc tốt về cuộc đời, sự nghiệp và thành tựu của họ.

# Task
1. Quy trình xử lý câu hỏi:
   - Gọi tool memory với tên người để lấy thông tin từ Wikipedia và lưu vào ChromaDB
   - Lấy collection_name từ kết quả trả về của tool memory
   - Gọi tool query_data với collection_name và câu hỏi để lấy thông tin từ ChromaDB
   - Trả lời dựa trên thông tin đã truy vấn được

2. Nguyên tắc trả lời:
   - Chỉ trả lời dựa trên thông tin có sẵn từ Wikipedia
   - Không yêu cầu người dùng cung cấp thêm thông tin
   - Nếu không tìm thấy thông tin, trả lời "Tôi không tìm thấy thông tin về [tên người] trong cơ sở dữ liệu"
   - Nếu thông tin không đầy đủ, trả lời dựa trên những gì có sẵn

# Format
- Bắt đầu với phần giới thiệu ngắn gọn về người đó
- Trả lời trực tiếp vào câu hỏi của người dùng
- Sắp xếp thông tin theo cách rõ ràng, có cấu trúc"""
    },
    {"role": "assistant", "content": "Xin chào! Tôi là trợ lý phân tích nhân vật. Bạn muốn biết gì về ai?"}
]

for message in messages:
    if message['role'] != 'system':
        print(f"{message['role']}: {message['content']}")

# https://platform.openai.com/api-keys
openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

COMPLETION_MODEL = "gemma2-9b-it"

def get_completion(messages):
    response = openai_client.chat.completions.create(
        model=COMPLETION_MODEL,
        messages=messages,
        tools=tools
    )
    return response

while True:
    user_input = input("user: ")

    messages.append({
        "role": "user",
        "content": user_input,
    })

    response = get_completion(messages)
    first_choice = response.choices[0]
    finish_reason = first_choice.finish_reason

    while finish_reason != "stop":
        tool_call = first_choice.message.tool_calls[0]

        tool_call_function = tool_call.function
        tool_call_arguments = json.loads(tool_call_function.arguments)

        tool_function = FUNCTION_MAP[tool_call_function.name]
        result = tool_function(**tool_call_arguments)

        messages.append(first_choice.message)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": tool_call_function.name,
            "content": json.dumps({"result": result})
        })

        response = get_completion(messages)
        first_choice = response.choices[0]
        finish_reason = first_choice.finish_reason

    print("assistant: ", first_choice.message.content)
