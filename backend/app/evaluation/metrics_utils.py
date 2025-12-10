import numpy as np
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class MetricsUtils:
    """
    規格書 6.2 評估指標共用算式庫
    """

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """計算餘弦相似度"""
        if not v1 or not v2:
            return 0.0
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0
        return dot_product / (norm_v1 * norm_v2)

    @staticmethod
    def calculate_top_k_accuracy(predicted_vector: List[float], gt_vector: List[float], threshold: float = 0.9) -> bool:
        """指標 1: Top-k Semantic Accuracy"""
        score = MetricsUtils.cosine_similarity(predicted_vector, gt_vector)
        return score > threshold

    @staticmethod
    def calculate_semantic_recall(candidates: List[str], ground_truth: str) -> float:
        """指標 2: Semantic Recall (簡易版：字串包含檢查)"""
        # 實際應使用 Embedding 比較，此處簡化為關鍵字匹配
        hits = [1 for c in candidates if ground_truth in c]
        return 1.0 if hits else 0.0

    @staticmethod
    def calculate_info_gain(prev_entropy: float, current_entropy: float) -> float:
        """指標 8: Info Gain"""
        return max(0.0, prev_entropy - current_entropy)

    @staticmethod
    def calculate_f1_score(precision: float, recall: float, beta: float = 2.0) -> float:
        """指標 4: F1-Score (Weighted F2)"""
        if precision + recall == 0:
            return 0.0
        return (1 + beta**2) * (precision * recall) / ((beta**2 * precision) + recall)