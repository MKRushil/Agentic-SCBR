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
            # 組合 Prompt
            # user_input_raw 已經包含了本回合的完整對話歷史 (由 Orchestrator 拼接)
            # 但理想情況下，我們應該只傳入「新增的對話」+「舊摘要」
            # 不過為了簡化，我們讓 LLM 重新摘要這段對話也無妨，或是假設 state.user_input_raw 是完整的 history
            
            prompt = build_summarizer_prompt(
                history_content=state.user_input_raw,
                current_summary=state.diagnosis_summary or "尚無摘要"
            )

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT_CORE + "\n" + SUMMARIZER_SYSTEM_PROMPT + "\n" + XML_OUTPUT_INSTRUCTION},
                {"role": "user", "content": prompt}
            ]

            # 呼叫 LLM
            response_text = await self.client.generate_completion(messages, temperature=0.1)
            
            # 解析結果
            result = self.parse_xml_json(response_text)
            
            # 更新狀態
            new_summary = result.get("updated_diagnosis_summary", "")
            state.diagnosis_summary = new_summary
            
            logger.info(f"[Summarizer] Summary updated: {new_summary[:50]}...")
            
            return state

        except Exception as e:
            logger.error(f"[Summarizer] Failed to summarize: {str(e)}")
            return state