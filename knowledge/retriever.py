"""
Case Retriever - 案例檢索器
"""

from typing import Dict, Any, List
from utils.logger import logger
from knowledge.case_manager import CaseManager
from knowledge.weaviate_store import WeaviateVectorStore
from utils.embedding_client import EmbeddingClient
from config.settings import settings

class CaseRetriever:
    """案例檢索器"""

    def __init__(self):
        self.case_manager = CaseManager()
        self.embedding_client = EmbeddingClient()

        # 嘗試初始化向量庫
        self.vector_store = None
        if settings.system.use_vector_search:
            try:
                self.vector_store = WeaviateVectorStore()
                logger.info("✅ 向量檢索已啟用")
            except Exception as e:
                logger.warning(f"向量庫初始化失敗，使用傳統檢索: {e}")

        logger.info("檢索器初始化完成")

    def retrieve(self, query: Dict[str, Any], top_k: int = None) -> List[Dict[str, Any]]:
        """
        檢索相似案例

        Args:
            query: 查詢數據
            top_k: 返回案例數量

        Returns:
            相似案例列表
        """
        if top_k is None:
            top_k = settings.system.top_k_cases

        # 優先使用向量檢索
        if self.vector_store and self.vector_store.client:
            try:
                return self._vector_retrieve(query, top_k)
            except Exception as e:
                logger.warning(f"向量檢索失敗，回退到傳統檢索: {e}")

        # 傳統檢索
        return self._traditional_retrieve(query, top_k)

    def _vector_retrieve(self, query: Dict[str, Any], top_k: int) -> List[Dict[str, Any]]:
        """向量檢索"""
        # 構建查詢文本
        query_text = self._build_query_text(query)

        # 獲取向量
        query_vector = self.embedding_client.embed(query_text)

        # 向量搜索
        results = self.vector_store.search_similar(query_vector, top_k)

        logger.info(f"向量檢索找到 {len(results)} 個案例")
        return results

    def _traditional_retrieve(self, query: Dict[str, Any], top_k: int) -> List[Dict[str, Any]]:
        """傳統關鍵詞檢索"""
        symptoms = query.get('symptoms', [])
        pulse = query.get('pulse', '')

        # 從案例庫搜索
        criteria = {
            'symptoms': symptoms,
            'pulse': pulse,
            'top_k': top_k
        }

        results = self.case_manager.search_cases(criteria)
        logger.info(f"傳統檢索找到 {len(results)} 個案例")
        return results

    def _build_query_text(self, query: Dict[str, Any]) -> str:
        """構建查詢文本"""
        parts = []

        if 'chief_complaint' in query:
            parts.append(f"主訴: {query['chief_complaint']}")

        if 'symptoms' in query:
            parts.append(f"症狀: {', '.join(query['symptoms'])}")

        if 'tongue' in query:
            tongue = query['tongue']
            parts.append(f"舌象: {tongue.get('color', '')}舌，{tongue.get('coating', '')}苔")

        if 'pulse' in query:
            parts.append(f"脈象: {query['pulse']}")

        return '\n'.join(parts)

    def close(self):
        """關閉資源"""
        if self.vector_store:
            self.vector_store.close()
