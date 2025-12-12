import weaviate
import logging
from typing import Dict, Any, List
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class WeaviateClient:
    """
    規格書 3.2 資料庫 Schema 設計 (BYOV Mode)
    """
    def __init__(self):
        try:
            self.client = weaviate.connect_to_local(
                host=settings.WEAVIATE_URL.replace("http://", "").split(":")[0],
                port=int(settings.WEAVIATE_URL.split(":")[-1]),
            )
            logger.info(f"Connected to Weaviate at {settings.WEAVIATE_URL}")
        except Exception as e:
            logger.error(f"Failed to connect to Weaviate: {str(e)}")
            raise e

    def close(self):
        self.client.close()

    def search_similar_cases(self, vector: List[float], limit: int = 1) -> List[Dict[str, Any]]:
        """Path A: 檢索相似案例"""
        try:
            collection = self.client.collections.get("TCM_Reference_Case")
            response = collection.query.near_vector(
                near_vector=vector,
                limit=limit,
                return_metadata=["distance"]
            )
            
            results = []
            for obj in response.objects:
                # Cosine Similarity = 1 - distance (Weaviate uses cosine distance)
                similarity = 1 - obj.metadata.distance
                results.append({
                    **obj.properties,
                    "similarity": similarity,
                    "id": str(obj.uuid)
                })
            return results
            
        except Exception as e:
            logger.error(f"[Weaviate] Search cases failed: {str(e)}")
            return []

    def insert_case(self, case_data: Dict[str, Any], vector: List[float]):
        """學習閉環：寫入新案例"""
        try:
            collection = self.client.collections.get("TCM_Reference_Case")
            collection.data.insert(
                properties=case_data,
                vector=vector
            )
            logger.info(f"[Weaviate] Inserted new case: {case_data.get('case_id')}")
        except Exception as e:
            logger.error(f"[Weaviate] Insert case failed: {str(e)}")
            raise e

    def search_diagnostic_rules(self, vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """Path B: 檢索診斷規則"""
        try:
            collection = self.client.collections.get("TCM_Diagnostic_Rules")
            response = collection.query.near_vector(
                near_vector=vector,
                limit=limit,
                return_metadata=["distance"]
            )
            
            results = []
            for obj in response.objects:
                results.append({
                    **obj.properties,
                    "similarity": 1 - obj.metadata.distance,
                    "id": str(obj.uuid)
                })
            return results
            
        except Exception as e:
            logger.error(f"[Weaviate] Search rules failed: {str(e)}")
            return []