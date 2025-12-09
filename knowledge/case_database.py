"""案例庫管理"""
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from utils.json_handler import JSONHandler
from utils.logger import logger
from config.settings import settings

class CaseDatabase:
    """案例庫管理器"""

    def __init__(self, case_library_path: Optional[str] = None):
        self.case_library_path = case_library_path or settings.CASE_LIBRARY_PATH
        self.cases = self._load_cases()
        logger.info(f"案例庫已載入,共 {len(self.cases)} 個案例")

    def _load_cases(self) -> List[Dict[str, Any]]:
        try:
            data = JSONHandler.load_json(self.case_library_path)
            return data.get('cases', [])
        except FileNotFoundError:
            logger.warning(f"案例庫文件不存在: {self.case_library_path}")
            return []
        except Exception as e:
            logger.error(f"載入案例庫失敗: {e}")
            return []

    def get_all_cases(self) -> List[Dict[str, Any]]:
        return self.cases

    def get_case_by_id(self, case_id: str) -> Optional[Dict[str, Any]]:
        for case in self.cases:
            if case.get('case_id') == case_id:
                return case
        return None

    def add_case(self, case: Dict[str, Any]) -> bool:
        try:
            if 'case_id' not in case:
                case['case_id'] = f"CASE{len(self.cases) + 1:03d}"
            self.cases.append(case)
            self._save_cases()
            logger.info(f"新增案例: {case['case_id']}")
            return True
        except Exception as e:
            logger.error(f"添加案例失敗: {e}")
            return False

    def update_case(self, case_id: str, updates: Dict[str, Any]) -> bool:
        for i, case in enumerate(self.cases):
            if case.get('case_id') == case_id:
                self.cases[i].update(updates)
                self._save_cases()
                logger.info(f"更新案例: {case_id}")
                return True
        return False

    def search_by_syndrome(self, syndrome: str) -> List[Dict[str, Any]]:
        results = []
        for case in self.cases:
            if case.get('syndrome') == syndrome:
                results.append(case)
        return results

    def search_by_symptoms(self, symptoms: List[str]) -> List[Dict[str, Any]]:
        results = []
        for case in self.cases:
            case_symptoms = set(case.get('symptoms', []))
            query_symptoms = set(symptoms)
            common_symptoms = case_symptoms & query_symptoms
            if len(common_symptoms) > 0:
                case_copy = case.copy()
                case_copy['matched_symptoms'] = list(common_symptoms)
                case_copy['match_ratio'] = len(common_symptoms) / len(query_symptoms) if query_symptoms else 0
                results.append(case_copy)
        results.sort(key=lambda x: x['match_ratio'], reverse=True)
        return results

    def _save_cases(self) -> None:
        data = {'cases': self.cases}
        JSONHandler.save_json(data, self.case_library_path)

    def get_statistics(self) -> Dict[str, Any]:
        syndromes = {}
        for case in self.cases:
            syndrome = case.get('syndrome', 'Unknown')
            syndromes[syndrome] = syndromes.get(syndrome, 0) + 1
        return {
            'total_cases': len(self.cases),
            'syndromes_distribution': syndromes,
            'average_efficacy': sum(c.get('efficacy_score', 0) for c in self.cases) / len(self.cases) if self.cases else 0
        }