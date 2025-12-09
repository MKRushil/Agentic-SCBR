"""診斷Agent - 辨證論治"""
from typing import Dict, Any, List
from .base_agent import BaseAgent
from utils.logger import logger
from utils.json_handler import JSONHandler
from pathlib import Path

class DiagnosisAgent(BaseAgent):
    """辨證論治Agent"""

    def __init__(self):
        super().__init__('diagnosis_agent')
        self.tcm_knowledge = self._load_tcm_knowledge()

    def _load_tcm_knowledge(self) -> Dict[str, Any]:
        """載入中醫知識庫"""
        knowledge_path = Path(__file__).parent.parent / 'config' / 'tcm_knowledge.json'
        try:
            return JSONHandler.load_json(str(knowledge_path))
        except Exception as e:
            logger.error(f"載入中醫知識庫失敗: {e}")
            return {}

    def process(
        self,
        intake_result: Dict[str, Any],
        pathogenesis_result: Dict[str, Any],
        similar_cases: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """綜合辨證論治"""
        logger.info("開始辨證論治...")

        # 從病機推理獲取假說
        hypotheses = pathogenesis_result.get('data', {}).get('pathogenesis_hypotheses', [])

        # 從相似案例獲取證型建議
        case_syndromes = self._extract_syndromes_from_cases(similar_cases)

        # 綜合判斷主證
        main_syndrome = self._determine_main_syndrome(hypotheses, case_syndromes)

        # 判斷兼證
        secondary_syndromes = self._determine_secondary_syndromes(
            intake_result, hypotheses
        )

        # 確定治法
        treatment_principle = self._determine_treatment_principle(main_syndrome)

        # 選擇方劑
        formula_recommendation = self._select_formula(
            main_syndrome, similar_cases
        )

        # 生成用藥建議
        herb_recommendations = self._generate_herb_recommendations(
            formula_recommendation, intake_result
        )

        result = {
            "status": "success",
            "agent": self.agent_name,
            "data": {
                "main_syndrome": main_syndrome,
                "secondary_syndromes": secondary_syndromes,
                "treatment_principle": treatment_principle,
                "formula": formula_recommendation,
                "herbs": herb_recommendations,
                "confidence": self._calculate_overall_confidence(similar_cases),
                "reasoning": self._construct_reasoning_chain(
                    main_syndrome, hypotheses, similar_cases
                )
            }
        }

        logger.info(f"辨證論治完成,主證: {main_syndrome['syndrome']}")
        return result

    def _extract_syndromes_from_cases(self, cases: List[Dict[str, Any]]) -> Dict[str, float]:
        """從相似案例提取證型及其權重"""
        syndrome_scores = {}
        total_weight = 0

        for case in cases:
            syndrome = case.get('syndrome', '')
            similarity = case.get('similarity_score', 0)
            efficacy = case.get('efficacy_score', 0)

            # 綜合權重: 相似度60% + 療效40%
            weight = similarity * 0.6 + efficacy * 0.4

            if syndrome:
                syndrome_scores[syndrome] = syndrome_scores.get(syndrome, 0) + weight
                total_weight += weight

        # 歸一化
        if total_weight > 0:
            syndrome_scores = {k: v/total_weight for k, v in syndrome_scores.items()}

        return syndrome_scores

    def _determine_main_syndrome(
        self,
        hypotheses: List[Dict[str, Any]],
        case_syndromes: Dict[str, float]
    ) -> Dict[str, Any]:
        """確定主證"""
        # 綜合病機假說和案例證型
        syndrome_scores = {}

        # 病機假說貢獻40%
        for i, hyp in enumerate(hypotheses):
            syndrome = hyp.get('syndrome', '')
            confidence = hyp.get('confidence', 1.0 - i * 0.15)
            syndrome_scores[syndrome] = syndrome_scores.get(syndrome, 0) + confidence * 0.4

        # 案例證型貢獻60%
        for syndrome, score in case_syndromes.items():
            syndrome_scores[syndrome] = syndrome_scores.get(syndrome, 0) + score * 0.6

        # 選擇得分最高的證型
        if syndrome_scores:
            main_syndrome_name = max(syndrome_scores, key=syndrome_scores.get)
            confidence = syndrome_scores[main_syndrome_name]
        else:
            main_syndrome_name = hypotheses[0].get('syndrome', '氣虛證') if hypotheses else '氣虛證'
            confidence = 0.5

        # 獲取證型詳細信息
        syndrome_info = self.tcm_knowledge.get('syndromes', {}).get(main_syndrome_name, {})

        return {
            "syndrome": main_syndrome_name,
            "confidence": round(confidence, 3),
            "key_symptoms": syndrome_info.get('key_symptoms', []),
            "treatment_principle": syndrome_info.get('treatment_principle', '')
        }

    def _determine_secondary_syndromes(
        self,
        intake_result: Dict[str, Any],
        hypotheses: List[Dict[str, Any]]
    ) -> List[str]:
        """判斷兼證"""
        # 簡化版:從病機假說中選擇次要證型
        secondary = []
        for hyp in hypotheses[1:3]:  # 取第2-3個假說作為可能的兼證
            syndrome = hyp.get('syndrome', '')
            if syndrome:
                secondary.append(syndrome)
        return secondary

    def _determine_treatment_principle(self, main_syndrome: Dict[str, Any]) -> str:
        """確定治法"""
        return main_syndrome.get('treatment_principle', '扶正祛邪')

    def _select_formula(
        self,
        main_syndrome: Dict[str, Any],
        similar_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """選擇方劑"""
        syndrome_name = main_syndrome['syndrome']

        # 優先從相似案例中選擇
        for case in similar_cases:
            if case.get('syndrome') == syndrome_name:
                return {
                    "name": case.get('formula', ''),
                    "source": f"參考案例 {case.get('case_id', '')}",
                    "efficacy": case.get('efficacy_score', 0),
                    "herbs": case.get('herbs', [])
                }

        # 從知識庫獲取經典方劑
        syndrome_info = self.tcm_knowledge.get('syndromes', {}).get(syndrome_name, {})
        common_formulas = syndrome_info.get('common_formulas', [])

        if common_formulas:
            return {
                "name": common_formulas[0],
                "source": "中醫知識庫",
                "efficacy": 0,
                "herbs": []
            }

        return {
            "name": "待定",
            "source": "需進一步辨證",
            "efficacy": 0,
            "herbs": []
        }

    def _generate_herb_recommendations(
        self,
        formula: Dict[str, Any],
        intake_result: Dict[str, Any]
    ) -> List[str]:
        """生成用藥建議"""
        herbs = formula.get('herbs', [])

        if not herbs:
            # 如果沒有具體藥物,返回說明
            return ["請根據證型選擇具體方劑"]

        # 可以根據患者特點進行加減
        recommendations = herbs.copy()

        # 示例:根據症狀調整(簡化版)
        symptoms = intake_result.get('data', {}).get('symptoms', [])
        symptom_text = ''.join(symptoms)

        if '失眠' in symptom_text and '酸棗仁' not in ''.join(recommendations):
            recommendations.append("加 酸棗仁15g (安神)")

        return recommendations

    def _calculate_overall_confidence(self, similar_cases: List[Dict[str, Any]]) -> float:
        """計算整體診斷信心度"""
        if not similar_cases:
            return 0.5

        # 基於最相似案例的相似度和療效
        top_case = similar_cases[0]
        similarity = top_case.get('similarity_score', 0)
        efficacy = top_case.get('efficacy_score', 0)

        confidence = similarity * 0.7 + efficacy * 0.3
        return round(confidence, 3)

    def _construct_reasoning_chain(
        self,
        main_syndrome: Dict[str, Any],
        hypotheses: List[Dict[str, Any]],
        similar_cases: List[Dict[str, Any]]
    ) -> str:
        """構建推理鏈"""
        reasoning = []

        reasoning.append(f"根據四診合參,辨證為{main_syndrome['syndrome']}")

        if hypotheses:
            reasoning.append(f"病機分析: {hypotheses[0].get('mechanism', '')}")

        if similar_cases:
            top_case = similar_cases[0]
            reasoning.append(
                f"參考相似案例{top_case.get('case_id', '')},"
                f"相似度{top_case.get('similarity_score', 0):.2f}"
            )

        reasoning.append(f"治法: {main_syndrome.get('treatment_principle', '')}")

        return "; ".join(reasoning)
