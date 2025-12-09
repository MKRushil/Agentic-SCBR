"""NVIDIA 嵌入模型服務"""
import requests
from typing import List, Union
from config.settings import settings
from utils.logger import logger
import time

class NVIDIAEmbeddingService:
    """NVIDIA 嵌入模型API服務"""

    def __init__(self):
        self.config = settings.embedding
        self.api_url = f"{self.config.api_url}/embeddings"
        self.headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

    def embed_text(self, text: str) -> List[float]:
        """
        生成單個文本的向量嵌入

        Args:
            text: 待嵌入的文本

        Returns:
            向量列表
        """
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成文本向量

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        if not texts:
            return []

        # 分批處理
        all_embeddings = []
        batch_size = self.config.batch_size

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self._embed_batch(batch)
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """處理單個批次"""
        payload = {
            "input": texts,
            "model": self.config.model,
            "encoding_format": "float"
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
                embeddings = [item["embedding"] for item in data["data"]]

                logger.debug(f"成功生成 {len(embeddings)} 個向量")
                return embeddings

            except requests.exceptions.RequestException as e:
                if attempt < self.config.retry:
                    logger.warning(f"嵌入生成失敗,重試 {attempt + 1}/{self.config.retry}: {e}")
                    time.sleep(2 ** attempt)  # 指數退避
                else:
                    logger.error(f"嵌入生成最終失敗: {e}")
                    raise

        return []

    def embed_case(self, case: dict) -> List[float]:
        """
        為案例生成嵌入向量

        將案例的關鍵信息組合成文本後生成向量
        """
        # 構建案例文本表示
        case_text = self._case_to_text(case)
        return self.embed_text(case_text)

    def _case_to_text(self, case: dict) -> str:
        """將案例轉換為文本表示"""
        parts = []

        # 主訴
        if case.get("chief_complaint"):
            parts.append(f"主訴: {case['chief_complaint']}")

        # 症狀
        if case.get("symptoms"):
            symptoms_text = ", ".join(case["symptoms"][:10])  # 限制長度
            parts.append(f"症狀: {symptoms_text}")

        # 舌脈
        tongue = case.get("tongue", {})
        if tongue:
            tongue_text = f"舌{tongue.get('color', '')}{tongue.get('coating', '')}"
            parts.append(f"舌象: {tongue_text}")

        if case.get("pulse"):
            parts.append(f"脈象: {case['pulse']}")

        # 證型
        if case.get("syndrome"):
            parts.append(f"證型: {case['syndrome']}")

        # 治則
        if case.get("treatment_principle"):
            parts.append(f"治法: {case['treatment_principle']}")

        return "; ".join(parts)


# 全局實例
embedding_service = NVIDIAEmbeddingService()