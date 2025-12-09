"""解釋Agent - 生成診斷解釋"""
from typing import Dict, Any
from .base_agent import BaseAgent
from utils.logger import logger

class ExplanationAgent(BaseAgent):
    """推理解釋Agent"""

    def __init__(self):
        super().__init__('explanation_agent')

    def process(
        self,
        diagnosis_result: Dict[str, Any],
        intake_result: Dict[str, Any],
        pathogenesis_result: Dict[str, Any],
        similar_cases: list,
        **kwargs
    ) -> Dict[str, Any]:
        """生成診斷解釋"""
        logger.info("開始生成診斷解釋...")

        diagnosis_data = diagnosis_result.get('data', {})

        # 構建解釋文本
        explanation_text = self._construct_explanation(
            diagnosis_data,
            intake_result,
            pathogenesis_result,
            similar_cases
        )

        # 構建理法方藥解釋
        principle_explanation = self._explain_treatment_principle(diagnosis_data)

        # 構建方藥解釋
        formula_explanation = self._explain_formula(diagnosis_data)

        result = {
            "status": "success",
            "agent": self.agent_name,
            "data": {
                "summary": explanation_text,
                "principle_explanation": principle_explanation,
                "formula_explanation": formula_explanation,
                "differential_diagnosis": self._explain_differential(diagnosis_data)
            }
        }

        logger.info("診斷解釋生成完成")
        return result

    def _construct_explanation(
        self,
        diagnosis: Dict[str, Any],
        intake: Dict[str, Any],
        pathogenesis: Dict[str, Any],
        cases: list
    ) -> str:
        """構建完整解釋"""
        parts = []

        # 症狀總結
        intake_data = intake.get('data', {})
        chief_complaint = intake_data.get('chief_complaint', '')
        parts.append(f"患者{chief_complaint}")

        # 四診要點
        tongue = intake_data.get('tongue', {})
        pulse = intake_data.get('pulse', '')
        tongue_desc = f"{tongue.get('color', '')}{tongue.get('coating', '')}"
        parts.append(f"舌{tongue_desc},脈{pulse}")

        # 病機分析
        path_data = pathogenesis.get('data', {})
        organs = path_data.get('affected_organs', [])
        nature = path_data.get('pathological_nature', {})

        if organs:
            parts.append(f"病位在{'、'.join(organs)}")

        if nature:
            parts.append(f"病性為{nature.get('虛實', '')}{nature.get('寒熱', '')}")

        # 辨證結論
        main_syndrome = diagnosis.get('main_syndrome', {})
        parts.append(f"辨證為{main_syndrome.get('syndrome', '')}")

        # 治法
        treatment = diagnosis.get('treatment_principle', '')
        parts.append(f"治以{treatment}")

        # 方藥
        formula = diagnosis.get('formula', {})
        formula_name = formula.get('name', '')
        if formula_name and formula_name != '待定':
            parts.append(f"方選{formula_name}")

        return ",".join(parts) + "。"

    def _explain_treatment_principle(self, diagnosis: Dict[str, Any]) -> str:
        """解釋治則治法"""
        principle = diagnosis.get('treatment_principle', '')
        main_syndrome = diagnosis.get('main_syndrome', {}).get('syndrome', '')

        explanations = {
            "補氣": "患者正氣虧虛,故以補氣為主,使正氣漸復",
            "補血養血": "血虛不能上榮,當補血以養心神",
            "溫陽散寒": "陽虛寒盛,當溫陽以散寒邪",
            "滋陰降火": "陰虛火旺,當滋陰以降虛火",
            "理氣解鬱": "氣機鬱滯,當理氣以解鬱結",
            "活血化瘀": "瘀血阻滯,當活血以化瘀滯",
            "化痰祛濕": "痰濕內蘊,當化痰以祛濕邪",
            "清熱利濕": "濕熱蘊結,當清熱以利濕濁"
        }

        return explanations.get(principle, f"{main_syndrome}當{principle}")

    def _explain_formula(self, diagnosis: Dict[str, Any]) -> str:
        """解釋方藥選擇"""
        formula = diagnosis.get('formula', {})
        formula_name = formula.get('name', '')
        source = formula.get('source', '')

        if not formula_name or formula_name == '待定':
            return "建議根據患者具體情況選擇合適方劑"

        explanation = f"選用{formula_name}"

        if "案例" in source:
            explanation += f",{source},療效確切"
        else:
            explanation += ",為治療本證之經典方劑"

        # 如果有具體藥物,可以進一步解釋
        herbs = diagnosis.get('herbs', [])
        if herbs and len(herbs) > 0:
            explanation += f",共{len(herbs)}味藥"

        return explanation

    def _explain_differential(self, diagnosis: Dict[str, Any]) -> str:
        """解釋鑑別診斷"""
        main_syndrome = diagnosis.get('main_syndrome', {}).get('syndrome', '')
        secondary = diagnosis.get('secondary_syndromes', [])

        if not secondary:
            return f"本證以{main_syndrome}為主,證候明確"

        diff = f"本證主要為{main_syndrome}"

        if secondary:
            diff += f",需與{secondary[0]}等證鑑別"
            diff += ",但從症狀、舌脈綜合判斷,仍以前者為主"

        return diff
