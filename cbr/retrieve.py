"""CBR檢索階段 - 支援向量檢索"""
from typing import Dict, Any, List
from knowledge.case_database import CaseDatabase
from knowledge.similarity_calculator import SimilarityCalculator
from utils.logger import logger
from config.settings import settings

class CaseRetriever:
    """案例檢索器 - 支援向量與傳統檢索"""

    def __init__(self):
        self.case_db = CaseDatabase()
        self.similarity_calc = SimilarityCalculator()
        self.top_k = settings.system.top_k_cases
        self.threshold = settings.system.similarity_threshold
        self.use_vector_search = settings.system.use_vector_search
        self.vector_store = None

        if self.use_vector_search:
            try:
                from knowledge.weaviate_store import WeaviateVectorStore
                from knowledge.embedding_service import embedding_service
                self.vector_store = WeaviateVectorStore()
                self.embedding_service = embedding_service
                logger.info("向量檢索已啟用")
            except Exception as e:
                logger.warning(f"向量庫初始化失敗,使用傳統檢索: {e}")
                self.use_vector_search = False

    def retrieve(self, current_case: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.info("開始檢索相似案例...")

        if self.use_vector_search and self.vector_store:
            return self._vector_retrieve(current_case)
        return self._traditional_retrieve(current_case)

    def _vector_retrieve(self, current_case: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.info("使用向量檢索...")
        try:
            query_vector = self.embedding_service.embed_case(current_case)
            similar_cases = self.vector_store.search_similar(query_vector, top_k=self.top_k)
            filtered = [c for c in similar_cases if c.get('similarity_score', 0) >= self.threshold]
            logger.info(f"向量檢索完成,找到 {len(filtered)} 個相似案例")
            return filtered
        except Exception as e:
            logger.error(f"向量檢索失敗: {e}")
            return self._traditional_retrieve(current_case)

    def _traditional_retrieve(self, current_case: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.info("使用傳統檢索...")
        all_cases = self.case_db.get_all_cases()
        similar_cases = self.similarity_calc.rank_cases_by_similarity(current_case, all_cases, self.top_k)
        filtered = [c for c in similar_cases if c.get('similarity_score', 0) >= self.threshold]
        logger.info(f"傳統檢索完成,找到 {len(filtered)} 個相似案例")
        return filtered
