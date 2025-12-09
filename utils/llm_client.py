"""
LLM Client - 大語言模型客戶端
"""

import requests
from typing import Optional
from config.settings import settings
from utils.logger import logger

class LLMClient:
    """LLM 客戶端"""

    def __init__(self):
        self.config = settings.llm
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        })

    def generate(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """
        生成文本

        Args:
            prompt: 提示詞
            max_tokens: 最大 token 數

        Returns:
            生成的文本
        """
        if max_tokens is None:
            max_tokens = self.config.max_tokens

        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": self.config.temperature,
            "max_tokens": max_tokens
        }

        try:
            response = self.session.post(
                f"{self.config.api_url}/chat/completions",
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()

            result = response.json()
            content = result['choices'][0]['message']['content']

            return content

        except Exception as e:
            logger.error(f"LLM 調用失敗: {e}")
            raise
