import re
import logging
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class InputGuard:
    """
    規格書 5.1 輸入端防護
    1. LLM02 (PII 洩漏): 遮罩敏感資訊
    2. LLM01 (Prompt Injection): 攔截攻擊關鍵字
    """
    
    # 簡單的 PII 正則表達式 (針對台灣身分證與姓名做簡單遮罩)
    # 注意: 實際生產環境可能需要更複雜的 NER 模型
    ID_PATTERN = r'[A-Z][1-2]\d{8}'
    NAME_PATTERN = r'(?<=姓名[:：\s])([\u4e00-\u9fa5]{2,4})' 
    
    # Injection 關鍵字 (黑名單)
    INJECTION_KEYWORDS = [
        "ignore previous instructions",
        "system prompt",
        "忽略前面的指示",
        "原本的指令"
    ]

    @classmethod
    def validate(cls, user_input: str) -> str:
        """
        執行輸入清洗與驗證。
        若偵測到攻擊，拋出 ValueError。
        若偵測到 PII，自動替換。
        """
        try:
            # 1. Injection Check
            for keyword in cls.INJECTION_KEYWORDS:
                if keyword in user_input.lower():
                    logger.warning(f"[Security Alert] Potential Prompt Injection detected: {keyword}")
                    raise ValueError("輸入包含非法指令，已攔截。")

            # 2. PII Masking
            sanitized_input = user_input
            
            # Mask ID
            ids_found = re.findall(cls.ID_PATTERN, sanitized_input)
            if ids_found:
                logger.info(f"[Privacy] Masked {len(ids_found)} ID numbers.")
                sanitized_input = re.sub(cls.ID_PATTERN, "<PATIENT_ID>", sanitized_input)
            
            # Mask Name (簡易版)
            names_found = re.findall(cls.NAME_PATTERN, sanitized_input)
            if names_found:
                logger.info(f"[Privacy] Masked potential names.")
                sanitized_input = re.sub(cls.NAME_PATTERN, "<PATIENT_NAME>", sanitized_input)

            return sanitized_input

        except ValueError as ve:
            # 重新拋出業務邏輯錯誤
            raise ve
        except Exception as e:
            logger.error(f"[InputGuard] Unexpected error during validation: {str(e)}")
            # 安全起見，若清洗失敗，回傳原始輸入但標記 Log，或視政策決定是否阻擋
            # 這裡選擇回傳原始輸入以免中斷服務，但在 Log 中留底
            return user_input

    @staticmethod
    def hash_patient_id(raw_id: str) -> str:
        """
        將真實身分證號轉為 Hash ID (用於 Weaviate 儲存)
        """
        import hashlib
        try:
            salt = settings.PATIENT_ID_SALT
            combined = f"{raw_id}{salt}".encode('utf-8')
            hashed = hashlib.sha256(combined).hexdigest()
            return hashed[:16] # 取前16碼即可
        except Exception as e:
            logger.error(f"[InputGuard] Hashing failed: {str(e)}")
            raise e