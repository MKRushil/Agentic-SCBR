"""基礎Agent類 - 整合 NVIDIA LLM"""
from typing import Dict, Any, Optional
import yaml
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from config.settings import settings
from utils.logger import logger
from knowledge.llm_service import llm_service

class BaseAgent:
    """Agent基礎類 - 使用 NVIDIA LLM API"""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.llm = llm_service
        self.prompts = self._load_prompts()
        self.system_prompt = self.prompts.get(agent_name, {}).get('system', '')
        self.user_template = self.prompts.get(agent_name, {}).get('user_template', '')
        logger.info(f"初始化 {agent_name} Agent (NVIDIA LLM)")

    def _load_prompts(self) -> Dict[str, Any]:
        prompt_file = Path(__file__).parent.parent / 'config' / 'prompts.yaml'
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"載入提示詞失敗: {e}")
            return {}

    def _call_llm(self, messages: list, temperature: Optional[float] = None) -> str:
        logger.info(f"[{self.agent_name}] 正在調用 LLM...")
        try:
            return self.llm.chat(messages=messages, temperature=temperature)
        except Exception as e:
            logger.error(f"[{self.agent_name}] LLM 調用失敗: {e}")
            return f"[錯誤: {str(e)}]"

    def process(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError("子類必須實現 process 方法")

    def format_user_prompt(self, **kwargs) -> str:
        try:
            return self.user_template.format(**kwargs)
        except KeyError as e:
            logger.warning(f"提示詞模板缺少參數: {e}")
            return self.user_template
