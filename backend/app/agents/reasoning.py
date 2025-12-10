from app.agents.base import BaseAgent
from app.core.orchestrator import WorkflowState
from app.prompts.base import SYSTEM_PROMPT_CORE, XML_OUTPUT_INSTRUCTION
from app.prompts.reasoning import REASONING_SYSTEM_PROMPT, build_reasoning_prompt
from app.api.schemas import ChatResponse, DiagnosisCandidate, FollowUpQuestion

class ReasoningAgent(BaseAgent):
    """
    規格書 3.3 Path B Logic
    Layer 2: Triage (判斷外感/臟腑 - 這裡簡化處理，實際應查詢 DB)
    Layer 3: Inference (LLM 推理)
    """
    async def run(self, state: WorkflowState) -> WorkflowState:
        # 1. 模擬 Layer 2 Triage & Retrieval (真實情況應呼叫 WeaviateClient)
        # retrieved_rules = weaviate_client.query_rules(...)
        retrieved_rules = [] # Mock
        
        # 2. Layer 3 Inference
        prompt = build_reasoning_prompt(state.standardized_features, retrieved_rules)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_CORE + "\n" + REASONING_SYSTEM_PROMPT + "\n" + XML_OUTPUT_INSTRUCTION},
            {"role": "user", "content": prompt}
        ]
        
        response_text = await self.client.generate_completion(messages, temperature=0.3)
        
        try:
            result_json = self.parse_xml_json(response_text)
            
            # 轉換為 Pydantic Model
            diagnosis_list = [DiagnosisCandidate(**d) for d in result_json.get("diagnosis_list", [])]
            follow_up = FollowUpQuestion(**result_json.get("follow_up_question", {"required": False}))
            
            response = ChatResponse(
                response_type=result_json.get("response_type", "FALLBACK"),
                diagnosis_list=diagnosis_list,
                follow_up_question=follow_up,
                evidence_trace=result_json.get("evidence_trace", "無法取得推導過程"),
                safety_warning=None, # 稍後由 Safety Engine 填入
                formatted_report=result_json.get("treatment_principle", "")
            )
            state.diagnosis_candidates = diagnosis_list
            state.final_response = response
            
        except Exception as e:
            # Fallback for parsing error
            state.final_response = ChatResponse(
                response_type="FALLBACK",
                diagnosis_list=[],
                follow_up_question=FollowUpQuestion(required=True, question_text="系統忙碌中，請重新描述症狀。"),
                evidence_trace="System Error"
            )
            
        return state