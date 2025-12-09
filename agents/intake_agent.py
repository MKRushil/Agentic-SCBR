"""信息採集與結構化Agent"""
import json
import re
from typing import Dict, Any
from .base_agent import BaseAgent
from utils.logger import logger
from utils.text_processor import TextProcessor

class IntakeAgent(BaseAgent):
    """問診信息採集Agent"""

    def __init__(self):
        super().__init__('intake_agent')
        self.text_processor = TextProcessor()

    def process(self, input_text: str, **kwargs) -> Dict[str, Any]:
        """
        處理患者輸入的自由文本,轉換為結構化數據

        Args:
            input_text: 醫師輸入的患者信息

        Returns:
            結構化的四診數據
        """
        logger.info(f"開始處理患者信息...")

        # 提取症狀
        symptoms = self._extract_symptoms_from_text(input_text)

        # 提取舌脈
        tongue_pulse = self.text_processor.extract_tongue_pulse(input_text)

        # 提取主訴
        chief_complaint = self._extract_chief_complaint(input_text)

        # 構建結構化數據
        structured_data = {
            "chief_complaint": chief_complaint,
            "symptoms": symptoms,
            "tongue": {
                "description": tongue_pulse.get("tongue", ""),
                "color": self._parse_tongue_color(tongue_pulse.get("tongue", "")),
                "coating": self._parse_tongue_coating(tongue_pulse.get("tongue", ""))
            },
            "pulse": tongue_pulse.get("pulse", ""),
            "other_signs": self._extract_other_signs(input_text)
        }

        logger.info(f"信息採集完成,提取到 {len(symptoms)} 個症狀")

        return {
            "status": "success",
            "agent": self.agent_name,
            "data": structured_data,
            "raw_input": input_text
        }

    def _extract_symptoms_from_text(self, text: str) -> list:
        """從文本提取症狀"""
        # 常見症狀關鍵詞
        symptom_keywords = [
            "頭暈", "頭痛", "乏力", "心悸", "失眠", "咳嗽", "氣短",
            "胸悶", "脘腹脹", "疼痛", "惡心", "嘔吐", "腹瀉", "便秘",
            "畏寒", "發熱", "盜汗", "自汗", "口乾", "口苦", "納差",
            "腰痛", "膝軟", "肢冷", "煩躁", "抑鬱", "耳鳴"
        ]

        symptoms = []
        for keyword in symptom_keywords:
            if keyword in text:
                # 提取包含關鍵詞的短語
                pattern = f'[^,。;]*{keyword}[^,。;]*'
                matches = re.findall(pattern, text)
                symptoms.extend(matches)

        # 去重
        return list(set(symptoms))

    def _extract_chief_complaint(self, text: str) -> str:
        """提取主訴"""
        # 尋找第一句話作為主訴
        sentences = re.split(r'[。;]', text)
        return sentences[0].strip() if sentences else ""

    def _parse_tongue_color(self, tongue_desc: str) -> str:
        """解析舌質顏色"""
        colors = ["淡", "紅", "絳", "紫", "青"]
        for color in colors:
            if color in tongue_desc:
                return color
        return ""

    def _parse_tongue_coating(self, tongue_desc: str) -> str:
        """解析舌苔"""
        coatings = ["白", "黃", "灰", "黑", "膩", "薄", "厚", "少", "無苔"]
        found_coatings = []
        for coating in coatings:
            if coating in tongue_desc:
                found_coatings.append(coating)
        return "".join(found_coatings)

    def _extract_other_signs(self, text: str) -> str:
        """提取其他體徵"""
        # 簡化版:返回原文
        return text
