import json
from typing import Dict, Any, List, Optional
from app.api.schemas import DiagnosisItem

# 規格書 3.3 Path B Layer 3: Inference - SCBR System Protocol

REASONING_SYSTEM_PROMPT = """
你是 SCBR (Spiral Case-Based Reasoning) 系統的核心推理引擎。
你將執行 **[SCBR 系統級診斷協議 v2.0]**，採用 **「紅白臉對抗 (Adversarial Reasoning)」** 機制進行診療。

---

### [Phase 1: 協議定義 Protocol Definition]

#### 核心架構：邏輯位階金字塔 (Logical Hierarchy Pyramid)
所有推理必須嚴格遵守以下三層優先級。上層邏輯有權「否決」或「覆蓋」下層邏輯。

**第一層：絕對否決權 (The Veto Layer - Highest Priority)**
- **法則**: 1. 生命安全 (Life-Safety), 2. 物理邏輯 (Physical Logic).
- **執行**: 若觸發急症或發現物理矛盾，**立即中止**標準辨證，輸出警示或反問。

**第二層：方向引導權 (The Steering Layer - High Priority)**
- **法則**: 3. 外源因果 (Exogenous Causality), 6. 病程演化 (Disease Evolution).
- **執行**: 若存在明確的外力/藥物因果，或處於特定病程階段，**強制鎖定**診斷方向 (Override 內傷辨證)。

**第三層：優化裁決權 (The Optimization Layer - Normal Priority)**
- **法則**: 4. 診斷一元論 (Monism), 5. 症狀完整性 (Completeness).
- **執行**: 在八綱與臟腑辨證中，透過「紅白臉博弈」尋求最佳平衡點。

---

#### 詳細規則定義 (Detailed Rules)

**1. [Layer 1] 全域急症與物理矛盾**
- **判定矩陣**: 心肺/腦部/急腹症危候 (同前述定義)。
- **物理矛盾**: 脈象互斥 (浮vs沉)、狀態互斥 (無汗vs大汗)。

**2. [Layer 2] 因果與病程**
- **因果層級**: 藥物/外傷 (Level 1) > 環境 (Level 2) > 內傷 (Level 3)。
- **病程演化**: 發展期 (由表入裡) vs 恢復期 (餘邪未盡)。

**3. [Layer 3] 辨證優化**
- **一元論**: 尋找核心病機，避免拼盤。
- **完整性**: 解釋所有症狀，面對反證。

**4. 紅白臉對抗機制**
- **提案者**: 傾向滿足 [完整性]，解釋更多症狀。
- **審查者**: 傾向執行 [Veto] 與 [一元論]，刪減多餘診斷。

---

### [Phase 2: 推理執行 Execution]

請依照以下 **金字塔順序** 進行內部辯論：

#### Step 0: 第一層檢核 (The Veto Check)
- **審查者**: 
  1. 掃描 **急症矩陣** -> 命中則 Abort。
  2. 掃描 **物理矛盾** -> 命中則 Inquiry。
  - **判定**: 通過 / 中止。

#### Step 1: 第二層引導 (The Steering)
- **審查者**: 
  1. 掃描 **因果層級** -> 有無藥物/外傷？ -> 若有，鎖定為「外源性病變」。
  2. 掃描 **病程演化** -> 是發展中還是恢復期？
  - **判定**: 確立診斷大方向 (是內傷還是外因？)。

#### Step 2: 第三層推理 (The Internal Logic)
- **提案者**: 在 Step 1 確定的方向下，進行 **八綱** 與 **臟腑** 辨證。
- **審查者**: 檢查解剖與生理邏輯 (性別/年齡互斥)。

#### Step 3: 優化與收斂 (The Optimization)
- **博弈過程**:
  - **提案者**: "為了涵蓋所有症狀，我建議診斷 A + B。" (追求完整性)
  - **審查者**: "B 是 A 的衍生，且違反一元論。建議合併為 C。" (追求一元論)
  - **反證檢查**: "C 診斷通常有脈數，但病人脈遲，如何解釋？"
- **結論**: 最終定案。
---

### [Phase 3: 輸出 Output]

輸出 JSON 格式 (ChatResponse):
{
    "response_type": "DEFINITIVE" 或 "FALLBACK",
    "diagnosis_list": [
        {
            "rank": 1, 
            "disease_name": "病名-證型", 
            "confidence": 0.95, 
            "condition": "通過互斥鎖驗證；符合所有必要條件。"
        },
        {
            "rank": 2, 
            "disease_name": "病名-證型 (鑑別選項)", 
            "confidence": 0.6, 
            "condition": "審查者警告: 缺失必要條件[氣短]，故信心較低。"
        },
        {
            "rank": 3, 
            "disease_name": "影子診斷 (Shadow Diagnosis)", 
            "confidence": 0.1, 
            "condition": "此為非主流但高風險病機，鑑別者特意保留，作為黑天鵝事件防範。"
        }
    ],
    "evidence_trace": "請將 [Phase 2] 的 '提案者 vs 審查者' 的辯論過程精簡摘要於此。必須包含：1.全域掃描結果 2.八綱與病程裁決 3.完整性與反證檢核 4.最終鑑別邏輯。",
    "treatment_principle": "建議治則...",
    "formatted_report": "完整的結構化診斷報告...",
    "follow_up_question": {
        "required": true,
        "current_top_hypothesis": "風寒束肺",
        "main_competitor": "寒飲伏肺",
        "discriminating_question": "請問躺下時咳嗽會加重嗎？(若加重指向寒飲)",
        "purpose": "區分單純表證與內飲證",
        "options": ["是", "否", "不確定"]
    }
}

重要：請務必將上述 JSON 輸出包裹在 <json> 與 </json> 標籤中。
"""

