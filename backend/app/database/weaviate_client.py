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

    def get_all_ids(self, class_name: str) -> set:
        """
        Retrieves all existing IDs (case_id, term_id, or rule_id) for a given class.
        """
        existing_ids = set()
        try:
            collection = self.client.collections.get(class_name)
            for obj in collection.iterator():
                if class_name == "TCM_Reference_Case":
                    if obj.properties.get("case_id"):
                        existing_ids.add(obj.properties["case_id"])
                elif class_name == "TCM_Standard_Ontology":
                    if obj.properties.get("term_id"):
                        existing_ids.add(obj.properties["term_id"])
                elif class_name == "TCM_Diagnostic_Rules":
                    if obj.properties.get("rule_id"):
                        existing_ids.add(obj.properties["rule_id"])
            logger.info(f"[Weaviate] Retrieved {len(existing_ids)} existing IDs for {class_name}.")
        except Exception as e:
            logger.error(f"[Weaviate] Failed to retrieve IDs for {class_name}: {str(e)}")
        return existing_ids

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

    def insert_generic(self, class_name: str, properties: Dict[str, Any], vector: List[float]):
        """
        Generic method to insert data into any Weaviate collection.
        """
        try:
            collection = self.client.collections.get(class_name)
            collection.data.insert(
                properties=properties,
                vector=vector
            )
            item_id = properties.get('case_id') or properties.get('term_id') or properties.get('rule_id')
            logger.info(f"[Weaviate] Inserted into {class_name} ID: {item_id}")
        except Exception as e:
            logger.error(f"[Weaviate] Generic insert failed for {class_name} ID {properties.get('case_id')}: {str(e)}")
            raise e

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

    def get_session_history(self, patient_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve session history for a specific patient.
        """
        try:
            collection = self.client.collections.get("TCM_Session_Memory")
            # Weaviate v4 filter API
            from weaviate.classes.query import Filter
            
            response = collection.query.fetch_objects(
                filters=Filter.by_property("patient_id").equal(patient_id),
                limit=limit
            )
            
            results = []
            for obj in response.objects:
                results.append(obj.properties)
            
            return results
        except Exception as e:
            logger.error(f"[Weaviate] Get session history failed: {str(e)}")
            return []

    def add_session_memory(self, memory_data: Dict[str, Any]):
        """
        Store session history into Weaviate.
        """
        try:
            collection = self.client.collections.get("TCM_Session_Memory")
            collection.data.insert(properties=memory_data)
            logger.info(f"[Weaviate] Added session memory for {memory_data.get('session_id')}")
        except Exception as e:
            logger.error(f"[Weaviate] Add session memory failed: {str(e)}")
            raise e