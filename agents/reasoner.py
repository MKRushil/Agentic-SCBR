"""
Case Reasoner - 案例推理器
"""

from typing import Dict, Any, List
from utils.logger import logger
from utils.llm_client import LLMClient

class CaseReasoner:
    """案例推理器"""

    def __init__(self):
        self.llm = LLMClient()
        logger.info("推理器初始化完成")

    def reason(self, query: Dict[str, Any], similar_cases: List[Dict]) -> Dict[str, Any]:
        """
        基於相似案例進行推理

        Args:
            query: 查詢數據
            similar_cases: 相似案例列表

        Returns:
            推理結果
        """
        # 構建提示詞
        prompt = self._build_prompt(query, similar_cases)

        # 調用 LLM
        logger.info("調用 LLM 進行推理...")
        response = self.llm.generate(prompt)

        # 解析結果
        result = self._parse_response(response)

        return result

    def _build_prompt(self, query: Dict[str, Any], cases: List[Dict]) -> str:
        """構建推理提示詞"""

        # 當前患者信息
        patient_info = f"""
【當前患者】
主訴: {query.get('chief_complaint', '')}
症狀: {', '.join(query.get('symptoms', []))}
舌象: {query.get('tongue', {}).get('color', '')}舌，{query.get('tongue', {}).get('coating', '')}苔
脈象: {query.get('pulse', '')}
"""

        # 相似案例
        cases_text = ""
        for i, case in enumerate(cases[:3], 1):
            cases_text += f"""
【參考案例 {i}】
證型: {case.get('syndrome', '')}
治法: {case.get('treatment_principle', '')}
方劑: {case.get('formula', '')}
藥物: {', '.join(case.get('herbs', []))}
相似度: {case.get('similarity_score', 0):.2%}
"""

        prompt = f"""你是一位經驗豐富的中醫師。請根據患者症狀和參考案例,給出中醫診斷。

{patient_info}

{cases_text}

請按以下格式輸出診斷結果:

證型: [證型名稱]
治法: [治療原則]
方劑: [推薦方劑]
藥物: [藥物1, 藥物2, ...]
推理依據: [簡要說明診斷依據]

注意:
1. 綜合考慮症狀、舌脈和參考案例
2. 證型要準確，治法要明確
3. 方劑和藥物要符合證型
4. 推理依據要清晰簡潔
"""
        return prompt

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """解析 LLM 響應"""
        result = {
            "syndrome": "",
            "treatment_principle": "",
            "formula": "",
            "herbs": [],
            "reasoning": "",
            "confidence": 0.75
        }

        try:
            lines = response.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('證型:'):
                    result['syndrome'] = line.replace('證型:', '').strip()
                elif line.startswith('治法:'):
                    result['treatment_principle'] = line.replace('治法:', '').strip()
                elif line.startswith('方劑:'):
                    result['formula'] = line.replace('方劑:', '').strip()
                elif line.startswith('藥物:'):
                    herbs_str = line.replace('藥物:', '').strip()
                    result['herbs'] = [h.strip() for h in herbs_str.split(',')]
                elif line.startswith('推理依據:'):
                    result['reasoning'] = line.replace('推理依據:', '').strip()

            # 如果沒有解析到完整結果，使用整個響應
            if not result['syndrome']:
                result['reasoning'] = response
                result['syndrome'] = "待專家審核"
                result['treatment_principle'] = "待專家審核"
                result['formula'] = "待專家審核"

        except Exception as e:
            logger.error(f"解析響應失敗: {e}")
            result['reasoning'] = response

        return result
