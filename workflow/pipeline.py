"""核心診斷流程管線"""
from typing import Dict, Any
from agents.intake_agent import IntakeAgent
from agents.pathogenesis_agent import PathogenesisAgent
from agents.retrieval_agent import RetrievalAgent
from agents.diagnosis_agent import DiagnosisAgent
from agents.explanation_agent import ExplanationAgent
from cbr.retrieve import CaseRetriever
from cbr.reuse import CaseReuser
from cbr.revise import CaseReviser
from cbr.retain import CaseRetainer
from workflow.state_manager import StateManager
from utils.logger import logger

class TCMDiagnosisPipeline:
    """中醫診斷流程管線 - 模擬中醫思維"""

    def __init__(self):
        # 初始化所有Agent
        self.intake_agent = IntakeAgent()
        self.pathogenesis_agent = PathogenesisAgent()
        self.retrieval_agent = RetrievalAgent()
        self.diagnosis_agent = DiagnosisAgent()
        self.explanation_agent = ExplanationAgent()

        # 初始化CBR模組
        self.retriever = CaseRetriever()
        self.reuser = CaseReuser()
        self.reviser = CaseReviser()
        self.retainer = CaseRetainer()

        # 狀態管理
        self.state = StateManager()

        logger.info("診斷流程管線初始化完成")

    def diagnose(self, patient_input: str, patient_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        執行完整診斷流程

        中醫思維流程:
        1. 觀測 - 採集四診信息
        2. 聯想案例 - 檢索相似病例
        3. 發現衝突 - 比對差異
        4. 修正判斷 - 調整方案
        5. 診察決策 - 辨證論治
        """
        logger.info("="*50)
        logger.info("開始中醫診斷流程")
        logger.info("="*50)

        try:
            # 階段1: 觀測 - 信息採集
            self.state.set_stage("觀測階段")
            intake_result = self._stage_intake(patient_input)
            structured_data = intake_result['data']

            # 添加患者基本信息
            if patient_info:
                structured_data['patient_info'] = patient_info

            # 階段2: 病機推理
            self.state.set_stage("病機分析階段")
            pathogenesis_result = self._stage_pathogenesis(structured_data)

            # 階段3: 聯想案例 - CBR檢索
            self.state.set_stage("聯想案例階段")
            similar_cases = self._stage_retrieve(structured_data)

            # 階段4: 重用案例
            self.state.set_stage("案例重用階段")
            reused_solution = self._stage_reuse(similar_cases, structured_data)

            # 階段5: 檢測衝突
            self.state.set_stage("衝突檢測階段")
            conflicts = self._stage_conflict_detection(
                structured_data, similar_cases, reused_solution
            )

            # 階段6: 修正判斷
            if conflicts:
                self.state.set_stage("修正判斷階段")
                revised_solution = self._stage_revise(
                    reused_solution, structured_data, conflicts
                )
            else:
                revised_solution = reused_solution

            # 階段7: 診察決策 - 辨證論治
            self.state.set_stage("辨證論治階段")
            diagnosis_result = self._stage_diagnosis(
                intake_result,
                pathogenesis_result,
                similar_cases
            )

            # 階段8: 生成解釋
            self.state.set_stage("生成解釋階段")
            explanation_result = self._stage_explanation(
                diagnosis_result,
                intake_result,
                pathogenesis_result,
                similar_cases
            )

            # 組裝最終結果
            final_result = self._assemble_result(
                intake_result,
                pathogenesis_result,
                similar_cases,
                diagnosis_result,
                explanation_result,
                conflicts
            )

            logger.info("="*50)
            logger.info("診斷流程完成")
            logger.info("="*50)

            return final_result

        except Exception as e:
            logger.error(f"診斷流程出錯: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e)
            }

    def _stage_intake(self, patient_input: str) -> Dict[str, Any]:
        """階段1: 觀測 - 信息採集"""
        logger.info("[觀測] 開始採集四診信息...")
        result = self.intake_agent.process(patient_input)
        self.state.update("intake_result", result)
        logger.info(f"[觀測] 完成,提取到 {len(result['data']['symptoms'])} 個症狀")
        return result

    def _stage_pathogenesis(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """階段2: 病機推理"""
        logger.info("[病機分析] 開始分析病因病機...")
        result = self.pathogenesis_agent.process(structured_data)
        self.state.update("pathogenesis_result", result)

        hypotheses = result['data']['pathogenesis_hypotheses']
        logger.info(f"[病機分析] 完成,生成 {len(hypotheses)} 個病機假說")
        return result

    def _stage_retrieve(self, structured_data: Dict[str, Any]) -> list:
        """階段3: 聯想案例 - 檢索相似病例"""
        logger.info("[聯想案例] 開始檢索相似病例...")
        similar_cases = self.retriever.retrieve(structured_data)
        self.state.update("retrieval_result", similar_cases)
        logger.info(f"[聯想案例] 找到 {len(similar_cases)} 個相似案例")

        if similar_cases:
            top_case = similar_cases[0]
            logger.info(
                f"  最相似: {top_case.get('case_id')} "
                f"(相似度: {top_case.get('similarity_score', 0):.2f})"
            )

        return similar_cases

    def _stage_reuse(self, similar_cases: list, current_case: Dict[str, Any]) -> Dict[str, Any]:
        """階段4: 重用案例"""
        logger.info("[案例重用] 開始重用歷史案例...")
        reused_solution = self.reuser.reuse(similar_cases, current_case)

        if reused_solution.get('syndrome_suggestions'):
            top_syndrome = reused_solution['syndrome_suggestions'][0]
            logger.info(f"[案例重用] 推薦證型: {top_syndrome['syndrome']}")

        return reused_solution

    def _stage_conflict_detection(
        self,
        current_case: Dict[str, Any],
        similar_cases: list,
        reused_solution: Dict[str, Any]
    ) -> list:
        """階段5: 檢測衝突"""
        logger.info("[衝突檢測] 檢查診斷與案例的衝突...")
        conflicts = []

        # 檢查證型一致性
        if similar_cases and reused_solution.get('syndrome_suggestions'):
            suggested_syndrome = reused_solution['syndrome_suggestions'][0]['syndrome']
            case_syndromes = [c.get('syndrome') for c in similar_cases[:2]]

            if suggested_syndrome not in case_syndromes:
                conflicts.append({
                    "type": "syndrome_mismatch",
                    "description": f"推薦證型{suggested_syndrome}與相似案例不完全一致",
                    "severity": "low"
                })

        # 檢查症狀衝突
        current_symptoms = set(current_case.get('symptoms', []))
        if similar_cases:
            case_symptoms = set(similar_cases[0].get('symptoms', []))
            unique_symptoms = current_symptoms - case_symptoms

            if len(unique_symptoms) > 3:
                conflicts.append({
                    "type": "symptom_conflict",
                    "description": f"當前患者有{len(unique_symptoms)}個獨特症狀",
                    "severity": "medium",
                    "details": list(unique_symptoms)[:3]
                })

        if conflicts:
            for conflict in conflicts:
                self.state.add_conflict(conflict)
            logger.warning(f"[衝突檢測] 發現 {len(conflicts)} 個潛在衝突")
        else:
            logger.info("[衝突檢測] 未發現明顯衝突")

        return conflicts

    def _stage_revise(
        self,
        reused_solution: Dict[str, Any],
        current_case: Dict[str, Any],
        conflicts: list
    ) -> Dict[str, Any]:
        """階段6: 修正判斷"""
        logger.info("[修正判斷] 開始根據衝突修正方案...")
        revised_solution = self.reviser.revise(reused_solution, current_case, conflicts)
        logger.info(f"[修正判斷] 完成,修正 {len(conflicts)} 處")
        return revised_solution

    def _stage_diagnosis(
        self,
        intake_result: Dict[str, Any],
        pathogenesis_result: Dict[str, Any],
        similar_cases: list
    ) -> Dict[str, Any]:
        """階段7: 辨證論治"""
        logger.info("[辨證論治] 開始綜合辨證...")
        diagnosis_result = self.diagnosis_agent.process(
            intake_result,
            pathogenesis_result,
            similar_cases
        )
        self.state.update("diagnosis_result", diagnosis_result)

        syndrome = diagnosis_result['data']['main_syndrome']['syndrome']
        logger.info(f"[辨證論治] 主證: {syndrome}")
        return diagnosis_result

    def _stage_explanation(
        self,
        diagnosis_result: Dict[str, Any],
        intake_result: Dict[str, Any],
        pathogenesis_result: Dict[str, Any],
        similar_cases: list
    ) -> Dict[str, Any]:
        """階段8: 生成解釋"""
        logger.info("[生成解釋] 開始生成診斷解釋...")
        explanation_result = self.explanation_agent.process(
            diagnosis_result,
            intake_result,
            pathogenesis_result,
            similar_cases
        )
        self.state.update("explanation_result", explanation_result)
        logger.info("[生成解釋] 完成")
        return explanation_result

    def _assemble_result(
        self,
        intake_result: Dict[str, Any],
        pathogenesis_result: Dict[str, Any],
        similar_cases: list,
        diagnosis_result: Dict[str, Any],
        explanation_result: Dict[str, Any],
        conflicts: list
    ) -> Dict[str, Any]:
        """組裝最終結果"""
        diagnosis_data = diagnosis_result['data']
        explanation_data = explanation_result['data']

        return {
            "status": "success",
            "patient_data": intake_result['data'],
            "pathogenesis_analysis": pathogenesis_result['data'],
            "similar_cases_count": len(similar_cases),
            "top_similar_cases": [
                {
                    "case_id": c.get('case_id'),
                    "syndrome": c.get('syndrome'),
                    "similarity": c.get('similarity_score')
                }
                for c in similar_cases[:3]
            ],
            "diagnosis": {
                "main_syndrome": diagnosis_data['main_syndrome']['syndrome'],
                "confidence": diagnosis_data['confidence'],
                "treatment_principle": diagnosis_data['treatment_principle'],
                "formula": diagnosis_data['formula']['name'],
                "herbs": diagnosis_data['herbs']
            },
            "explanation": explanation_data['summary'],
            "reasoning": diagnosis_data['reasoning'],
            "conflicts_detected": len(conflicts),
            "conflicts": conflicts,
            "metadata": {
                "has_conflicts": len(conflicts) > 0,
                "similar_cases_used": len(similar_cases)
            }
        }

    def save_case(
        self,
        diagnosis_result: Dict[str, Any],
        treatment_outcome: Dict[str, Any] = None,
        expert_reviewed: bool = False
    ) -> bool:
        """保存案例到案例庫 (CBR Retain階段)"""
        logger.info("[保留案例] 開始保存新案例...")

        current_case = self.state.get("intake_result", {}).get('data', {})
        diagnosis_data = diagnosis_result.get('data', {})

        success = self.retainer.retain(
            current_case,
            diagnosis_data,
            treatment_outcome,
            expert_reviewed
        )

        if success:
            logger.info("[保留案例] 案例已成功保存")

        return success
