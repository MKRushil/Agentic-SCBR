# backend/app/api/schemas.py

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum

# --- Enums ---

class ResponseType(str, Enum):
    DEFINITIVE = "DEFINITIVE"
    FALLBACK = "FALLBACK"
    INQUIRY_ONLY = "INQUIRY_ONLY"

class PathSelected(str, Enum):
    PATH_A = "PATH_A"
    PATH_B = "PATH_B"

# --- Frontend Interaction Models (Section 7.1 & 7.3) ---

class DiagnosisItem(BaseModel):
    rank: int
    disease_name: str
    confidence: float
    condition: Optional[str] = None # 用於保底模式，例如 "若伴隨..."

class FollowUpQuestion(BaseModel):
    required: bool
    question_text: str
    options: List[str] = Field(default_factory=list)

class UnifiedResponse(BaseModel):
    """
    規格書 7.1 統一輸出資料結構
    """
    response_type: ResponseType
    diagnosis_list: List[DiagnosisItem]
    follow_up_question: Optional[FollowUpQuestion] = None
    evidence_trace: str # 必須包含引用來源
    safety_warning: Optional[str] = None
    visualization_data: Optional[Dict[str, Any]] = None # ECharts 數據
    formatted_report: Optional[str] = None # HTML/Markdown

class FeedbackAction(str, Enum):
    ACCEPT = "ACCEPT"
    MODIFY = "MODIFY"
    REJECT = "REJECT"

class FeedbackRequest(BaseModel):
    """
    規格書 7.3 學習閉環請求
    """
    session_id: str
    patient_id: str
    action: FeedbackAction
    modified_content: Optional[str] = None # 若 action 為 MODIFY 則必填

class ChatRequest(BaseModel):
    session_id: str
    patient_id: str # 前端傳來的 Hash ID
    message: str

# --- Internal Workflow State (Section 3.1) ---

class WorkflowState(BaseModel):
    """
    規格書 3.1 資料接力協議
    防止 Agent 資訊傳遞失真，必須使用強型別 WorkflowState 物件流轉。
    """
    session_id: str
    patient_id: str             # Hash 後的 ID
    user_input_raw: str         # 原始輸入
    standardized_features: Dict[str, Any] = Field(default_factory=dict) # Translator 產出 (JSON)
    path_selected: Optional[PathSelected] = None
    retrieved_context: List[Any] = Field(default_factory=list)     # 檢索到的案例或規則內容
    diagnosis_candidates: List[DiagnosisItem] = Field(default_factory=list)  # 推理結果列表
    diagnosis_summary: Optional[str] = None # Summarizer 產出的病況摘要
    follow_up_question: Optional[FollowUpQuestion] = None    # 反問內容
    final_response: Optional[UnifiedResponse] = None        # 最終輸出給前端的 JSON
    
    # 輔助欄位，用於 Trace
    step_logs: List[str] = Field(default_factory=list)