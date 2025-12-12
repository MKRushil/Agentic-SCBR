Agentic SCBR-CDSS 專案全方位執行規格書 (vFinal-Full)

版本: 8.0 (Master Build)

日期: 2025-12-10

核心架構: LLM + RAG + CBR + Agentic Workflow

硬體資源限制: 單執行緒序列化 (Strictly Serial Execution) - Global Mutex Lock Required

1. 系統定義與核心限制 (System Overview)

1.1 系統定位

全名: 代理式螺旋案例推理中醫輔助診斷系統 (Agentic Spiral Case-Based Reasoning CDSS)。

功能: 接收非結構化醫病對話 (多回合)，輸出「診斷建議 (病名+證型)」、「病機推導證據」與「治療策略」。

關鍵邊界 (Critical Boundary): 系統僅提供 治療方向 (治則)，嚴禁 輸出具體藥物劑量與配伍。最終處方權屬於中醫師。

1.2 資源調度策略 (Resource Orchestration)

由於硬體資源有限，系統必須實作 全域互斥鎖 (Global Mutex Lock)。

單一調用原則: Embedding API 與 LLM 推理 API 嚴禁同時調用。

執行管線 (Serial Pipeline):
Input Guard $\rightarrow$ Embedding $\rightarrow$ Vector Search $\rightarrow$ LLM (Translation) $\rightarrow$ LLM (Reasoning) $\rightarrow$ Safety Check $\rightarrow$ Visualization Adapter $\rightarrow$ Report Gen $\rightarrow$ Output $\rightarrow$ LLM (Summarization - Async Post-response).

模型指定 (NVIDIA NIM):

Embedding Model: nvidia/nv-embedqa-e5-v5 (Dimension: 1024).

Generative Model: nvidia/llama-3.3-nemotron-super-49b-v1.5 (具備強大的指令遵循與 XML/JSON 處理能力).

2. 檔案目錄結構規範 (File Structure)

本專案採用 Monorepo 架構。Python 負責後端，Vue3 負責前端。

