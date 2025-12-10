import httpx
import logging
from typing import Dict, Any, List
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class NvidiaClient:
    """
    規格書 1.2: 資源調度策略與 API 封裝
    負責與 NVIDIA NIM 服務溝通。
    注意：並發控制 (Concurrency Control) 由 Orchestrator 的 Global Lock 處理，
    此處僅負責單次 HTTP 請求。
    """
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.LLM_API_URL
        self.model = settings.LLM_MODEL_NAME
        self.embed_model = settings.EMBEDDING_MODEL_NAME
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def get_embedding(self, text: str) -> List[float]:
        """調用 nvidia/nv-embedqa-e5-v5"""
        url = f"{self.base_url}/embeddings"
        payload = {
            "input": [text],
            "model": self.embed_model,
            "input_type": "query",
            "encoding_format": "float"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, json=payload, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                return data['data'][0]['embedding']
            except Exception as e:
                logger.error(f"Embedding API Failed: {str(e)}")
                # 在真實環境中應有 Retry 機制或 fallback
                raise e

    async def generate_completion(self, 
                                messages: List[Dict[str, str]], 
                                temperature: float = 0.2,
                                max_tokens: int = 1024) -> str:
        """調用 nvidia/llama-3.3-nemotron-super-49b-v1.5"""
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "top_p": 0.7,
            "max_tokens": max_tokens,
            "stream": False
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, json=payload, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                content = data['choices'][0]['message']['content']
                return content
            except Exception as e:
                logger.error(f"LLM Generation Failed: {str(e)}")
                raise e