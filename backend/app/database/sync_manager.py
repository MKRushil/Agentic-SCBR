import json
import logging
import os
from typing import List, Dict, Any
from app.core.config import get_settings
from app.database.weaviate_client import WeaviateClient
from app.services.nvidia_client import NvidiaClient

settings = get_settings()
logger = logging.getLogger(__name__)

class SyncManager:
    """
    規格書 8.0: 資料同步策略 (Startup Sync)
    邏輯:
    1. 讀取 data/*.json (Single Source of Truth)
    2. 讀取 Weaviate 現有 IDs
    3. 計算差集 (Diff)
    4. 呼叫 NVIDIA Embedding 並寫入 Weaviate
    """
    
    DATA_DIR = "./data"
    FILES_MAPPING = {
        "TCM_Reference_Case": "tcm_expert_cases.json",
        "TCM_Standard_Ontology": "tcm_ontology.json",
        "TCM_Diagnostic_Rules": "tcm_diagnostic_rules.json"
    }

    def __init__(self):
        self.weaviate_client = WeaviateClient()
        self.nvidia_client = NvidiaClient()

    async def run_sync(self):
        logger.info("[Sync] Starting data synchronization...")
        
        try:
            for class_name, filename in self.FILES_MAPPING.items():
                file_path = os.path.join(self.DATA_DIR, filename)
                if not os.path.exists(file_path):
                    logger.warning(f"[Sync] File not found: {file_path}, skipping.")
                    continue

                # 1. Load JSON
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                    # 假設 JSON 是一個 List
                    if not isinstance(file_data, list):
                        logger.error(f"[Sync] Invalid JSON format in {filename}, expected List.")
                        continue

                # 2. Get Existing IDs from Weaviate (Mocking logic here)
                # 真實情況需 query Weaviate 取得所有 ID
                # existing_ids = self.weaviate_client.get_all_ids(class_name)
                existing_ids = set() 
                
                # 3. Calculate Diff & Insert
                new_items = []
                for item in file_data:
                    item_id = item.get("case_id") or item.get("term_id") or item.get("rule_id")
                    if item_id and item_id not in existing_ids:
                        new_items.append(item)

                if new_items:
                    logger.info(f"[Sync] Found {len(new_items)} new items for {class_name}.")
                    await self._process_batch(class_name, new_items)
                else:
                    logger.info(f"[Sync] {class_name} is up to date.")

        except Exception as e:
            logger.error(f"[Sync] Critical Error during sync: {str(e)}")
            # 不拋出錯誤，讓 App 繼續啟動，但記錄 Log
        finally:
            self.weaviate_client.close()

    async def _process_batch(self, class_name: str, items: List[Dict]):
        """
        序列化處理 Embedding 並寫入，避免觸發 API Rate Limit
        """
        for item in items:
            try:
                # 準備 Embedding Text 與 屬性轉換 (ETL)
                properties = {}
                text_to_embed = ""
                
                if class_name == "TCM_Reference_Case":
                    text_to_embed = f"{item.get('chief_complaint')} {' '.join(item.get('symptom_tags', []))}"
                    
                    # ETL: Map JSON fields to Schema
                    properties = {
                        "case_id": item.get("case_id"),
                        "source_type": item.get("type"), # Map 'type' to 'source_type'
                        "chief_complaint": item.get("chief_complaint"),
                        "symptom_tags": item.get("symptom_tags"),
                        "diagnosis_main": f"{item.get('diagnosis_disease')} - {item.get('diagnosis_syndrome')}", # Combine
                        "treatment_principle": item.get("treatment_principle"),
                        "pathology_analysis": item.get("pathology_analysis"),
                        "confidence_score": item.get("confidence_score")
                    }
                    
                elif class_name == "TCM_Standard_Ontology":
                    text_to_embed = f"{item.get('term_name')} {item.get('definition')}"
                    properties = item # 欄位大致相符
                    
                elif class_name == "TCM_Diagnostic_Rules":
                    text_to_embed = f"{item.get('syndrome_name')} {' '.join(item.get('main_symptoms', []))}"
                    properties = {
                        "rule_id": item.get("rule_id"),
                        "syndrome_name": item.get("syndrome_name"),
                        "category": item.get("category"),
                        "main_symptoms": item.get("main_symptoms"),
                        "secondary_symptoms": item.get("secondary_symptoms"),
                        "tongue_pulse": item.get("tongue_pulse"), # Now a list
                        "exclusion": item.get("exclusion"),
                        "treatment_principle": item.get("treatment_principle")
                    }

                # 呼叫 Embedding API
                vector = await self.nvidia_client.get_embedding(text_to_embed)
                
                # 寫入 Weaviate
                # 使用通用的 client.insert 方法 (需確認 WeaviateClient 有此方法，這裡假設有或直接調用)
                # 為了避免 AttributeError，我們先假設 WeaviateClient 有一個 generic_insert
                # 但實際上您的 WeaviateClient 只有 insert_case 和 search_similar_cases
                # 我需要在此處直接調用 client 的 collection 方法，或者之後擴充 WeaviateClient
                
                # 暫時直接使用 weaviate_client 內部的 client 屬性進行操作 (若為 public)
                # 或者擴充 WeaviateClient。比較好的做法是擴充 WeaviateClient。
                # 這裡我們先呼叫一個尚未存在的方法，隨後我去補上。
                self.weaviate_client.insert_generic(class_name, properties, vector)
                
                logger.info(f"[Sync] Inserted {class_name} ID: {properties.get('case_id') or properties.get('term_id') or properties.get('rule_id')}")

            except Exception as e:
                logger.error(f"[Sync] Failed to process item in {class_name}: {str(e)}")