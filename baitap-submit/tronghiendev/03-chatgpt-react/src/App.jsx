import OpenAI from 'openai';
import { useState, useEffect } from "react"

// Kiểm tra xem tin nhắn có phải là của bot không
function isBotMessage(chatMessage) {
  return chatMessage.role === 'assistant'
}

function App() {
  const [message, setMessage] = useState('')
  const [chatHistory, setChatHistory] = useState([])
  const [apiKey, setApiKey] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [useLocalLLM, setUseLocalLLM] = useState(false)
  const [localBaseURL, setLocalBaseURL] = useState('')
  const [localModel, setLocalModel] = useState('')
  
  // Load API key from localStorage when component mounts
  useEffect(() => {
    const savedApiKey = localStorage.getItem('groqApiKey')
    if (savedApiKey) {
      setApiKey(savedApiKey)
    }
    
    // Load local LLM settings if previously saved
    const savedLocalBaseURL = localStorage.getItem('localBaseURL')
    const savedLocalModel = localStorage.getItem('localModel')
    const savedUseLocalLLM = localStorage.getItem('useLocalLLM') === 'true'
    
    if (savedLocalBaseURL) setLocalBaseURL(savedLocalBaseURL)
    if (savedLocalModel) setLocalModel(savedLocalModel)
    if (savedUseLocalLLM) setUseLocalLLM(savedUseLocalLLM)
    
    // Load chat history from localStorage
    const savedChatHistory = localStorage.getItem('chatHistory')
    if (savedChatHistory) {
      try {
        const parsedHistory = JSON.parse(savedChatHistory)
        setChatHistory(parsedHistory)
      } catch (error) {
        console.error('Error parsing chat history from localStorage:', error)
      }
    }
  }, [])
  
  // Save chat history to localStorage whenever it changes
  useEffect(() => {
    if (chatHistory.length > 0) {
      localStorage.setItem('chatHistory', JSON.stringify(chatHistory))
    }
  }, [chatHistory])
  
  // Hàm xử lý khi nhấn nút nhập API key
  const handleEnterApiKey = () => {
    const userApiKey = window.prompt('Vui lòng nhập API key của Groq để sử dụng ứng dụng:')
    if (userApiKey) {
      setApiKey(userApiKey)
      // Save to localStorage
      localStorage.setItem('groqApiKey', userApiKey)
    }
  }
  
  // Hàm xử lý khi nhấn nút kết nối LLM local
  const handleConnectLocalLLM = () => {
    const baseURL = window.prompt('Vui lòng nhập base URL (ví dụ: http://127.0.0.1:1234/v1):')
    if (baseURL) {
      setLocalBaseURL(baseURL)
      localStorage.setItem('localBaseURL', baseURL)
      
      const model = window.prompt('Vui lòng nhập tên model (ví dụ: gemma-3-4b-it-qat):')
      if (model) {
        setLocalModel(model)
        localStorage.setItem('localModel', model)
        setUseLocalLLM(true)
        localStorage.setItem('useLocalLLM', 'true')
      }
    }
  }
  
  // Hàm chuyển đổi giữa LLM local và cloud
  const toggleLLMMode = () => {
    setUseLocalLLM(!useLocalLLM)
    localStorage.setItem('useLocalLLM', (!useLocalLLM).toString())
  }

  // Hàm xóa lịch sử chat
  const clearChatHistory = () => {
    setChatHistory([])
    localStorage.removeItem('chatHistory')
  }
  
  // Gọi hàm này khi người dùng bấm enter, gửi tin nhắn
  const submitForm = async (e) => {
    e.preventDefault()

    if (!useLocalLLM && !apiKey) {
      alert('Vui lòng nhập API key để sử dụng ứng dụng')
      const userApiKey = window.prompt('Vui lòng nhập API key của Groq để sử dụng ứng dụng:')
      if (userApiKey) {
        setApiKey(userApiKey)
        // Save to localStorage
        localStorage.setItem('groqApiKey', userApiKey)
      }
      return
    }
    
    if (useLocalLLM && (!localBaseURL || !localModel)) {
      alert('Vui lòng nhập thông tin kết nối LLM local')
      handleConnectLocalLLM()
      return
    }

    if (!message.trim()) return

    // Set loading state to true
    setIsLoading(true)

    // Clear message ban đầu
    setMessage('')

    // Thêm tin nhắn người dùng và tin nhắn của bot vào danh sách
    const userMessage = { role: 'user', content: message }
    const botMessage = { role: 'assistant', content: "" }
    
    // Add user message and empty bot message to chat history
    setChatHistory([...chatHistory, userMessage, botMessage])
    
    try {
      // Khởi tạo OpenAI instance với cấu hình phù hợp
      const openai = new OpenAI({
        baseURL: useLocalLLM ? localBaseURL : 'https://api.groq.com/openai/v1',
        apiKey: useLocalLLM ? '' : apiKey,
        // Khi chạy ở browser, cần thêm option này
        dangerouslyAllowBrowser: true,
      });
      
      // Gọi OpenAI API để lấy kết quả
      const stream = await openai.chat.completions.create({
        messages: [...chatHistory, userMessage],
        model: useLocalLLM ? localModel : 'gemma2-9b-it',
        stream: true,
      });

      let accumulatedContent = "";
      
      // Process each chunk as it arrives
      for await (const chunk of stream) {
        const content = chunk.choices[0]?.delta?.content || "";
        accumulatedContent += content;
        
        // Update bot's message with accumulated content so far
        setChatHistory(currentHistory => {
          const newHistory = [...currentHistory];
          newHistory[newHistory.length - 1] = { 
            role: 'assistant', 
            content: accumulatedContent 
          };
          return newHistory;
        });
      }
      
      // Set loading state back to false after response is complete
      setIsLoading(false)
    } catch (error) {
      console.error("Error during streaming:", error);
      setChatHistory(currentHistory => {
        const newHistory = [...currentHistory];
        newHistory[newHistory.length - 1] = { 
          role: 'assistant', 
          content: "Đã xảy ra lỗi khi gọi API. Vui lòng kiểm tra cấu hình kết nối hoặc thử lại sau." 
        };
        return newHistory;
      });
      
      // Set loading state back to false on error
      setIsLoading(false)
    }
  }

  return (
    <div className="bg-gray-100 h-screen flex flex-col">
      <div className="container mx-auto p-4 flex flex-col h-full max-w-2xl">
        <div className="mb-4">
          <h1 className="text-2xl font-bold text-center mb-3">ChatUI với React + OpenAI</h1>
          <div className="flex flex-wrap justify-center gap-2">
            {useLocalLLM ? (
              <>
                {localBaseURL && localModel ? (
                  <span className="text-green-600 text-sm flex items-center">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    LLM Local: {localModel}
                  </span>
                ) : (
                  <span className="text-red-600 text-sm">LLM Local chưa được cấu hình</span>
                )}
                <button 
                  onClick={handleConnectLocalLLM}
                  className="bg-purple-500 text-white px-3 py-2 rounded hover:bg-purple-600"
                >
                  Cấu hình LLM Local
                </button>
              </>
            ) : (
              <>
                {apiKey && (
                  <span className="text-green-600 text-sm flex items-center">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    API Key đã được nhập
                  </span>
                )}
                <button 
                  onClick={handleEnterApiKey}
                  className="bg-green-500 text-white px-3 py-2 rounded hover:bg-green-600"
                >
                  {apiKey ? 'Cập nhật API Key' : 'Nhập API Key'}
                </button>
              </>
            )}
            <button 
              onClick={toggleLLMMode}
              className={`text-white px-3 py-2 rounded ${useLocalLLM ? 'bg-blue-500 hover:bg-blue-600' : 'bg-purple-500 hover:bg-purple-600'}`}
            >
              {useLocalLLM ? 'Chuyển sang Groq' : 'Chuyển sang LLM Local'}
            </button>
          </div>
        </div>

        <form className="flex" onSubmit={submitForm}>
          <input 
            type="text" 
            placeholder={isLoading ? "Đang chờ phản hồi..." : "Tin nhắn của bạn..."}
            value={message} 
            onChange={e => setMessage(e.target.value)}
            className="flex-grow p-2 rounded-l border border-gray-300" 
            disabled={isLoading}
          />
          <button 
            type="submit"
            className={`text-white px-4 py-2 rounded-r ${isLoading ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-500 hover:bg-blue-600'}`}
            disabled={isLoading}
          >
            {isLoading ? 'Đang xử lý...' : 'Gửi tin nhắn'}
          </button>
          <button 
            type="button"
            onClick={clearChatHistory}
            className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 ml-2"
          >
            Xóa lịch sử
          </button>
        </form>

        <div className="flex-grow overflow-y-auto mt-4 bg-white rounded shadow p-4">
          {chatHistory.map((chatMessage, i) => (
            <div key={i} className={`mb-2 ${isBotMessage(chatMessage) ? 'text-right' : ''}`}>
              <p className="text-gray-600 text-sm">{isBotMessage(chatMessage) ? 'Bot' : 'User'}</p>
              <p className={`p-2 rounded-lg inline-block ${isBotMessage(chatMessage) ? 'bg-green-100' : 'bg-blue-100'}`}>{chatMessage.content}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default App
