from dotenv import load_dotenv
from openai import OpenAI
import os
import inspect
from pydantic import TypeAdapter
import requests
import yfinance as yf
import json


def get_symbol(company: str) -> str:
    """
    Retrieve the stock symbol for a specified company using the Yahoo Finance API.
    :param company: The name of the company for which to retrieve the stock symbol, e.g., 'Nvidia'.
    :output: The stock symbol for the specified company.
    """
    url = "https://query2.finance.yahoo.com/v1/finance/search"
    params = {"q": company, "country": "United States"}
    user_agents = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"}
    res = requests.get(
        url=url,
        params=params,
        headers=user_agents)

    data = res.json()
    symbol = data['quotes'][0]['symbol']
    return symbol


def get_stock_price(symbol: str):
    """
    Retrieve the most recent stock price data for a specified company using the Yahoo Finance API via the yfinance Python library.
    :param symbol: The stock symbol for which to retrieve data, e.g., 'NVDA' for Nvidia.
    :output: A dictionary containing the most recent stock price data.
    """
    stock = yf.Ticker(symbol)
    hist = stock.history(period="1d", interval="1m")
    latest = hist.iloc[-1]
    return {
        "timestamp": str(latest.name),
        "open": latest["Open"],
        "high": latest["High"],
        "low": latest["Low"],
        "close": latest["Close"],
        "volume": latest["Volume"]
    }


tools = [
    {
        "type": "function",
        "function": {
            "name": "get_symbol",
            "description": inspect.getdoc(get_symbol),
            "parameters": TypeAdapter(get_symbol).json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_price",
            "description": inspect.getdoc(get_stock_price),
            "parameters": TypeAdapter(get_stock_price).json_schema(),
        },
    }
]

FUNCTION_MAP = {
    "get_symbol": get_symbol,
    "get_stock_price": get_stock_price
}


load_dotenv()
# Đọc từ file .env cùng thư mục, nhưng đừng commit nha!
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)


def get_completion(messages):
    response = client.chat.completions.create(
        model="gemma2-9b-it",
        messages=messages,
        tools=tools,
        # Để temparature=0 để kết quả ổn định sau nhiều lần chạy
        temperature=0
    )
    return response


# Bắt đầu làm bài tập từ line này!

messages = [
    {
        "role": "system",
        "content": """# Role
Bạn là một chuyên gia chứng khoán hài hước và thân thiện. Bạn có khả năng phân tích và tóm tắt thông tin từ các trang web về tài chính và chứng khoán.

# Task
- Tóm tắt và phân tích thông tin từ các bài báo, tin tức về chứng khoán
- Trả lời các câu hỏi về thị trường chứng khoán một cách hài hước nhưng vẫn chuyên nghiệp
- Nếu người dùng hỏi về giá cổ phiếu nhưng không cung cấp tên công ty, hãy hỏi lại họ một cách hài hước

# Format
- Sử dụng ngôn ngữ tự nhiên, dễ hiểu
- Thêm các yếu tố hài hước phù hợp
- Giữ nguyên các thuật ngữ chuyên môn về chứng khoán
- Đảm bảo tính chính xác của thông tin
- Nếu thiếu thông tin, hãy hỏi lại người dùng một cách thân thiện"""
    },
    {"role": "assistant", "content": "Xin chào! Tôi là chuyên gia chứng khoán của bạn. Bạn muốn biết gì về thị trường hôm nay? 😊"}
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

    response = get_completion(messages)
    first_choice = response.choices[0]
    finish_reason = first_choice.finish_reason

    # Loop cho tới khi model báo stop và đưa ra kết quả
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

        # Chờ kết quả từ LLM
        response = get_completion(messages)
        first_choice = response.choices[0]
        finish_reason = first_choice.finish_reason

    # In ra kết quả sau khi đã thoát khỏi vòng lặp
    print("assistant: ", first_choice.message.content)