project-root/
├── .env                       # [Config] 全域環境變數 (API Keys, URLs, Feature Flags)
├── docker-compose.yml         # [Infra] Weaviate, Backend, Frontend 服務編排
├── README.md                  # [Doc] 專案說明文件
│
├── backend/                   # [Backend] Python FastAPI
│   ├── main.py                # App 入口 (Startup Sync, CORS, Middleware)
│   ├── requirements.txt       # Python 依賴清單
│   │
│   ├── data/                  # [Data Layer] JSON Single Source of Truth
│   │   ├── tcm_expert_cases.json     # 專家案例 (Class 1 Seed)
│   │   ├── tcm_ontology.json         # 標準術語庫 (Class 2 Seed)
│   │   └── tcm_diagnostic_rules.json # 診斷規則庫 (Class 4 Seed)
│   │
│   └── app/
│       ├── __init__.py
│       ├── core/              # [Core Logic]
│       │   ├── orchestrator.py    # 總指揮 (維護 WorkflowState, 序列化鎖, 螺旋邏輯)
│       │   └── config.py          # 環境變數讀取與設定
│       │
│       ├── prompts/           # [Prompt Engineering] .py 格式模板 (Dynamic Injection)
│       │   ├── __init__.py
│       │   ├── base.py            # 系統級 System Prompt (XML輸出規範, JSON Schema)
│       │   ├── translator.py      # 語意標準化 Prompt
│       │   ├── memory.py          # Path A 差異分析 Prompt
│       │   ├── reasoning.py       # Path B 三層推理 Prompt
│       │   └── summarizer.py      # 螺旋壓縮 Prompt
│       │
│       ├── agents/            # [Agent Execution Logic]
│       │   ├── base.py            # Agent 基礎介面 (LLM 調用封裝)
│       │   ├── memory.py          # Path A Logic (Retrieve -> Align -> Revise)
│       │   ├── reasoning.py       # Path B Logic (Parser -> Triage -> Inference Pipeline)
│       │   ├── translator.py      # Normalization Logic (RAG-based)
│       │   └── summarizer.py      # Async Summarization Logic
│       │
│       ├── database/          # [Database Integration]
│       │   ├── weaviate_client.py # Client 封裝
│       │   ├── schema.py          # 4個 Class 的 Schema 定義
│       │   └── sync_manager.py    # 啟動時 JSON->DB 同步邏輯 (Set Difference 防重複)
│       │
│       ├── guardrails/        # [Security - OWASP]
│       │   ├── input_guard.py     # PII 遮罩, Prompt Injection 檢測
│       │   ├── output_guard.py    # JSON Schema 驗證, 證據引用檢查
│       │   └── safety_rules.py    # [補充模組 1] 禁忌症規則引擎 (Regex/Logic)
│       │
│       ├── services/          # [Services & Supplementary Modules]
│       │   ├── patient_manager.py # ID 雜湊生成, 歷史回溯檢索
│       │   ├── visualization.py   # [補充模組 2] 圖表數據 Adapter (Sanitization)
│       │   ├── report_gen.py      # [補充模組 3] 結構化報告生成 (Jinja2)
│       │   └── nvidia_client.py   # Embedding API 封裝 (序列化控制)
│       │
│       ├── evaluation/        # [Evaluation & Monitoring]
│       │   ├── monitor.py         # 線上監控 Sidecar (Threading/BackgroundTasks)
│       │   └── metrics_utils.py   # [10大指標] 共用數學算式庫
│       │
│       └── api/               # [API Layer]
│           ├── endpoints.py       # 定義 /chat, /feedback, /patient 接口
│           └── schemas.py         # [Data Contract] WorkflowState, API Pydantic Models
│
├── frontend/                  # [Frontend] Vue 3 + TypeScript
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── .env                   # 前端環境變數
│   │
│   └── src/
│       ├── main.ts
│       ├── App.vue
│       ├── api/               # [API Client]
│       │   ├── axiosClient.ts     # Axios 實例 (攔截器: Timeout 60s, Retry 1)
│       │   └── scbrService.ts     # API 呼叫封裝
│       │
│       ├── components/        # [UI Components]
│       │   ├── layout/
│       │   │   ├── GlobalDisclaimer.vue # [LLM09] 全域免責聲明 (Footer)
│       │   │   └── SafetyBanner.vue     # 安全警示橫幅
│       │   │
│       │   ├── reception/         # [Module 1]
│       │   │   ├── PatientSearch.vue    # 身分證 -> Hash ID 映射介面
│       │   │
│       │   ├── chat/              # [Module 2]
│       │   │   ├── ChatContainer.vue    # 對話流
│       │   │   ├── ChatBubble.vue       # 氣泡樣式
│       │   │   └── InputArea.vue        # [LLM10] 輸入框限制 (1000 char)
│       │   │
│       │   ├── dashboard/         # [Module 3]
│       │   │   ├── DiagnosisCard.vue    # 核心卡片 (確診/保底模式切換)
│       │   │   ├── RadarChart.vue       # 八綱雷達圖 (ECharts)
│       │   │   └── EvidencePanel.vue    # 證據追溯面板
│       │   │
│       │   └── interaction/       # [Module 4]
│       │   │   ├── InquiryForm.vue      # 主動追問選項 (Chips)
│       │   │   └── FeedbackActions.vue  # 學習閉環按鈕 (Accept/Modify/Reject)
│       │
│       ├── stores/            # [State Management - Pinia]
│       │   ├── patientStore.ts    # 管理 CurrentPatient (RealName, HashUUID)
│       │   └── chatStore.ts       # 管理 SessionHistory, DiagnosisState
│       │
│       ├── types/             # [TypeScript Definitions]
│       │   └── apiTypes.ts    # 對齊後端 Pydantic Schemas
│       │
│       └── utils/             # [Utils]
│           └── formatters.ts
│
└── tests/                     # [Tests]
    ├── test_dataset.json      # 測試集 (含 Ground Truth)
    └── run_benchmark.py       # 離線評估腳本 (呼叫 core & evaluation)


3. 後端詳細規格 (Backend Specification)

3.1 資料接力協議 (Data Relay Protocol)

為了防止 Agent 資訊傳遞失真，必須使用強型別 WorkflowState 物件流轉。

class WorkflowState(BaseModel):
    session_id: str
    patient_id: str             # Hash 後的 ID
    user_input_raw: str         # 原始輸入
    standardized_features: dict # Translator 產出 (JSON)
    path_selected: str          # "PATH_A" or "PATH_B"
    retrieved_context: list     # 檢索到的案例或規則內容
    diagnosis_candidates: list  # 推理結果列表
    follow_up_question: dict    # 反問內容
    final_response: dict        # 最終輸出給前端的 JSON


3.2 資料庫 Schema (Weaviate - BYOV Mode)

