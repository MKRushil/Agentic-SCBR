# backend/app/core/orchestrator.py

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from uuid import uuid4
from datetime import datetime

from app.core.config import settings
from app.api.schemas import WorkflowState, PathSelected, UnifiedResponse, ResponseType
from app.services.nvidia_client import NvidiaClient
from app.database.weaviate_client import WeaviateClient
from app.api.schemas import DiagnosisItem, FollowUpQuestion
from app.agents.reasoning import ReasoningAgent
from app.agents.summarizer import SummarizerAgent
from app.agents.memory import MemoryAgent
from app.agents.translator import TranslatorAgent
from app.services.visualization import VisualizationAdapter
from app.evaluation.monitor import monitor
from app.guardrails.input_guard import InputGuard
from app.guardrails.output_guard import OutputGuard

logger = logging.getLogger(__name__)

class Orchestrator:
    """
    核心調度器 (System Brain)
    規格書 1.2: 必須實作 全域互斥鎖 (Global Mutex Lock) 以確保單執行緒序列化。
    """
    
    def __init__(self):
        # Global Mutex Lock Required by Spec 1.2
        self._global_lock = asyncio.Lock()
        self.nvidia_client = NvidiaClient()
        self.weaviate_client = WeaviateClient()
        self.reasoning_agent = ReasoningAgent(self.nvidia_client, self.weaviate_client)
        self.memory_agent = MemoryAgent(self.nvidia_client)
        self.summarizer_agent = SummarizerAgent(self.nvidia_client)
        self.translator_agent = TranslatorAgent(self.nvidia_client)
        
        # In-memory 短期記憶 (當前 Session)
        # Structure: {session_id: {"messages": [{"role": "user", "content": "..."}, ...], "summary": "...", "previous_diagnosis_candidates": []}}
        self._session_histories: Dict[str, Dict[str, Any]] = {}

    async def process_session(self, request: Any, background_tasks: Any = None) -> UnifiedResponse:
        """
        執行管線 (Serial Pipeline):
        Input Guard -> Embedding -> Vector Search -> Path Selection -> Agent -> Output -> Async Summarization
        """
        session_id = request.session_id
        patient_id = request.patient_id
        
        # [Security] Input Guard
        try:
            user_input_current_turn = InputGuard.validate(request.message)
        except ValueError as ve:
            logger.warning(f"[Orchestrator] Input guard blocked request: {ve}")
            raise ve

        # 獲取或初始化當前 Session 的歷史
        session_data = self._session_histories.setdefault(session_id, {"messages": [], "summary": {}, "previous_diagnosis_candidates": []})
        session_history = session_data["messages"]
        current_summary = session_data["summary"] # current_summary 應該是 Dict
        previous_diagnosis_candidates = session_data["previous_diagnosis_candidates"] # 上一輪的診斷候選
        
        # 將當前使用者輸入加入歷史
        session_history.append({"role": "user", "content": user_input_current_turn})

        # 1. 構建 Embedding Query (優化策略：摘要 + 當前輸入)
        # 這樣能聚焦核心病況，同時包含最新細節
        embedding_input = current_summary.get("updated_diagnosis_summary", "") + " " + user_input_current_turn
        embedding_input = embedding_input.strip()
        
        # 2. 構建 LLM Context (完整歷史，供推理用)
        full_conversation_context = " ".join([msg["content"] for msg in session_history])

        # 初始化 Workflow State
        state = WorkflowState(
            session_id=session_id,
            patient_id=patient_id,
            user_input_raw=full_conversation_context, # 供 Reasoning Agent 用
            diagnosis_summary=current_summary,
            previous_diagnosis_candidates=previous_diagnosis_candidates # 傳入上一輪診斷
        )

        # 1. Acquire Global Lock (Strictly Serial Execution)
        async with self._global_lock:
            logger.info(f"Lock acquired for session {session_id}")
            
            try:
                # --- Step 0: Translation (Standardization) ---
                # 在 Embedding 之前先進行標準化，這有助於理解特徵
                state = await self.translator_agent.run(state)
                logger.info(f"[Orchestrator] Translation complete. Missing info: {state.standardized_features.get('missing_fields')}")

                # [Safety Check] 急症攔截 (Red Flag)
                if state.standardized_features.get("is_emergency"):
                    warning_msg = state.standardized_features.get("emergency_warning", "偵測到危急重症徵兆，請立即就醫！")
                    logger.warning(f"[Orchestrator] Emergency detected: {warning_msg}")
                    return UnifiedResponse(
                        response_type=ResponseType.INQUIRY_ONLY,
                        diagnosis_list=[],
                        evidence_trace="系統攔截：偵測到危急重症關鍵字。",
                        safety_warning=warning_msg,
                        formatted_report=f"### ⚠️ 緊急警示\n\n系統偵測到危急徵兆：**{warning_msg}**\n\n本系統僅供慢性病輔助參考，無法處理急症。請立即前往急診就醫。"
                    )

                # --- Step 2: Embedding & Gating (Path Selection) ---
                # 使用優化後的 embedding_input
                query_vector = await self.nvidia_client.get_embedding(embedding_input)
                
                # Search for similar cases (Top 3 for potential fallback)
                similar_cases = self.weaviate_client.search_similar_cases(query_vector, limit=3)
                
                max_similarity = 0.0
                best_case = None
                
                if similar_cases:
                    best_case = similar_cases[0]
                    max_similarity = best_case.get('similarity', 0.0)
                    state.retrieved_context = similar_cases 

                logger.info(f"[Orchestrator] Max similarity: {max_similarity} (Query: {embedding_input[:50]}...)")

                # Generate Visualization Data (Radar Chart)
                # 使用 Translator 產出的八綱分數
                viz_data = VisualizationAdapter.process(state)

                # Path Selection Logic
                # Default to Path B if Path A fails or similarity is low
                execute_path_b = True 
                
                if max_similarity >= 0.8:
                    state.path_selected = PathSelected.PATH_A
                    logger.info(f"Path A Selected (Similarity: {max_similarity:.4f})")
                    
                    # --- Path A: Memory Agent (Gap Analysis & Revision) ---
                    state = await self.memory_agent.run(state)
                    
                    # [Fallback Check] 檢查 Path A 是否拒絕了案例
                    # 檢查方式：看 diagnosis_list 是否為空，或病名是否為 CASE_REJECTED
                    path_a_rejected = False
                    if state.final_response and state.final_response.diagnosis_list:
                        first_diag = state.final_response.diagnosis_list[0].disease_name
                        if first_diag == "CASE_REJECTED":
                            path_a_rejected = True
                    
                    if not path_a_rejected:
                        execute_path_b = False # Path A 成功，不需要跑 Path B
                        # Inject Visualization Data
                        if state.final_response:
                            state.final_response.visualization_data = viz_data
                    else:
                        logger.warning(f"[Orchestrator] Path A rejected the case (Procrustean Gap). Falling back to Path B.")
                        state.path_selected = PathSelected.PATH_B # Update path record

                if execute_path_b:
                    if state.path_selected != PathSelected.PATH_A: # Avoid double logging if fallback
                        state.path_selected = PathSelected.PATH_B
                        logger.info(f"Path B Selected. Max sim: {max_similarity}")
                    
                    # --- Path B: Reasoning Agent (Real Implementation) ---
                    state = await self.reasoning_agent.run(state)
                    
                    if similar_cases and state.final_response:
                        ref_info = f"\n\n[參考案例補充] 雖然相似度不足以直接引用，但發現最接近的案例為: {similar_cases[0].get('diagnosis_main')} (相似度 {max_similarity:.2f})"
                        state.final_response.evidence_trace += ref_info
                    
                    # Inject Visualization Data into Response
                    if state.final_response:
                        state.final_response.visualization_data = viz_data
                
                logger.info(f"Pipeline finished for session {session_id}. Path: {state.path_selected}")
                
                # Update History with Assistant Response
                assistant_response_content = "..."
                if state.final_response and state.final_response.follow_up_question and state.final_response.follow_up_question.question_text:
                    assistant_response_content = state.final_response.follow_up_question.question_text
                elif state.final_response and state.final_response.diagnosis_list:
                    assistant_response_content = f"主要考慮為：{state.final_response.diagnosis_list[0].disease_name}"
                
                session_history.append({"role": "assistant", "content": assistant_response_content})

                # Trigger Background Task (Summarization)
                if background_tasks:
                     background_tasks.add_task(self.trigger_async_summarization, state)

                # --- 規格書 6.3 Online Monitoring ---
                monitor.log_detailed_metrics(state)
                
                # [Security] Output Guard
                if state.final_response:
                    state.final_response = OutputGuard.validate_response(state.final_response)
                
                # [Diagnostic Funnel] 保存本次診斷結果，供下一輪使用
                if state.final_response and state.final_response.diagnosis_list:
                    self._session_histories[session_id]["previous_diagnosis_candidates"] = state.final_response.diagnosis_list

                return state.final_response

            except Exception as e:
                logger.error(f"Error in pipeline: {e}")
                if session_id in self._session_histories:
                    del self._session_histories[session_id]
                raise e

    async def trigger_async_summarization(self, state: WorkflowState):
        """
        規格書 3.4: Summarizer Agent 必須在 HTTP Response 回傳之後執行 (Background Task)
        """
        try:
            # 呼叫 Summarizer Agent
            new_state = await self.summarizer_agent.run(state)
            
            # 將新摘要存回 In-Memory History
            if state.session_id in self._session_histories:
                # new_state.diagnosis_summary 已經是 Dict，無需 json.loads
                self._session_histories[state.session_id]["summary"] = new_state.diagnosis_summary
                logger.info(f"[Summarizer] Updated In-Memory Summary for {state.session_id}")
                
        except Exception as e:
            logger.error(f"[Orchestrator] Background summarization failed: {str(e)}")

    async def process_feedback(self, request: Any):
        """
        規格書 7.3: 學習閉環 (Learning Loop)
        """
        session_id = request.session_id
        action = request.action
        
        logger.info(f"[Feedback] Processing {action} for session {session_id}")
        
        # 1. 獲取 Session Context
        session_data = self._session_histories.get(session_id)
        if not session_data:
            logger.warning(f"[Feedback] Session history not found for {session_id}")
            return

        # 2. 準備數據
        # 從最後一次 Assistant Message 或 Summary 提取資訊
        # 理想情況下，我們應該緩存最後的 WorkflowState，但這裡我們用 Summary 和 History 重建
        summary_obj = session_data.get("summary", {})
        summary_text = summary_obj.get("updated_diagnosis_summary", "")

        # 構建 TCM_Reference_Case 數據
        case_data = {
            "case_id": f"CASE_LEARNED_{uuid4().hex[:8]}",
            "source_type": "LEARNED",
            "chief_complaint": summary_text, # 使用摘要作為主訴/病史
            "symptom_tags": summary_obj.get("key_findings", []), # 從結構化摘要中提取
            "diagnosis_main": "User Feedback", # 需從 request 或 history 提取
            "treatment_principle": "User Feedback",
            "pathology_analysis": "Generated from Learning Loop",
            "confidence_score": 1.0 if action == "ACCEPT" else 0.8 # ACCEPT=High, MODIFY=Med
        }

        # 如果是 MODIFY，覆蓋內容
        if action == "MODIFY" and request.modified_content:
            case_data["diagnosis_main"] = "Modified Diagnosis" # 這裡應該解析 user input
            case_data["treatment_principle"] = request.modified_content
            case_data["pathology_analysis"] += f" (Modified: {request.modified_content})"

        # 3. 寫入 Weaviate
        if action in ["ACCEPT", "MODIFY"]:
            try:
                # Embedding
                text_to_embed = f"{case_data['chief_complaint']} {case_data['diagnosis_main']} {case_data['treatment_principle']}"
                vector = await self.nvidia_client.get_embedding(text_to_embed)
                
                # Insert Case
                self.weaviate_client.insert_case(case_data, vector)
                logger.info(f"[Learning] Case learned: {case_data['case_id']}")
                
                # Insert Session Memory (完整對話)
                memory_data = {
                    "session_id": session_id,
                    "patient_id": request.patient_id,
                    "content": str(session_data["messages"]), # 轉字串存
                    "diagnosis_summary": summary_text, # 存入文字摘要
                    "timestamp": datetime.now().isoformat()
                }
                self.weaviate_client.add_session_memory(memory_data)
                
            except Exception as e:
                logger.error(f"[Learning] Failed to store case: {str(e)}")
                raise e

# Singleton Instance
orchestrator = Orchestrator()
