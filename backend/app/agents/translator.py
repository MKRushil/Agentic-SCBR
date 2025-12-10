from app.agents.base import BaseAgent
from app.core.orchestrator import WorkflowState
from app.prompts.base import SYSTEM_PROMPT_CORE, XML_OUTPUT_INSTRUCTION
from app.prompts.translator import TRANSLATOR_SYSTEM_PROMPT, build_translation_prompt

class TranslatorAgent(BaseAgent):
    """
    規格書 3.3 LLM Translation
    負責將 Raw Input 轉為 Standardized Features。
    """
    async def run(self, state: WorkflowState) -> WorkflowState:
        prompt = build_translation_prompt(state.user_input_raw)
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_CORE + "\n" + TRANSLATOR_SYSTEM_PROMPT + "\n" + XML_OUTPUT_INSTRUCTION},
            {"role": "user", "content": prompt}
        ]
        
        response_text = await self.client.generate_completion(messages, temperature=0.1)
        
        try:
            parsed_data = self.parse_xml_json(response_text)
            state.standardized_features = parsed_data
        except Exception as e:
            # 簡單 Fallback: 將原始輸入當作主訴
            state.standardized_features = {
                "chief_complaint": state.user_input_raw,
                "symptoms": [],
                "is_missing_info": True
            }
            
        return state