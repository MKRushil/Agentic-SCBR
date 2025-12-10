from app.agents.base import BaseAgent
from app.core.orchestrator import WorkflowState
from app.prompts.base import SYSTEM_PROMPT_CORE, XML_OUTPUT_INSTRUCTION
from app.prompts.memory import MEMORY_SYSTEM_PROMPT
from app.api.schemas import ChatResponse, DiagnosisCandidate, FollowUpQuestion

class MemoryAgent(BaseAgent):
    """
    規格書 3.3 Path A Logic
    Retrieve -> Align -> Revise
    """
    async def run(self, state: WorkflowState) -> WorkflowState:
        # 1. Retrieve (Mock)
        # reference_case = weaviate_client.get_similar_case(...)
        reference_case = {"case_id": "CASE_001", "diagnosis": "感冒", "symptoms": ["發燒"]} # Mock
        
        # 2. Revise (LLM)
        prompt = f"""
        當前病患: {state.standardized_features}
        參考案例: {reference_case}
        請進行差異分析與策略調整。
        """
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_CORE + "\n" + MEMORY_SYSTEM_PROMPT + "\n" + XML_OUTPUT_INSTRUCTION},
            {"role": "user", "content": prompt}
        ]
        
        response_text = await self.client.generate_completion(messages, temperature=0.2)
        
        try:
            result_json = self.parse_xml_json(response_text)
            
            # 構建回應
            diag = DiagnosisCandidate(
                rank=1, 
                disease_name=result_json.get("adjusted_diagnosis", "未知"), 
                confidence=result_json.get("similarity", 0.8)
            )
            
            state.diagnosis_candidates = [diag]
            state.final_response = ChatResponse(
                response_type="DEFINITIVE",
                diagnosis_list=[diag],
                follow_up_question=FollowUpQuestion(required=False),
                evidence_trace=f"基於參考案例 {result_json.get('base_case_id')} 進行調整",
                formatted_report=result_json.get("final_treatment", "")
            )
            
        except Exception:
            state.final_response = ChatResponse(
                response_type="INQUIRY_ONLY",
                diagnosis_list=[],
                follow_up_question=FollowUpQuestion(required=True, question_text="無法匹配案例，請詳細描述。"),
                evidence_trace="Error in Memory Agent"
            )
            
        return state