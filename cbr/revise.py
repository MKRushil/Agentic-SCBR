"""CBR修正階段"""
from typing import Dict, Any, List, Optional
from utils.logger import logger

class CaseReviser:
    """案例修正器"""

    @staticmethod
    def revise(
        reused_solution: Dict[str, Any],
        current_case: Dict[str, Any],
        conflicts: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        修正重用的診療方案

        Args:
            reused_solution: 重用的方案
            current_case: 當前患者信息
            conflicts: 檢測到的衝突列表

        Returns:
            修正後的診療方案
        """
        logger.info("開始修正診療方案...")

        revised_solution = reused_solution.copy()
        revision_notes = []

        # 檢查是否有衝突需要處理
        if conflicts:
            for conflict in conflicts:
                conflict_type = conflict.get('type')

                if conflict_type == 'symptom_conflict':
                    # 症狀衝突:調整證型判斷
                    revision_notes.append(f"發現症狀衝突: {conflict.get('description')}")
                    revised_solution['needs_expert_review'] = True

                elif conflict_type == 'syndrome_mismatch':
                    # 證型不匹配:降低信心度
                    revised_solution['confidence'] *= 0.8
                    revision_notes.append("證型匹配度較低,已降低信心度")

                elif conflict_type == 'contraindication':
                    # 禁忌症:標記警告
                    revised_solution['warnings'] = revised_solution.get('warnings', [])
                    revised_solution['warnings'].append(conflict.get('description'))
                    revision_notes.append(f"發現用藥禁忌: {conflict.get('description')}")

        # 根據當前患者特徵調整
        adjustments = CaseReviser._adjust_for_patient_specifics(
            revised_solution,
            current_case
        )

        revision_notes.extend(adjustments)

        revised_solution['revision_notes'] = revision_notes
        revised_solution['revised'] = True

        logger.info(f"修正完成,共 {len(revision_notes)} 處調整")

        return revised_solution

    @staticmethod
    def _adjust_for_patient_specifics(
        solution: Dict[str, Any],
        current_case: Dict[str, Any]
    ) -> List[str]:
        """根據患者特異性調整方案"""
        adjustments = []

        # 檢查年齡因素
        age = current_case.get('patient_info', {}).get('age', 0)
        if age > 65:
            adjustments.append("患者年齡較大,建議減輕藥量")
        elif age < 18:
            adjustments.append("患者為兒童/青少年,需調整用藥劑量")

        # 檢查性別因素
        gender = current_case.get('patient_info', {}).get('gender', '')
        if gender == '女':
            # 檢查是否有月經相關症狀
            symptoms = current_case.get('symptoms', [])
            menstrual_symptoms = [s for s in symptoms if '月經' in s or '經期' in s]
            if menstrual_symptoms:
                adjustments.append("存在月經相關症狀,考慮調經用藥")

        return adjustments
