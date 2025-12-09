"""檢索Agent"""
from typing import Dict, Any, List
from .base_agent import BaseAgent
from knowledge.case_database import CaseDatabase
from knowledge.similarity_calculator import SimilarityCalculator
from utils.logger import logger

class RetrievalAgent(BaseAgent):
    """案例檢索Agent"""

    def __init__(self):
        super().__init__('retrieval_agent')
        self.case_db = CaseDatabase()
        self.similarity_calc = SimilarityCalculator()

    def process(self, current_case: Dict[str, Any], top_k: int = 5, **kwargs) -> Dict[str, Any]:
        """檢索相似案例"""
        logger.info(f"開始檢索相似案例 (Top-{top_k})...")

        all_cases = self.case_db.get_all_cases()

        # 計算相似度並排序
        similar_cases = self.similarity_calc.rank_cases_by_similarity(
            current_case, all_cases, top_k
        )

        # 過濾低相似度案例
        filtered_cases = [c for c in similar_cases if c.get('similarity_score', 0) >= 0.3]

        result = {
            "status": "success",
            "agent": self.agent_name,
            "data": {
                "similar_cases": filtered_cases,
                "total_found": len(filtered_cases),
                "search_summary": self._generate_summary(filtered_cases)
            }
        }

        logger.info(f"檢索完成,找到 {len(filtered_cases)} 個相似案例")
        return result

    def _generate_summary(self, cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成檢索摘要"""
        if not cases:
            return {"message": "未找到相似案例"}

        syndromes = {}
        for case in cases:
            syndrome = case.get('syndrome', 'Unknown')
            syndromes[syndrome] = syndromes.get(syndrome, 0) + 1

        return {
            "highest_similarity": cases[0].get('similarity_score', 0) if cases else 0,
            "syndrome_distribution": syndromes,
            "average_efficacy": sum(c.get('efficacy_score', 0) for c in cases) / len(cases)
        }