所有 Class 設定 vectorizer: none，由 Python 調用 NVIDIA API 寫入。

TCM_Reference_Case (Class 1)

用途: Path A 檢索。包含專家 (SEEDED) 與學習 (LEARNED) 案例。

Properties: case_id, source_type ("SEEDED"|"LEARNED"), chief_complaint, diagnosis_main, treatment_principle, symptom_tags, confidence_score.

Embedding Input: chief_complaint + " " + symptom_tags.

TCM_Standard_Ontology (Class 2)

用途: Path B 語意標準化。

Properties: term_name, category, definition.

Embedding Input: term_name + "：" + definition.

TCM_Session_Memory (Class 3)

用途: 螺旋上下文追溯，LLM10 防禦。

Properties: patient_id (String Hash), session_id, turn_index, content, diagnosis_summary.

Embedding Input: content + " " + diagnosis_summary.

TCM_Diagnostic_Rules (Class 4)

用途: Path B 規則檢索，解決幻覺。

Properties: syndrome_name, category ("ZangFu"|"Exogenous"|"QiBlood"), main_symptoms, secondary_symptoms, tongue_pulse, exclusion.

Embedding Input: main_symptoms + " " + syndrome_name.

3.3 雙軌推演核心邏輯 (Dual-Path Logic)

閘門分流 (Gating): 計算 Cosine Similarity(Input, Reference_Cases)。

Score >= 0.8 $\rightarrow$ Path A.

Score < 0.8 $\rightarrow$ Path B.

Path A: Memory Agent (經驗聯想)

Retrieve: 檢索 Top-1 案例。

Align: 呼叫 Translator Agent 將新舊案例特徵標準化。

Revise (Gap Analysis):

針對 $S_{new}$ (新增症狀): 分析病機，在原治則中增加對應策略。

針對 $S_{missing}$ (缺失症狀): 從原治則中移除相關策略。

Evidence: 輸出必須包含 Reference Case ID 與 Similarity Score。

Path B: Reasoning Agent (三層 Pipeline)

Layer 1 Parser (解析):

呼叫 Translator Agent 產出標準 JSON。

四診檢查: 若舌/脈缺失，標記 MISSING_INFO。

Layer 2 Triage (分流):

檢測外感特徵 (惡寒/發熱/起病急)。

決定檢索 Diagnostic_Rules 的 Exogenous 類別或 ZangFu 類別。

Layer 3 Inference (推理):

規則匹配: 比對病人症狀與檢索到的規則。

氣血整合: 強制融合氣血津液狀態。

Fallback (保底): 若信心不足，生成 Top-3 鑑別列表 + 反問 (Inquiry)。

Evidence: 輸出必須標註引用的辨證模型與規則名稱。

3.4 螺旋上下文與 LLM10 防禦

Sequencing: Summarizer Agent 必須在 HTTP Response 回傳之後執行 (Background Task)。

Logic:

每一回合結束，提取確診事實更新 Current State JSON。

若 Raw History Token 數過高，壓縮早期回合為摘要。

4. 補充功能模組規格 (Supplementary Modules)

4.1 補充模組 1：禁忌症與安全規則引擎 (Safety Rule Engine)

位置: backend/app/guardrails/safety_rules.py

機制: Python 後處理腳本 (Regex/Logic)，不依賴 LLM。

邏輯: 針對孕婦、老幼等特殊族群，檢查治則是否含禁忌關鍵字 (如攻下、峻汗)。

輸出: 觸發時在 JSON 附加 safety_warning。

4.2 補充模組 2：可解釋性視覺化轉接器 (Visualization Adapter)

位置: backend/app/services/visualization.py

機制: 負責清洗 LLM 輸出的數據，轉換為 ECharts 格式。

防呆 (Sanitization): 解析 LLM 輸出的八綱分數。若格式錯誤、欄位缺失或為空，回傳空物件以隱藏圖表，確保不崩潰。

4.3 補充模組 3：結構化報告生成器 (Structured Report Generator)

位置: backend/app/services/report_gen.py

機制: 使用 Jinja2 模板，將 JSON 數據轉換為標準病歷格式 (HTML/Markdown)。

功能: 處理證據引用的超連結化、治則高亮顯示。

5. 安全架構 (Security - OWASP Top 10 2025)

5.1 輸入端防護

LLM10 (資源耗盡): 前端強制限制單次輸入 1000 字。

LLM01 (Prompt Injection): 後端 XML 標籤隔離 <user_input>，前置正則掃描攻擊關鍵字。

