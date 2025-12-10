import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class OutputGuard:
    """
    規格書 5.2 輸出端防護
    1. LLM05 (輸出處理): JSON Schema 驗證
    2. LLM09 (錯誤資訊): 證據追溯檢查 (Evidence Trace Check)
    """

    @staticmethod
    def validate_structure(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證 LLM 輸出的 JSON 是否包含必要欄位。
        """
        required_fields = ["response_type", "diagnosis_list", "evidence_trace"]
        
        try:
            missing = [f for f in required_fields if f not in data]
            if missing:
                logger.error(f"[OutputGuard] Missing required fields in LLM output: {missing}")
                # 嘗試修復：補上預設值
                if "evidence_trace" not in data:
                    data["evidence_trace"] = "警告：系統未能生成完整推導過程 (Missing Trace)"
                if "diagnosis_list" not in data:
                    data["diagnosis_list"] = []
                if "response_type" not in data:
                    data["response_type"] = "FALLBACK"
            
            # 2. Evidence Trace Check (LLM09)
            if not data.get("evidence_trace") or len(data["evidence_trace"]) < 5:
                logger.warning("[OutputGuard] Evidence trace is empty or too short. Intercepting.")
                data["evidence_trace"] = "警告：系統偵測到推導證據不足，請醫師謹慎參考。"
                # 強制降級為 FALLBACK
                data["response_type"] = "FALLBACK"

            return data

        except Exception as e:
            logger.error(f"[OutputGuard] Validation Logic Error: {str(e)}")
            # 發生嚴重錯誤時，回傳一個安全的空物件
            return {
                "response_type": "FALLBACK",
                "diagnosis_list": [],
                "evidence_trace": "System Error in Output Guard",
                "follow_up_question": {"required": True, "question_text": "系統輸出驗證失敗，請重試。"}
            }