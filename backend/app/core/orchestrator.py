# backend/app/core/orchestrator.py

import asyncio
import logging
from typing import Dict, Any, List
from uuid import uuid4

from app.core.config import settings
from app.api.schemas import WorkflowState, PathSelected, UnifiedResponse, ResponseType
from app.services.nvidia_client import NvidiaClient
from app.database.weaviate_client import WeaviateClient
from app.api.schemas import DiagnosisItem, FollowUpQuestion
from app.agents.reasoning import ReasoningAgent

logger = logging.getLogger(__name__)

class Orchestrator:
    """
    核心調度器 (System Brain)
    規格書 1.2: 必須實作 全域互斥鎖 (Global Mutex Lock) 以確保單執行緒序列化。
    """
from app.agents.summarizer import SummarizerAgent
from app.agents.memory import MemoryAgent
from app.agents.translator import TranslatorAgent
from app.services.visualization import VisualizationAdapter

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
        # Structure: {session_id: {"messages": [{"role": "user", "content": "..."}, ...], "summary": "..."}}
        self._session_histories: Dict[str, Dict[str, Any]] = {} 

    async def process_session(self, request: Any, background_tasks: Any = None) -> UnifiedResponse:
        """
        執行管線 (Serial Pipeline):
        Input Guard -> Embedding -> Vector Search -> Path Selection -> Agent -> Output -> Async Summarization
        """
        session_id = request.session_id
        patient_id = request.patient_id
        user_input_current_turn = request.message

        # 獲取或初始化當前 Session 的歷史
        session_data = self._session_histories.setdefault(session_id, {"messages": [], "summary": ""})
        session_history = session_data["messages"]
        current_summary = session_data["summary"]
        
        # 將當前使用者輸入加入歷史
        session_history.append({"role": "user", "content": user_input_current_turn})

        # 1. 構建 Embedding Query (優化策略：摘要 + 當前輸入)
        # 這樣能聚焦核心病況，同時包含最新細節
        embedding_input = f"{current_summary} {user_input_current_turn}".strip()
        
        # 2. 構建 LLM Context (完整歷史，供推理用)
        full_conversation_context = " ".join([msg["content"] for msg in session_history])

        # 初始化 Workflow State
        state = WorkflowState(
            session_id=session_id,
            patient_id=patient_id,
            user_input_raw=full_conversation_context, # 供 Reasoning Agent 用
            diagnosis_summary=current_summary
        )

        # 1. Acquire Global Lock (Strictly Serial Execution)
        async with self._global_lock:
            logger.info(f"Lock acquired for session {session_id}")
            
            try:
                # --- Step 0: Translation (Standardization) ---
                # 在 Embedding 之前先進行標準化，這有助於理解特徵
                # 雖然 Embedding 我們仍用 embedding_input，但 Translator 的產出 (standardized_features) 
                # 會被 Reasoning Agent 和 Visualization 使用
                state = await self.translator_agent.run(state)
                logger.info(f"[Orchestrator] Translation complete. Missing info: {state.standardized_features.get('missing_fields')}")

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
                if max_similarity >= 0.8:
                    state.path_selected = PathSelected.PATH_A
                    logger.info(f"Path A Selected (Similarity: {max_similarity:.4f})")
                    
                    # --- Path A: Memory Agent (Gap Analysis & Revision) ---
                    # 不再直接引用，而是呼叫 MemoryAgent 進行差異分析
                    state = await self.memory_agent.run(state)
                    
                    # Inject Visualization Data into Response
                    if state.final_response:
                        state.final_response.visualization_data = viz_data

                else:
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
                self._session_histories[state.session_id]["summary"] = new_state.diagnosis_summary
                logger.info(f"[Summarizer] Updated In-Memory Summary for {state.session_id}")
                
        except Exception as e:
            logger.error(f"[Orchestrator] Background summarization failed: {str(e)}")

# Singleton Instance
orchestrator = Orchestrator()