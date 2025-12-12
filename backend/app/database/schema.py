from typing import List, Dict, Any

class WeaviateSchema:
    """
    規格書 3.2 資料庫 Schema (Weaviate - BYOV Mode)
    
    核心原則:
    1. 所有 Class 設定 vectorizer: "none" (由 Python 端調用 NVIDIA API 生成向量)。
    2. 包含四個核心類別: Reference Case, Ontology, Session Memory, Diagnostic Rules。
    """
    
    @staticmethod
    def get_schema() -> List[Dict[str, Any]]:
        return [
            # 1. TCM_Reference_Case (核心案例庫 - 用於 Path A)
            {
                "class": "TCM_Reference_Case",
                "description": "Path A 檢索用的專家案例 (SEEDED) 與學習案例 (LEARNED)",
                "vectorizer": "none",
                "properties": [
                    {"name": "case_id", "dataType": ["text"]},
                    {"name": "source_type", "dataType": ["text"]},  # 'SEEDED' 或 'LEARNED' (JSON: type)
                    {"name": "chief_complaint", "dataType": ["text"]},
                    {"name": "symptom_tags", "dataType": ["text[]"]},
                    {"name": "diagnosis_main", "dataType": ["text"]},   # 病名 (JSON: diagnosis_disease + diagnosis_syndrome)
                    {"name": "treatment_principle", "dataType": ["text"]},
                    {"name": "pathology_analysis", "dataType": ["text"]}, # JSON: pathology_analysis
                    {"name": "confidence_score", "dataType": ["number"]},
                ]
            },
            
            # 2. TCM_Standard_Ontology (標準術語庫 - 用於 Path B Translator)
            {
                "class": "TCM_Standard_Ontology",
                "description": "Path B 語意標準化用的術語定義",
                "vectorizer": "none",
                "properties": [
                    {"name": "term_id", "dataType": ["text"]},
                    {"name": "term_name", "dataType": ["text"]},
                    {"name": "category", "dataType": ["text"]},
                    {"name": "definition", "dataType": ["text"]},
                    {"name": "synonyms", "dataType": ["text[]"]},
                ]
            },
            
            # 3. TCM_Session_Memory (螺旋對話記憶 - 用於 Context & LLM10)
            {
                "class": "TCM_Session_Memory",
                "description": "螺旋上下文追溯與對話歷史記錄",
                "vectorizer": "none",
                "properties": [
                    {"name": "patient_id", "dataType": ["text"]},  # Hashed ID
                    {"name": "session_id", "dataType": ["text"]},
                    {"name": "turn_index", "dataType": ["int"]},
                    {"name": "role", "dataType": ["text"]},
                    {"name": "content", "dataType": ["text"]},
                    {"name": "diagnosis_summary", "dataType": ["text"]},
                    {"name": "timestamp", "dataType": ["date"]},
                ]
            },
            
            # 4. TCM_Diagnostic_Rules (診斷規則庫 - 用於 Path B Reasoning)
            {
                "class": "TCM_Diagnostic_Rules",
                "description": "Path B 規則檢索，用於解決幻覺與提供邏輯依據",
                "vectorizer": "none",
                "properties": [
                    {"name": "rule_id", "dataType": ["text"]},
                    {"name": "syndrome_name", "dataType": ["text"]},
                    {"name": "category", "dataType": ["text"]},
                    {"name": "main_symptoms", "dataType": ["text[]"]},
                    {"name": "secondary_symptoms", "dataType": ["text[]"]},
                    {"name": "tongue_pulse", "dataType": ["text[]"]}, # Changed to list
                    {"name": "exclusion", "dataType": ["text[]"]},     # Changed to list
                    # Removed condition_logic
                    {"name": "treatment_principle", "dataType": ["text"]}, # Renamed from associated_treatment
                ]
            }
        ]