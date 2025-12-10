from abc import ABC, abstractmethod
from typing import Any, Dict
from app.services.nvidia_client import NvidiaClient
from app.core.orchestrator import WorkflowState

class BaseAgent(ABC):
    """
    規格書 2.0: Agent 基礎介面
    所有 Agent 必須繼承此類別並實作 run 方法。
    """
    def __init__(self, nvidia_client: NvidiaClient):
        self.client = nvidia_client

    @abstractmethod
    async def run(self, state: WorkflowState) -> WorkflowState:
        """
        接收當前 WorkflowState，執行邏輯後回傳更新後的 State。
        """
        pass
    
    def parse_xml_json(self, llm_output: str) -> Dict[str, Any]:
        """
        輔助函式：從 LLM 輸出中提取 <json> 區塊並解析。
        若解析失敗，應由具體 Agent 處理 Retry 或 Fallback。
        """
        import re
        import json
        
        match = re.search(r'<json>(.*?)</json>', llm_output, re.DOTALL)
        if match:
            json_str = match.group(1).strip()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                raise ValueError("LLM Output is not valid JSON")
        else:
            # 嘗試直接解析整個字串 (容錯)
            try:
                return json.loads(llm_output)
            except:
                raise ValueError("No JSON block found in LLM output")