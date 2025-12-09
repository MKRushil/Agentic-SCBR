"""NVIDIA LLM API 服務"""
import requests
import json
from typing import List, Dict, Any, Optional
from config.settings import settings
from utils.logger import logger
import time

class NVIDIALLMService:
    """NVIDIA LLM API 服務"""

    def __init__(self):
        self.config = settings.llm
        self.api_url = f"{self.config.api_url}/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        調用 LLM 進行對話

        Args:
            messages: 對話消息列表 [{"role": "system/user/assistant", "content": "..."}]
            temperature: 溫度參數
            max_tokens: 最大token數

        Returns:
            LLM 回覆內容
        """
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
            "top_p": 0.9,
            "stream": False
        }

        for attempt in range(self.config.retry + 1):
            try:
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=self.config.timeout
                )
                response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"]

                # 記錄token使用情況
                if "usage" in data:
                    usage = data["usage"]
                    logger.debug(
                        f"Token使用: {usage.get('total_tokens')} "
                        f"(prompt: {usage.get('prompt_tokens')}, "
                        f"completion: {usage.get('completion_tokens')})"
                    )

                return content

            except requests.exceptions.RequestException as e:
                if attempt < self.config.retry:
                    logger.warning(f"LLM調用失敗,重試 {attempt + 1}/{self.config.retry}: {e}")
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"LLM調用最終失敗: {e}")
                    # 返回錯誤提示而不是拋出異常
                    return f"[LLM調用失敗: {str(e)}]"

        return "[LLM調用失敗]"

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        簡化的生成接口

        Args:
            prompt: 用戶提示詞
            system_prompt: 系統提示詞

        Returns:
            生成的內容
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        return self.chat(messages)


# 全局實例
llm_service = NVIDIALLMService()