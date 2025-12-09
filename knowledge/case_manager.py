"""
Case Manager - 案例庫管理器
"""

import json
import os
from typing import Dict, Any, List
from pathlib import Path
from utils.logger import logger
from config.settings import settings

class CaseManager:
    """案例庫管理器"""

    def __init__(self):
        self.case_library_path = settings.system.case_library_path
        self.cases = []
        self._load_cases()

    def _load_cases(self):
        """加載案例庫"""
        try:
            # 確保目錄存在
            os.makedirs(os.path.dirname(self.case_library_path), exist_ok=True)

            if os.path.exists(self.case_library_path):
                with open(self.case_library_path, 'r', encoding='utf-8') as f:
                    self.cases = json.load(f)
                logger.info(f"載入 {len(self.cases)} 個案例")
            else:
                # 創建空案例庫
                self.cases = []
                self._save_cases()
                logger.info("創建新的案例庫")

        except Exception as e:
            logger.error(f"載入案例庫失敗: {e}")
            self.cases = []

    def _save_cases(self):
        """保存案例庫"""
        try:
            with open(self.case_library_path, 'w', encoding='utf-8') as f:
                json.dump(self.cases, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存案例庫失敗: {e}")

    def get_case_count(self) -> int:
        """獲取案例數量"""
        return len(self.cases)

    def add_case(self, case: Dict[str, Any]) -> bool:
        """添加案例"""
        try:
            self.cases.append(case)
            self._save_cases()
            logger.info(f"添加案例: {case.get('case_id', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"添加案例失敗: {e}")
            return False

    def get_case(self, case_id: str) -> Dict[str, Any]:
        """獲取指定案例"""
        for case in self.cases:
            if case.get('case_id') == case_id:
                return case
        return None

    def search_cases(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """搜索案例"""
        results = []
        top_k = criteria.get('top_k', 5)
        symptoms = criteria.get('symptoms', [])
        
        # ✅ 添加：如果沒有案例，返回空列表
        if not self.cases:
            logger.info("案例庫為空，返回空結果")
            return []
        
        for case in self.cases:
            # ✅ 添加：類型檢查
            if not isinstance(case, dict):
                logger.warning(f"跳過非字典類型的案例: {type(case)}")
                continue
            
            score = 0
            case_symptoms = case.get('symptoms', [])
            
            # ✅ 添加：確保症狀是列表
            if not isinstance(case_symptoms, list):
                logger.warning(f"案例症狀格式錯誤: {type(case_symptoms)}")
                continue
            
            # 計算症狀匹配度
            for sym in symptoms:
                if sym in case_symptoms:
                    score += 1
            
            if score > 0:
                case_copy = case.copy()
                case_copy['similarity_score'] = score / max(len(symptoms), 1)
                results.append(case_copy)
        
        # 排序
        results.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
        return results[:top_k]