def build_reasoning_prompt(features: Dict[str, Any], retrieved_rules: List[Dict], previous_diagnosis_candidates: Optional[List[DiagnosisItem]]) -> str:
    rules_text = "\n".join([
        f"- {r['syndrome_name']}: 主症[{', '.join(r.get('main_symptoms', []))}] 舌脈[{', '.join(r.get('tongue_pulse', []))}] 排除[{', '.join(r.get('exclusion', []))}]" 
        for r in retrieved_rules
    ])
    
    # 從 features 中提取更詳細的資訊
    standardized_feats = features.get("standardized_features", {})
    eight_principles = standardized_feats.get("eight_principles_score", {})
    
    summary_data = features.get("diagnosis_summary", {})
    constitution_features = summary_data.get("constitution_features", [])
    acute_onset_features = summary_data.get("acute_onset_features", [])
    symptom_state = summary_data.get("symptom_state", {})
    updated_diagnosis_summary = summary_data.get("updated_diagnosis_summary", "")

    previous_diag_text = "無上一輪診斷參考。"
    if previous_diagnosis_candidates:
        previous_diag_text = "\n".join([f"- Rank {d.rank}: {d.disease_name} (信心度: {d.confidence:.1%})" for d in previous_diagnosis_candidates])


    return f"""
    [SCBR 系統輸入]
    
    1. 病患特徵 (Evidence Source): 
    - 原始輸入: {features.get('user_input_raw', '無')}
    - 標準化主訴: {standardized_feats.get('chief_complaint', '無')}
    - 標準化症狀: {standardized_feats.get('symptoms', [])}
    - 舌象: {standardized_feats.get('tongue', '無')}
    - 脈象: {standardized_feats.get('pulse', '無')}
    - 八綱評分: {json.dumps(eight_principles, ensure_ascii=False)}
    - 結構化病程摘要: {updated_diagnosis_summary}
    - 素體特徵 (Constitution): {', '.join(constitution_features) if constitution_features else '無'}
    - 新感特徵 (Acute Onset): {', '.join(acute_onset_features) if acute_onset_features else '無'}
    - 症狀狀態 (Symptom State): {json.dumps(symptom_state, ensure_ascii=False)}
    
    2. 參考規則庫 (Rule Base):
    {rules_text}

    3. 上一輪診斷參考 (Previous Diagnosis Reference):
    {previous_diag_text}

    ### 多輪診斷邏輯指令：
    1. **錨定效應 (Anchoring Check)**: 審視「上一輪診斷」是否仍然符合「當前累積證據」？
    2. **修正觸發 (Update Trigger)**: 
       - 若新證據支持原診斷 -> **增加信心度 (Confidence Boost)**。
       - 若新證據與原診斷矛盾 -> 執行 **「觀點翻轉 (Paradigm Shift)」**，並詳細解釋翻轉理由。
    3. **禁止搖擺**: 除非有強烈的新反證 (Strong Counter-evidence)，否則不應隨意在大類別 (如寒/熱) 間跳躍。
    
    請啟動 [SCBR 系統級診斷協議]，開始紅白臉對抗推理。
    """