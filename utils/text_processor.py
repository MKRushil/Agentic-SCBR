"""文本處理工具"""
import re
from typing import List, Dict

class TextProcessor:
    """中醫文本處理器"""

    @staticmethod
    def extract_symptoms(text: str) -> List[str]:
        """從文本中提取症狀"""
        # 簡化版:用頓號、逗號分隔
        symptoms = []
        # 移除標點符號並分割
        cleaned = re.sub(r'[,、。;;\s]+', ',', text)
        symptoms = [s.strip() for s in cleaned.split(',') if s.strip()]
        return symptoms

    @staticmethod
    def extract_tongue_pulse(text: str) -> Dict[str, str]:
        """提取舌脈信息"""
        result = {"tongue": "", "pulse": ""}

        # 提取舌象
        tongue_pattern = r'舌([^,。;]+)'
        tongue_match = re.search(tongue_pattern, text)
        if tongue_match:
            result["tongue"] = tongue_match.group(1)

        # 提取脈象
        pulse_pattern = r'脈([^,。;]+)'
        pulse_match = re.search(pulse_pattern, text)
        if pulse_match:
            result["pulse"] = pulse_match.group(1)

        return result

    @staticmethod
    def normalize_symptom(symptom: str) -> str:
        """標準化症狀術語"""
        # 簡化版:去除空白
        return symptom.strip()

    @staticmethod
    def calculate_text_similarity(text1: str, text2: str) -> float:
        """計算文本相似度(簡單版本)"""
        set1 = set(text1)
        set2 = set(text2)

        if not set1 or not set2:
            return 0.0

        intersection = set1 & set2
        union = set1 | set2

        return len(intersection) / len(union) if union else 0.0