LLM02 (PII 洩漏): 正則替換姓名、身分證為 <PATIENT_NAME>。

5.2 輸出端防護

LLM05 (輸出處理): JSON Schema 嚴格驗證，失敗自動重試。

LLM09 (錯誤資訊):

前端: Footer 固定顯示全域免責聲明。

後端: 強制檢查 evidence_trace 欄位，未填寫則攔截。

6. 評估與監控詳細規格 (Evaluation & Metrics)

6.1 架構設計

模式: 非同步旁路監聽 (Asynchronous Sidecar)。使用 Threading 寫入 Log。

共用算式庫: backend/app/evaluation/metrics_utils.py。

6.2 十大評估指標 (Top 10 Metrics)

類別

指標名稱

定義簡述

計算時機

A. 準確度

1. Top-k Semantic Accuracy

預測向量與 GT 向量相似度 > 0.9

醫師確診後

(需 GT)

2. Semantic Recall

GT 是否在候選名單中 (含保底)

醫師確診後



3. Semantic Precision

建議項目的相關性密度

醫師確診後



4. F1-Score (Weighted)

偏重 Recall 的 F2 Score

醫師確診後



5. Confusion Matrix

錯誤型態統計 (如寒熱誤判)

醫師確診後



6. Round-wise Hit Rate

螺旋過程中的命中率曲線

醫師確診後

B. 效率

7. Avg. Convergence Turns

達成高信心的平均輪數

每回合

(無 GT)

8. Info Gain (Entropy)

該回合減少的不確定性量 ($H_{t-1} - H_t$)

每回合

C. 軌跡

9. V-SCR (覆蓋率)

Path A 檢索案例向量與病人主訴向量重疊度

醫師確診後

(需 GT)

10. DTS (軌跡相似度)

推理向量逼近 GT 的路徑線性度

醫師確診後

7. 前端詳細規格 (Frontend Specification)

7.1 統一輸出資料結構 (Unified JSON)

後端回傳格式：

{
  "response_type": "DEFINITIVE" | "FALLBACK" | "INQUIRY_ONLY",
  "diagnosis_list": [
    { "rank": 1, "disease_name": "...", "confidence": 0.95, "condition": null },
    { "rank": 2, "disease_name": "...", "confidence": 0.45, "condition": "若伴隨..." }
  ],
  "follow_up_question": { "required": true, "question_text": "...", "options": [...] },
  "evidence_trace": "...",
  "safety_warning": "...",
  "visualization_data": { ... },
  "formatted_report": "..."
}


7.2 儀表板渲染邏輯

確診模式 (Length=1): 顯示單一綠色大卡片。

保底模式 (Length>1): 顯示多張黃色卡片，必顯示 condition。

視覺化: 若有數據則渲染雷達圖，否則隱藏。

安全警示: 若有 safety_warning 則顯示紅色橫幅。

7.3 互動與學習閉環

反問: 顯示 follow_up_question 與選項 Chips。

學習閉環:

[採納]: 送出 ACCEPT $\rightarrow$ 後端寫入 Weaviate (High Conf).

[修改]: 送出 MODIFY $\rightarrow$ 後端寫入 Weaviate (Med Conf).

[拒絕]: 送出 REJECT $\rightarrow$ 後端不寫入。

8. 資料同步策略 (Startup Sync)

8.1 啟動同步邏輯 (sync_manager.py)

讀取 data/*.json 取得所有 IDs。

讀取 Weaviate 取得現有 IDs。

計算 Set Difference (JSON - DB)。

僅針對 新增 資料呼叫 NVIDIA API 並寫入 Weaviate，確保等冪性。

9. 環境變數模板 (.env)

# System Configuration
ENV_MODE=development
ENABLE_EVALUATION=True
LOG_LEVEL=INFO
MAX_INPUT_LENGTH=1000

# Security
PATIENT_ID_SALT=changeme_random_salt_string

# Models (NVIDIA NIM)
NVIDIA_API_KEY=nvapi-xxxx
# Model Names (Fixed in Code, override here if needed)
LLM_MODEL_NAME=nvidia/llama-3.3-nemotron-super-49b-v1.5
EMBEDDING_MODEL_NAME=nvidia/nv-embedqa-e5-v5
LLM_API_URL=[https://integrate.api.nvidia.com/v1](https://integrate.api.nvidia.com/v1)

# Database Configuration
WEAVIATE_URL=http://localhost:
