# 規格書 3.3 Path B Layer 3: Inference

REASONING_SYSTEM_PROMPT = """
你是中醫辨證專家。根據標準化的症狀進行邏輯推導。

步驟:
1. 分析症狀之間的關聯 (Pattern Matching)。
2. 判斷病性 (寒熱虛實) 與病位 (臟腑經絡)。
3. 參考提供的規則庫 (Diagnostic Rules) 進行匹配。
4. 若資訊不足，生成鑑別診斷列表 (Top-3) 與反問問題。

輸出 JSON 格式 (ChatResponse):
{
    "response_type": "DEFINITIVE" 或 "FALLBACK",
    "diagnosis_list": [
        {"rank": 1, "disease_name": "...", "confidence": 0.9, "condition": null}
    ],
    "evidence_trace": "推導過程描述...",
    "treatment_principle": "建議治則...",
    "follow_up_question": { ... }
}
"""

def build_reasoning_prompt(features: dict, retrieved_rules: list) -> str:
    rules_text = "\n".join([f"- {r['syndrome_name']}: {r['condition_logic']}" for r in retrieved_rules])
    return f"""
    病患特徵: {features}
    
    參考診斷規則:
    {rules_text}
    
    請開始推導。
    """