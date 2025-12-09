"""CBR保留階段"""
from typing import Dict, Any, Optional
from knowledge.case_database import CaseDatabase
from utils.logger import logger
from config.settings import settings
import datetime

class CaseRetainer:
    """案例保留器"""

    def __init__(self):
        self.case_db = CaseDatabase()

    def retain(
        self,
        current_case: Dict[str, Any],
        diagnosis_result: Dict[str, Any],
        treatment_outcome: Optional[Dict[str, Any]] = None,
        expert_reviewed: bool = False
    ) -> bool:
        """
        保留新案例到案例庫

        Args:
            current_case: 當前患者信息
            diagnosis_result: 診斷結果
            treatment_outcome: 治療結果(可選)
            expert_reviewed: 是否經過專家審核

        Returns:
            是否成功保留
        """
        logger.info("開始保留新案例...")

        # 檢查是否需要專家審核
        if settings.REQUIRE_EXPERT_REVIEW and not expert_reviewed:
            logger.warning("需要專家審核,案例暫不保留")
            return False

        # 構建新案例
        new_case = {
            "case_id": f"CASE{len(self.case_db.get_all_cases()) + 1:03d}",
            "patient_info": current_case.get('patient_info', {}),
            "chief_complaint": current_case.get('chief_complaint', ''),
            "symptoms": current_case.get('symptoms', []),
            "tongue": current_case.get('tongue', {}),
            "pulse": current_case.get('pulse', ''),
            "syndrome": diagnosis_result.get('syndrome', ''),
            "treatment_principle": diagnosis_result.get('treatment_principle', ''),
            "formula": diagnosis_result.get('formula', ''),
            "herbs": diagnosis_result.get('herbs', []),
            "created_date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "expert_reviewed": expert_reviewed
        }

        # 添加治療結果(如果有)
        if treatment_outcome:
            new_case['outcome'] = treatment_outcome.get('description', '')
            new_case['efficacy_score'] = treatment_outcome.get('efficacy_score', 0)
        else:
            new_case['outcome'] = '待隨訪'
            new_case['efficacy_score'] = 0

        # 保存到案例庫
        success = self.case_db.add_case(new_case)

        if success:
            logger.info(f"新案例已保留: {new_case['case_id']}")
        else:
            logger.error("保留案例失敗")

        return success

    def update_treatment_outcome(
        self,
        case_id: str,
        outcome: str,
        efficacy_score: float
    ) -> bool:
        """更新案例的治療結果"""
        updates = {
            'outcome': outcome,
            'efficacy_score': efficacy_score,
            'updated_date': datetime.datetime.now().strftime("%Y-%m-%d")
        }

        success = self.case_db.update_case(case_id, updates)

        if success:
            logger.info(f"案例 {case_id} 的治療結果已更新")

        return success
