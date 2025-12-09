"""
Embedding Client - 向量嵌入客戶端
"""

import requests
from typing import List
from config.settings import settings
from utils.logger import logger

class EmbeddingClient:
    """嵌入向量客戶端"""

    def __init__(self):
        self.config = settings.embedding
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        })

    def embed(self, text: str) -> List[float]:
        """
        生成文本向量

        Args:
            text: 輸入文本

        Returns:
            向量列表
        """
        payload = {
            "input": text,
            "model": self.config.model,
            "encoding_format": "float"
        }

        try:
            response = self.session.post(
                f"{self.config.api_url}/embeddings",
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()

            result = response.json()
            embedding = result['data'][0]['embedding']

            return embedding

        except Exception as e:
            logger.error(f"Embedding 生成失敗: {e}")
            raise
