"""病機推理Agent"""
from typing import Dict, Any, List
from .base_agent import BaseAgent
from utils.logger import logger
from utils.json_handler import JSONHandler
from pathlib import Path

class PathogenesisAgent(BaseAgent):
    """病機推理Agent - 分析病因病機"""

    def __init__(self):
        super().__init__('pathogenesis_agent')
        self.tcm_knowledge = self._load_tcm_knowledge()

    def _load_tcm_knowledge(self) -> Dict[str, Any]:
        """載入中醫知識庫"""
        knowledge_path = Path(__file__).parent.parent / 'config' / 'tcm_knowledge.json'
        try:
            return JSONHandler.load_json(str(knowledge_path))
        except Exception as e:
            logger.error(f"載入中醫知識庫失敗: {e}")
            return {}

    def process(self, structured_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """分析病因病機"""
        logger.info("開始病機推理...")

        symptoms = structured_data.get('symptoms', [])
        tongue = structured_data.get('tongue', {})
        pulse = structured_data.get('pulse', '')

        # 分析病位
        affected_organs = self._analyze_affected_organs(symptoms, tongue, pulse)

        # 分析病性
        pathological_nature = self._analyze_pathological_nature(symptoms, tongue, pulse)

        # 推斷病因
        etiology = self._infer_etiology(symptoms, pathological_nature)

        # 生成病機假說
        pathogenesis_hypotheses = self._generate_hypotheses(
            affected_organs, pathological_nature, etiology
        )

        result = {
            "status": "success",
            "agent": self.agent_name,
            "data": {
                "affected_organs": affected_organs,
                "pathological_nature": pathological_nature,
                "etiology": etiology,
                "pathogenesis_hypotheses": pathogenesis_hypotheses
            }
        }

        logger.info(f"病機推理完成,生成 {len(pathogenesis_hypotheses)} 個假說")
        return result

    def _analyze_affected_organs(self, symptoms: List[str], tongue: Dict[str, str], pulse: str) -> List[str]:
        """分析受累臟腑"""
        affected = []
        symptom_text = ''.join(symptoms)

        if any(s in symptom_text for s in ['心悸', '失眠', '健忘']):
            affected.append('心')
        if any(s in symptom_text for s in ['脅痛', '目眩', '抑鬱']) or '弦' in pulse:
            affected.append('肝')
        if any(s in symptom_text for s in ['乏力', '納差', '腹脹']):
            affected.append('脾')
        if any(s in symptom_text for s in ['咳嗽', '氣短', '喘促']):
            affected.append('肺')
        if any(s in symptom_text for s in ['腰痛', '耳鳴', '尿頻']):
            affected.append('腎')

        return affected if affected else ['未明確']

    def _analyze_pathological_nature(self, symptoms: List[str], tongue: Dict[str, str], pulse: str) -> Dict[str, str]:
        """分析病性"""
        return {
            "寒熱": self._determine_cold_heat(symptoms, tongue, pulse),
            "虛實": self._determine_deficiency_excess(symptoms, pulse)
        }

    def _determine_cold_heat(self, symptoms: List[str], tongue: Dict[str, str], pulse: str) -> str:
        """判斷寒熱"""
        heat_score = sum(1 for s in symptoms if any(x in s for x in ['發熱', '口渴', '煩躁']))
        cold_score = sum(1 for s in symptoms if any(x in s for x in ['畏寒', '肢冷', '喜溫']))

        if tongue.get('color') in ['紅', '絳']: heat_score += 2
        if tongue.get('color') == '淡': cold_score += 2
        if '數' in pulse: heat_score += 1
        if '遲' in pulse: cold_score += 1

        return '熱證' if heat_score > cold_score + 2 else '寒證' if cold_score > heat_score + 2 else '寒熱錯雜'

    def _determine_deficiency_excess(self, symptoms: List[str], pulse: str) -> str:
        """判斷虛實"""
        def_count = sum(1 for s in symptoms if any(x in s for x in ['乏力', '氣短', '自汗']))
        exc_count = sum(1 for s in symptoms if any(x in s for x in ['脹滿', '疼痛', '煩躁']))

        if any(x in pulse for x in ['虛', '弱', '細']): def_count += 2
        if any(x in pulse for x in ['實', '洪']): exc_count += 2

        return '虛證' if def_count > exc_count + 1 else '實證' if exc_count > def_count + 1 else '虛實夾雜'

    def _infer_etiology(self, symptoms: List[str], nature: Dict[str, str]) -> List[str]:
        """推斷病因"""
        etiologies = []
        symptom_text = ''.join(symptoms)

        if any(x in symptom_text for x in ['惡寒', '發熱', '頭痛']):
            etiologies.append('風寒外感' if nature['寒熱'] == '寒證' else '風熱外感')
        if any(x in symptom_text for x in ['抑鬱', '易怒', '脅痛']):
            etiologies.append('情志不遂')
        if any(x in symptom_text for x in ['脘腹脹', '噯氣', '納差']):
            etiologies.append('飲食不節')

        return etiologies if etiologies else ['待查']

    def _generate_hypotheses(self, organs: List[str], nature: Dict[str, str], etiology: List[str]) -> List[Dict[str, Any]]:
        """生成病機假說"""
        hypotheses = []
        syndromes = self.tcm_knowledge.get('syndromes', {})

        for syndrome_name, syndrome_info in list(syndromes.items())[:3]:
            hypotheses.append({
                "syndrome": syndrome_name,
                "mechanism": f"病位在{'、'.join(organs)},{nature.get('虛實','')},{nature.get('寒熱','')}",
                "treatment_principle": syndrome_info.get('treatment_principle', ''),
                "confidence": round(1.0 - len(hypotheses) * 0.15, 2)
            })

        return hypotheses
