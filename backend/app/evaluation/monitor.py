import logging
import time
import math
from typing import Dict, Any, List
from app.api.schemas import WorkflowState
from app.evaluation.scbr_evaluator import SCBREvaluator

logger = logging.getLogger("monitoring")

class MonitorService:
    """
    規格書 6.3: 線上監控 (Online Monitoring)
    負責記錄系統運作指標：回應時間、Token 使用量、使用者反饋。
    整合 SCBREvaluator 進行 Spec 6.2 指標計算。
    """
    
    def __init__(self):
        self.evaluator = SCBREvaluator()

    @staticmethod
    def log_latency(session_id: str, endpoint: str, start_time: float):
        """
        記錄 API 延遲
        """
        latency_ms = (time.time() - start_time) * 1000
        logger.info(f"[METRIC] Type=Latency | Session={session_id} | Endpoint={endpoint} | Value={latency_ms:.2f}ms")

    @staticmethod
    def log_token_usage(session_id: str, prompt_tokens: int, completion_tokens: int):
        """
        記錄 Token 消耗 (成本監控)
        """
        total_tokens = prompt_tokens + completion_tokens
        logger.info(f"[METRIC] Type=TokenUsage | Session={session_id} | Total={total_tokens} | Prompt={prompt_tokens} | Completion={completion_tokens}")

    @staticmethod
    def log_feedback_score(session_id: str, feedback_action: str):
        """
        記錄使用者滿意度 (CSAT Proxy)
        """
        score_map = {"ACCEPT": 5, "MODIFY": 3, "REJECT": 1}
        score = score_map.get(feedback_action, 0)
        logger.info(f"[METRIC] Type=Feedback | Session={session_id} | Action={feedback_action} | Score={score}")

    def log_detailed_metrics(self, state: WorkflowState):
        """
        規格書 6.2: 紀錄詳細線上評估指標
        包含: Confidence, Path Similarity, Convergence Turns, Info Gain (Entropy)
        並同步至 SCBREvaluator。
        """
        try:
            session_id = state.session_id
            
            # 1. Semantic Confidence (Top-1 Confidence)
            max_confidence = 0.0
            confidences = []
            pred_diag = ""
            
            if state.diagnosis_candidates:
                max_confidence = state.diagnosis_candidates[0].confidence
                pred_diag = state.diagnosis_candidates[0].disease_name
                confidences = [d.confidence for d in state.diagnosis_candidates]
            
            logger.info(f"[METRIC] Type=SemanticConfidence | Session={session_id} | Value={max_confidence:.4f}")

            # 2. Path Similarity (Max Similarity from Retrieval) -> Proxy for V-SCR
            max_sim = 0.0
            if state.retrieved_context:
                try:
                    max_sim = max([item.get('similarity', 0.0) for item in state.retrieved_context], default=0.0)
                except:
                    pass
            logger.info(f"[METRIC] Type=PathSimilarity | Session={session_id} | Value={max_sim:.4f}")
            
            # 3. Path Selected
            logger.info(f"[METRIC] Type=PathSelected | Session={session_id} | Value={state.path_selected}")
            
            # 4. Convergence Turns
            logger.info(f"[METRIC] Type=TurnProcessed | Session={session_id} | Timestamp={time.time()}")

            # 5. Info Gain (Entropy)
            entropy = 0.0
            if confidences:
                total_conf = sum(confidences)
                if total_conf > 0:
                    probs = [c / total_conf for c in confidences]
                    entropy = -sum(p * math.log2(p) for p in probs if p > 0)
            logger.info(f"[METRIC] Type=InfoEntropy | Session={session_id} | Value={entropy:.4f}")

            # --- Sync to SCBREvaluator ---
            # 嘗試從 standardized_features 獲取 ambiguous_terms_count
            amb_count = 0
            pred_attributes = {} # Initialize pred_attributes here
            
            if state.standardized_features:
                amb_count = len(state.standardized_features.get("ambiguous_terms", []))
                
                # Extract pred_attributes
                standardized = state.standardized_features
                symptoms = standardized.get("symptoms", [])
                
                # Check for sweat
                if any(k in s for s in symptoms for k in ["無汗", "不出汗"]):
                    pred_attributes['sweat'] = 'no_sweat'
                elif any(k in s for s in symptoms for k in ["自汗", "盜汗", "大汗", "汗出"]):
                    pred_attributes['sweat'] = 'sweat'

                # Extract nature and deficiency from eight_principles_score
                eight_principles = standardized.get('eight_principles_score', {})
                han = eight_principles.get('han', 0)
                re = eight_principles.get('re', 0)
                xu = eight_principles.get('xu', 0)
                shi = eight_principles.get('shi', 0)
                
                if han > re: pred_attributes['nature'] = 'cold'
                elif re > han: pred_attributes['nature'] = 'hot'
                
                if xu > shi: pred_attributes['deficiency'] = 'deficiency'
                elif shi > xu: pred_attributes['deficiency'] = 'excess'
            
            pred_type = "FALLBACK"
            if state.final_response:
                pred_type = state.final_response.response_type.value

            turn_data = {
                "case_id": session_id,
                "turn_id": int(time.time()), # Proxy for turn_id
                "input_text": state.user_input_raw,
                "gt_diagnosis": None, # Online mode: No GT
                "gt_attributes": None,
                "is_emergency_gt": None,
                "pred_response_type": pred_type,
                "pred_diagnosis": pred_diag,
                "pred_confidence": max_confidence,
                "pred_attributes": pred_attributes, # Use the populated pred_attributes
                "ambiguous_terms_count": amb_count
            }
            self.evaluator.log_turn(turn_data)

        except Exception as e:
            logger.error(f"[Monitor] Failed to log detailed metrics: {str(e)}")

    def get_online_metrics_report(self) -> Dict[str, float]:
        """
        獲取當前累積的線上評估報告
        """
        return self.evaluator.get_summary_report()

# Global Instance
monitor = MonitorService()