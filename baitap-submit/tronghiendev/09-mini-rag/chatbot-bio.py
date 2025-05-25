# 1. Dùng chunking để làm bot trả lời tiểu sử người nổi tiếng, anime v...v
#   - <https://en.wikipedia.org/wiki/S%C6%A1n_T%C3%B9ng_M-TP>
#   - <https://en.wikipedia.org/wiki/Jujutsu_Kaisen>

from wikipediaapi import Wikipedia
from openai import OpenAI
import chromadb
from chromadb.utils import embedding_functions
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

COLLECTION_NAME = "bac_nguyen_nhat_anh"
# Ở đây, ta dùng `PersistentClient` để lưu trữ dữ liệu trong một file trong thư mục `./data`.
client = chromadb.PersistentClient(path="./data")
client.heartbeat()

# Mặc định, chroma DB sử dụng `all-MiniLM-L6-v2` của Sentence Transformers
# mà mình đã hướng dẫn ở bài trước để tạo embeddings.
embedding_function = embedding_functions.DefaultEmbeddingFunction()

# Ngoài ra, bạn có thể sử dụng mô hình embedding của OpenAI để có hiệu suất tốt hơn
# Nhưng cần đăng ký và có API key của OpenAI
# embedding_function = embedding_functions.OpenAIEmbeddingFunction(api_key=OPENAI_API_KEY, model_name="text-embedding-3-small")
try:
    collection = client.get_collection(name=COLLECTION_NAME)
except chromadb.errors.NotFoundError:
    collection = client.create_collection(name=COLLECTION_NAME,
                                        embedding_function=embedding_function)


# Sử dụng wikipediaapi để lấy dữ liệu từ https://en.wikipedia.org/wiki/Nguyễn_Nhật_Ánh
wiki = Wikipedia('HocCodeAI/0.0 (https://hoccodeai.com)', 'en')
doc = wiki.page('Nguyễn_Nhật_Ánh').text

# In dữ liệu ra
print(doc)

# Chia nhỏ văn bản một cách đơn giản
paragraphs = doc.split('\n\n')

# Lưu trữ các đoạn văn bản trong collection
for index, paragraph in enumerate(paragraphs):
    collection.add(documents=[paragraph], ids=[str(index)])

# In thử kết quả
print(collection.peek())

# https://platform.openai.com/api-keys
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)
query = "What is Nguyễn Nhật Ánh most famous seriesg?"

q = collection.query(query_texts=[query], n_results=3)
CONTEXT = q["documents"][0]

prompt = f"""
Use the following CONTEXT to answer the QUESTION at the end.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
Use an unbiased and journalistic tone.

CONTEXT: {CONTEXT}

QUESTION: {query}
"""

# Sử dụng RAG để trả lời câu hỏi, trong biến `prompt` đã có ngữ cảnh
response = client.chat.completions.create(
    model="gemma2-9b-it",
    messages=[
        {"role": "user", "content": prompt},
    ]
)

print(response.choices[0].message.content)
