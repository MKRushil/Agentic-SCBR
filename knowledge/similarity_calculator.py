"""案例相似度計算"""
from typing import Dict, Any, List
import math

class SimilarityCalculator:
    """案例相似度計算器"""

    @staticmethod
    def calculate_case_similarity(case1: Dict[str, Any], case2: Dict[str, Any]) -> float:
        """
        計算兩個案例的綜合相似度

        考慮因素:
        1. 症狀相似度 (權重: 0.4)
        2. 舌象相似度 (權重: 0.2)
        3. 脈象相似度 (權重: 0.2)
        4. 證型相似度 (權重: 0.2)
        """
        # 症狀相似度
        symptom_sim = SimilarityCalculator._symptom_similarity(
            case1.get('symptoms', []),
            case2.get('symptoms', [])
        )

        # 舌象相似度
        tongue_sim = SimilarityCalculator._tongue_similarity(
            case1.get('tongue', {}),
            case2.get('tongue', {})
        )

        # 脈象相似度
        pulse_sim = SimilarityCalculator._pulse_similarity(
            case1.get('pulse', ''),
            case2.get('pulse', '')
        )

        # 證型相似度
        syndrome_sim = 1.0 if case1.get('syndrome') == case2.get('syndrome') else 0.0

        # 加權計算
        total_similarity = (
            symptom_sim * 0.4 +
            tongue_sim * 0.2 +
            pulse_sim * 0.2 +
            syndrome_sim * 0.2
        )

        return round(total_similarity, 3)

    @staticmethod
    def _symptom_similarity(symptoms1: List[str], symptoms2: List[str]) -> float:
        """計算症狀相似度 (Jaccard相似度)"""
        if not symptoms1 or not symptoms2:
            return 0.0

        set1 = set(symptoms1)
        set2 = set(symptoms2)

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    @staticmethod
    def _tongue_similarity(tongue1: Dict[str, str], tongue2: Dict[str, str]) -> float:
        """計算舌象相似度"""
        if not tongue1 or not tongue2:
            return 0.0

        score = 0.0

        # 舌質相似
        if tongue1.get('color') == tongue2.get('color'):
            score += 0.5

        # 舌苔相似
        coating1 = tongue1.get('coating', '')
        coating2 = tongue2.get('coating', '')

        if coating1 and coating2:
            # 計算字符重疊
            common_chars = set(coating1) & set(coating2)
            score += 0.5 * (len(common_chars) / max(len(coating1), len(coating2)))

        return score

    @staticmethod
    def _pulse_similarity(pulse1: str, pulse2: str) -> float:
        """計算脈象相似度"""
        if not pulse1 or not pulse2:
            return 0.0

        # 簡單的字符匹配
        set1 = set(pulse1)
        set2 = set(pulse2)

        if not set1 or not set2:
            return 0.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    @staticmethod
    def rank_cases_by_similarity(
        current_case: Dict[str, Any],
        candidate_cases: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        對案例按相似度排序

        Returns:
            排序後的案例列表,每個案例包含 similarity_score 字段
        """
        scored_cases = []

        for case in candidate_cases:
            similarity = SimilarityCalculator.calculate_case_similarity(current_case, case)
            case_with_score = case.copy()
            case_with_score['similarity_score'] = similarity
            scored_cases.append(case_with_score)

        # 按相似度降序排序
        scored_cases.sort(key=lambda x: x['similarity_score'], reverse=True)

        return scored_cases[:top_k]
