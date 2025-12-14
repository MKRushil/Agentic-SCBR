import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any, Optional
import logging

# 設置為 Silent 模式，僅在錯誤時 Log
logger = logging.getLogger("SCBR_Evaluator")

class SCBREvaluator:
    """
    SCBR vFinal 評估器 (符合 10 大指標規格)
    Design Pattern: Silent Plugin (無副作用，純邏輯計算)
    """
    def __init__(self):
        self.logs = [] 

    def log_turn(self, turn_data: Dict[str, Any]):
        """
        記錄單輪數據。
        必須包含: pred_attributes, pred_vector (可選), gt_vector (可選)
        """
        self.logs.append(turn_data)

    def reset(self):
        self.logs = []

    # ==========================================
    # A. 準確度 (Accuracy) - 邏輯鎖驗證
    # ==========================================

    def calculate_hybrid_accuracy(self) -> float:
        """指標 1: Hybrid Semantic Accuracy (混合語意準確率)"""
        scores = []
        for log in self.logs:
            if not log.get('gt_diagnosis'): continue # Online Mode without GT
            
            # 1. 向量分數 (若無向量，退化為字串比對)
            vec_score = 0.0
            if 'pred_vector' in log and 'gt_vector' in log and log['pred_vector'] and log['gt_vector']:
                try:
                    v1 = np.array(log['pred_vector']).reshape(1, -1)
                    v2 = np.array(log['gt_vector']).reshape(1, -1)
                    vec_score = cosine_similarity(v1, v2)[0][0]
                except Exception as e:
                    logger.warning(f"Vector similarity calculation failed: {e}")
                    vec_score = 0.0
            else:
                # Fallback: 若文字完全相同給 1.0，否則 0.5 (同義詞無法捕捉)
                vec_score = 1.0 if log['pred_diagnosis'] == log['gt_diagnosis'] else 0.5

            # 2. 邏輯懲罰 (Penalty)
            penalty = 0.0
            p_attr = log.get('pred_attributes', {})
            g_attr = log.get('gt_attributes', {})
            
            # 檢核寒熱 (Nature)
            if p_attr.get('nature') and g_attr.get('nature'):
                if p_attr['nature'] != g_attr['nature']:
                    penalty = 1.0 # 致命錯誤
            
            # 檢核虛實 (Deficiency)
            if p_attr.get('deficiency') and g_attr.get('deficiency'):
                if p_attr['deficiency'] != g_attr['deficiency']:
                    penalty = 1.0

            final_score = max(0.0, vec_score * (1.0 - penalty))
            scores.append(final_score)
            
        return float(np.mean(scores)) if scores else 0.0

    def calculate_effective_recall(self) -> float:
        """指標 2: Effective Recall (排除 Inquiry 的召回率)"""
        total_definitive = 0
        correct_definitive = 0
        
        for log in self.logs:
            if not log.get('gt_diagnosis'): continue # Online Mode without GT
            
            # 只看已確診的回合
            if log['pred_response_type'] == 'DEFINITIVE':
                total_definitive += 1
                if log['pred_diagnosis'] == log['gt_diagnosis']: # 或語意相似
                    correct_definitive += 1
        
        return correct_definitive / total_definitive if total_definitive > 0 else 0.0

    def calculate_rejection_precision(self) -> float:
        """指標 3: Rejection Precision (拒絕精確率)"""
        # 統計系統觸發 "CASE_REJECTED" (通常轉為 FALLBACK/INQUIRY 且帶有 reject 標記)
        # 這裡假設 log 中有一個欄位 'is_rejected_action'
        true_rejects = 0
        total_rejects = 0
        
        for log in self.logs:
            if not log.get('gt_diagnosis'): continue # Online Mode without GT
            
            if log.get('is_rejected_action', False):
                total_rejects += 1
                # 判斷拒絕是否正確：看 GT 是否真的屬性衝突
                # 這裡需要更精細的邏輯，例如比較 pred_attributes 和 gt_attributes
                p_attr = log.get('pred_attributes', {})
                g_attr = log.get('gt_attributes', {})
                
                # 簡易判斷：如果寒熱屬性相反，則認為拒絕是正確的
                if p_attr.get('nature') and g_attr.get('nature') and p_attr['nature'] != g_attr['nature']:
                    true_rejects += 1
                    
        return true_rejects / total_rejects if total_rejects > 0 else 1.0 # 預設無拒絕視為完美

    def calculate_logic_f1(self) -> float:
        """指標 4: Logic-Weighted F1"""
        # 使用 Effective Recall 和 Hybrid Accuracy (作為 Precision 的近似)
        r = self.calculate_effective_recall()
        p = self.calculate_hybrid_accuracy() 
        
        if (p + r) == 0: return 0.0
        return 2 * (p * r) / (p + r)

    def calculate_critical_conflict_rate(self) -> float:
        """指標 5: Critical Conflict Rate (越低越好)"""
        conflicts = 0
        total_definitive = 0
        for log in self.logs:
            if not log.get('gt_diagnosis'): continue # Online Mode without GT
            
            if log['pred_response_type'] == 'DEFINITIVE':
                total_definitive += 1
                p_attr = log.get('pred_attributes', {})
                g_attr = log.get('gt_attributes', {})
                # 檢查寒熱與虛實
                if (p_attr.get('nature') and g_attr.get('nature') and p_attr['nature'] != g_attr['nature']) or \
                   (p_attr.get('deficiency') and g_attr.get('deficiency') and p_attr['deficiency'] != g_attr['deficiency']):
                    conflicts += 1
        return conflicts / total_definitive if total_definitive > 0 else 0.0

    # ==========================================
    # B. 效率 (Efficiency) - 收斂速度
    # ==========================================

    def calculate_incremental_slope(self) -> float:
        """指標 6: Incremental Hit Slope"""
        slopes = []
        cases = set(l['case_id'] for l in self.logs)
        for cid in cases:
            case_logs = sorted([l for l in self.logs if l['case_id'] == cid], key=lambda x: x['turn_id'])
            if len(case_logs) < 2: continue
            turns = [l['turn_id'] for l in case_logs]
            confs = [l['pred_confidence'] for l in case_logs]
            try:
                slope, _ = np.polyfit(turns, confs, 1)
                slopes.append(slope)
            except: pass
        return float(np.mean(slopes)) if slopes else 0.0

    def calculate_turns_to_stability(self) -> float:
        """指標 7: Turns to Stability (TTS)"""
        tts_values = []
        cases = set(l['case_id'] for l in self.logs)
        for cid in cases:
            case_logs = sorted([l for l in self.logs if l['case_id'] == cid], key=lambda x: x['turn_id'])
            
            # 如果是 Online 模式，沒有 GT，則只檢查連續穩定
            gt = case_logs[0].get('gt_diagnosis') 

            stable_turn = -1
            hits = 0
            
            for log in case_logs:
                # 判定穩定：連續兩次確診且 (正確 或 無 GT 模式)
                is_correct = (gt is None) or (log['pred_diagnosis'] == gt)
                
                if log['pred_response_type'] == 'DEFINITIVE' and is_correct:
                    hits += 1
                    if hits >= 2: # 連續兩輪命中視為穩定
                        stable_turn = log['turn_id'] 
                        break
                else:
                    hits = 0 # 中斷重算
            
            if stable_turn != -1: tts_values.append(stable_turn)
            else: tts_values.append(len(case_logs)) # 懲罰: 未收斂則算最大輪數
            
        return float(np.mean(tts_values)) if tts_values else 0.0

    def calculate_ambiguity_resolution_rate(self) -> float:
        """指標 8: Ambiguity Resolution Rate"""
        rates = []
        cases = set(l['case_id'] for l in self.logs)
        for cid in cases:
            case_logs = sorted([l for l in self.logs if l['case_id'] == cid], key=lambda x: x['turn_id'])
            for i in range(len(case_logs) - 1):
                # 僅在系統處於 Inquiry 模式時計算
                if case_logs[i]['pred_response_type'] == 'INQUIRY_ONLY':
                    curr = case_logs[i]['ambiguous_terms_count']
                    next_ = case_logs[i+1]['ambiguous_terms_count']
                    if curr > 0:
                        rates.append((curr - next_) / curr) # 計算減少的比例
                    else:
                        rates.append(1.0) # 如果已經沒有模糊項了，算解決
        return float(np.mean(rates)) if rates else 0.0

    # ==========================================
    # C. 軌跡 (Trajectory) - 合規性
    # ==========================================

    def calculate_structure_match_score(self) -> float:
        """指標 9: Structure-Match Score (Jaccard)"""
        scores = []
        for log in self.logs:
            if not log.get('gt_attributes'): continue # Online Mode without GT
            
            p_feats = set(log.get('pred_attributes', {}).items()) # 轉為 set((k,v))
            g_feats = set(log.get('gt_attributes', {}).items())
            
            if not g_feats: continue # 防止 GT 為空
            
            intersection = len(p_feats & g_feats)
            union = len(p_feats | g_feats)
            scores.append(intersection / union if union > 0 else 0.0)
            
        return float(np.mean(scores)) if scores else 0.0

    def calculate_funnel_adherence(self) -> float:
        """指標 10: Funnel Adherence Score"""
        illegal = 0
        total = 0
        
        for log in self.logs:
            total += 1
            # 規則 1: 急症必須攔截 (僅在有 GT 時檢查)
            if log.get('is_emergency_gt') is not None:
                if log['is_emergency_gt'] and log['pred_response_type'] not in ['EMERGENCY_ABORT', 'FALLBACK', 'INQUIRY_ONLY']: # 允許 Inquiry
                    illegal += 1
            
            # 規則 2: 模糊項過多不可確診
            elif log['ambiguous_terms_count'] >= 2 and log['pred_response_type'] == 'DEFINITIVE':
                illegal += 1
                
        return 1.0 - (illegal / total) if total > 0 else 1.0

    def get_summary_report(self) -> Dict[str, float]:
        """輸出 10 大指標總表"""
        return {
            "A1_Hybrid_Accuracy": self.calculate_hybrid_accuracy(),
            "A2_Effective_Recall": self.calculate_effective_recall(),
            "A3_Rejection_Precision": self.calculate_rejection_precision(),
            "A4_Logic_F1": self.calculate_logic_f1(),
            "A5_Crit_Conflict_Rate": self.calculate_critical_conflict_rate(),
            "B6_Incr_Hit_Slope": self.calculate_incremental_slope(),
            "B7_Avg_TTS": self.calculate_turns_to_stability(),
            "B8_Ambiguity_Res_Rate": self.calculate_ambiguity_resolution_rate(),
            "C9_Struct_Match_Score": self.calculate_structure_match_score(),
            "C10_Funnel_Adherence": self.calculate_funnel_adherence()
        }
