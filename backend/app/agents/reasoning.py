import logging
import json # Import json for parsing summary
from app.agents.base import BaseAgent
from app.core.orchestrator import WorkflowState
from app.prompts.base import SYSTEM_PROMPT_CORE, XML_OUTPUT_INSTRUCTION
from app.prompts.reasoning import REASONING_SYSTEM_PROMPT, build_reasoning_prompt
from app.api.schemas import UnifiedResponse, DiagnosisItem, FollowUpQuestion, ResponseType
from app.database.weaviate_client import WeaviateClient

class ReasoningAgent(BaseAgent):
    """
    規格書 3.3 Path B Logic
    Layer 2: Triage (判斷外感/臟腑 - 這裡簡化處理，實際應查詢 DB)
    Layer 3: Inference (LLM 推理)
    """
    def __init__(self, nvidia_client, weaviate_client: WeaviateClient):
        super().__init__(nvidia_client)
        self.weaviate_client = weaviate_client

    async def run(self, state: WorkflowState) -> WorkflowState:
        # 1. 取得 Embedding (用於檢索規則) - 使用原始輸入，因為規則檢索是基於原始語意
        query_vector = await self.client.get_embedding(state.user_input_raw)
        
        # 2. 檢索診斷規則 (Retrieval)
        retrieved_rules = self.weaviate_client.search_diagnostic_rules(query_vector, limit=3)
        
        # 3. 準備更豐富的特徵給 Prompt
        features_for_prompt = {
            "user_input_raw": state.user_input_raw,
            "standardized_features": state.standardized_features, # Translator 的輸出
            "diagnosis_summary": state.diagnosis_summary # Summarizer 的結構化輸出
        }
        
        # 4. Layer 3 Inference
        # 傳遞 previous_diagnosis_candidates 給 Prompt，實現診斷漏斗邏輯
        prompt = build_reasoning_prompt(
            features_for_prompt, 
            retrieved_rules, 
            state.previous_diagnosis_candidates
        )
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_CORE + "\n" + REASONING_SYSTEM_PROMPT + "\n" + XML_OUTPUT_INSTRUCTION},
            {"role": "user", "content": prompt}
        ]
        
        response_text = await self.client.generate_completion(messages, temperature=0.1)
        
        try:
            result_json = self.parse_xml_json(response_text)
            
            # 轉換為 Pydantic Model
            diagnosis_list = [DiagnosisItem(**d) for d in result_json.get("diagnosis_list", [])]
            
            # Handle FollowUpQuestion safely
            follow_up_data = result_json.get("follow_up_question")
            follow_up = None
            if follow_up_data:
                # [Schema Fix] Map 'discriminating_question' to 'question_text' if needed
                if not follow_up_data.get("question_text") and follow_up_data.get("discriminating_question"):
                    follow_up_data["question_text"] = follow_up_data["discriminating_question"]
                
                try:
                    follow_up = FollowUpQuestion(**follow_up_data)
                except Exception as e:
                    # Log validation error but don't crash
                    import logging
                    logging.getLogger(__name__).warning(f"FollowUpQuestion validation failed: {e}. Using fallback.")
                    follow_up = FollowUpQuestion(required=False, question_text="請問還有其他症狀嗎？", options=[])

            # 5. 構建 UnifiedResponse
            response_type = result_json.get("response_type", ResponseType.FALLBACK)
            
            # 處理 formatted_report，特別是 FALLBACK 模式下的鑑別診斷
            formatted_report_content = result_json.get("formatted_report")
            if not formatted_report_content and response_type == ResponseType.FALLBACK and diagnosis_list:
                formatted_report_content = "## 鑑別診斷報告 (可能證型)\n"
                for diag in diagnosis_list:
                    formatted_report_content += f"- **{diag.disease_name}** (信心度: {diag.confidence:.1%})\n"
                    if diag.condition:
                        formatted_report_content += f"  - *判斷依據/待確認:* {diag.condition}\n"
                formatted_report_content += "\n---"

            response = UnifiedResponse(
                response_type=response_type,
                diagnosis_list=diagnosis_list,
                follow_up_question=follow_up,
                evidence_trace=result_json.get("evidence_trace", "無法取得推導過程"),
                safety_warning=None, # 稍後由 Safety Engine 填入
                visualization_data=None,
                formatted_report=formatted_report_content
            )
            state.diagnosis_candidates = diagnosis_list
            state.final_response = response
            state.retrieved_context = retrieved_rules # 存起來做證據
            
        except Exception as e:
            # Fallback for parsing error
            import logging
            logging.getLogger(__name__).error(f"Reasoning Agent Error: {e} \nRaw Output: {response_text}")
            
            state.final_response = UnifiedResponse(
                response_type=ResponseType.FALLBACK,
                diagnosis_list=[],
                follow_up_question=FollowUpQuestion(required=True, question_text="系統推導發生錯誤，請重新描述症狀。", options=[]),
                evidence_trace=f"System Error: {str(e)}",
                formatted_report="",
                safety_warning=None,
                visualization_data=None
            )
            
        return state