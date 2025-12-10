import axios from 'axios'

// 規格書 7.0: 前端 API 設定
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 60000, // Timeout 60s (因應序列化與 LLM 推理耗時)
  headers: {
    'Content-Type': 'application/json'
  }
})

// 請求攔截器
apiClient.interceptors.request.use(config => {
  // 可以在此加入 Auth Token
  return config
}, error => {
  return Promise.reject(error)
})

// 回應攔截器 (Retry 邏輯可在此擴充)
apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.code === 'ECONNABORTED') {
      console.error('[API] Request timed out. System might be busy due to Serial Execution.')
    }
    return Promise.reject(error)
  }
)

export default apiClient