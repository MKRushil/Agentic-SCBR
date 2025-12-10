import logging
from app.agents.base import BaseAgent
from app.core.orchestrator import WorkflowState
from app.prompts.base import SYSTEM_PROMPT_CORE, XML_OUTPUT_INSTRUCTION
from app.prompts.summarizer import SUMMARIZER_SYSTEM_PROMPT, build_summarizer_prompt

logger = logging.getLogger(__name__)

class SummarizerAgent(BaseAgent):
    """
    規格書 3.4: 螺旋上下文與 LLM10 防禦
    執行時機: HTTP Response 回傳後 (Background Task)
    功能: 壓縮對話歷史，提取結構化事實。
    """
    
    async def run(self, state: WorkflowState) -> WorkflowState:
        logger.info(f"[Summarizer] Starting background summarization for Session: {state.session_id}")
        
        try:
            # 組合 Prompt (這裡假設 state 有 accumulative_context 或類似欄位，或是從 DB 撈取)
            # 簡化示範：直接拿 user_input 當作本回合對話
            prompt = build_summarizer_prompt(
                history_content=f"User: {state.user_input_raw}\nSystem: {state.final_response.formatted_report if state.final_response else ''}",
                current_summary=state.diagnosis_summary or ""
            )

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT_CORE + "\n" + SUMMARIZER_SYSTEM_PROMPT + "\n" + XML_OUTPUT_INSTRUCTION},
                {"role": "user", "content": prompt}
            ]

            # 呼叫 LLM (注意: 這是背景執行，不阻塞主流程)
            response_text = await self.client.generate_completion(messages, temperature=0.1)
            
            # 解析結果
            result = self.parse_xml_json(response_text)
            
            # 更新狀態 (這些變更應該寫入資料庫，這裡更新 State 物件)
            state.diagnosis_summary = result.get("updated_diagnosis_summary", "")
            
            logger.info(f"[Summarizer] Summary updated. Key findings: {result.get('key_findings', [])}")
            
            # TODO: 呼叫 PatientManager 或 WeaviateClient 將更新後的摘要寫回 DB (TCM_Session_Memory)
            
            return state

        except Exception as e:
            logger.error(f"[Summarizer] Failed to summarize: {str(e)}")
            # 背景任務失敗不影響主回應，僅記錄錯誤
            return state