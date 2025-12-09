"""
CBR Agent - 案例推理主控制器
"""

from typing import Dict, Any, List
from utils.logger import logger
from knowledge.retriever import CaseRetriever
from agents.reasoner import CaseReasoner

class CBRAgent:
    """案例推理 Agent"""

    def __init__(self):
        """初始化 CBR Agent"""
        logger.info("正在初始化 CBR Agent...")

        # 初始化檢索器
        self.retriever = CaseRetriever()

        # 初始化推理器
        self.reasoner = CaseReasoner()

        logger.info("✅ CBR Agent 初始化完成")

    def diagnose(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行診斷推理

        Args:
            query: 查詢數據

        Returns:
            診斷結果
        """
        try:
            # 1. 檢索相似案例
            logger.info("步驟 1/3: 檢索相似案例...")
            similar_cases = self.retriever.retrieve(query)
            logger.info(f"✅ 檢索到 {len(similar_cases)} 個相似案例")

            # 2. 推理診斷結果
            logger.info("步驟 2/3: 推理診斷結果...")
            diagnosis = self.reasoner.reason(query, similar_cases)
            logger.info("✅ 推理完成")

            # 3. 組裝結果
            result = {
                "syndrome": diagnosis.get("syndrome", ""),
                "treatment_principle": diagnosis.get("treatment_principle", ""),
                "formula": diagnosis.get("formula", ""),
                "herbs": diagnosis.get("herbs", []),
                "reasoning": diagnosis.get("reasoning", ""),
                "similar_cases": similar_cases,
                "confidence": diagnosis.get("confidence", 0.0)
            }

            logger.info("步驟 3/3: 結果組裝完成")
            return result

        except Exception as e:
            logger.error(f"診斷失敗: {e}", exc_info=True)
            raise

    def close(self):
        """關閉資源"""
        if hasattr(self.retriever, 'close'):
            self.retriever.close()
        logger.info("CBR Agent 資源已釋放")
