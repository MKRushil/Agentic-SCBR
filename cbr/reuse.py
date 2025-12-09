"""CBR重用階段"""
from typing import Dict, Any, List
from utils.logger import logger

class CaseReuser:
    """案例重用器"""

    @staticmethod
    def reuse(similar_cases: List[Dict[str, Any]], current_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        重用相似案例的診療方案

        Args:
            similar_cases: 檢索到的相似案例列表
            current_case: 當前患者信息

        Returns:
            重用的診療建議
        """
        logger.info("開始重用相似案例...")

        if not similar_cases:
            logger.warning("沒有相似案例可供重用")
            return {
                "syndrome_suggestions": [],
                "formula_suggestions": [],
                "treatment_principles": [],
                "confidence": 0.0
            }

        # 提取證型建議
        syndrome_votes = {}
        formula_suggestions = []
        treatment_principles = set()

        total_weight = 0.0
        for case in similar_cases:
            weight = case.get('similarity_score', 0.0)
            total_weight += weight

            # 證型投票(加權)
            syndrome = case.get('syndrome', '')
            if syndrome:
                syndrome_votes[syndrome] = syndrome_votes.get(syndrome, 0) + weight

            # 收集方劑
            formula = case.get('formula', '')
            if formula:
                formula_suggestions.append({
                    'formula': formula,
                    'case_id': case.get('case_id'),
                    'similarity': weight,
                    'efficacy': case.get('efficacy_score', 0)
                })

            # 收集治則
            principle = case.get('treatment_principle', '')
            if principle:
                treatment_principles.add(principle)

        # 排序證型(按權重)
        sorted_syndromes = sorted(
            syndrome_votes.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # 排序方劑(按相似度和療效)
        formula_suggestions.sort(
            key=lambda x: (x['similarity'] * 0.6 + x['efficacy'] * 0.4),
            reverse=True
        )

        result = {
            "syndrome_suggestions": [
                {"syndrome": s, "confidence": w/total_weight if total_weight > 0 else 0}
                for s, w in sorted_syndromes
            ],
            "formula_suggestions": formula_suggestions[:3],  # 取前3個
            "treatment_principles": list(treatment_principles),
            "confidence": total_weight / len(similar_cases) if similar_cases else 0,
            "reference_cases": [c.get('case_id') for c in similar_cases]
        }

        logger.info(f"重用完成,推薦證型: {sorted_syndromes[0][0] if sorted_syndromes else 'Unknown'}")

        return result
