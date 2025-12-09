"""狀態管理器"""
from typing import Dict, Any, Optional
from utils.logger import logger

class StateManager:
    """診斷流程狀態管理器"""

    def __init__(self):
        self.state = {
            "current_stage": None,
            "intake_result": None,
            "pathogenesis_result": None,
            "retrieval_result": None,
            "diagnosis_result": None,
            "explanation_result": None,
            "conflicts": [],
            "revision_history": []
        }

    def set_stage(self, stage: str):
        self.state["current_stage"] = stage
        logger.info(f"進入階段: {stage}")

    def update(self, key: str, value: Any):
        self.state[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.state.get(key, default)

    def add_conflict(self, conflict: Dict[str, Any]):
        self.state["conflicts"].append(conflict)
        logger.warning(f"發現衝突: {conflict.get('type', 'Unknown')}")

    def has_conflicts(self) -> bool:
        return len(self.state.get("conflicts", [])) > 0
