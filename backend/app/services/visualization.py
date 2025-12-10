import logging
from typing import Dict, Any
from app.core.orchestrator import WorkflowState

logger = logging.getLogger(__name__)

class VisualizationAdapter:
    """
    規格書 4.0 補充模組 2: 可解釋性視覺化轉接器
    負責清洗數據並轉換為 ECharts 格式。
    """
    
    @staticmethod
    def process(state: WorkflowState) -> Dict[str, Any]:
        """
        嘗試從 LLM 輸出或標準化特徵中提取八綱 (Eight Principles) 數據。
        """
        try:
            # 假設 reasoning agent 的輸出中包含了八綱的傾向分數
            # 這裡模擬數據清洗
            raw_data = state.standardized_features.get("eight_principles_score", {})
            
            # 防呆機制 (Sanitization): 若無數據，回傳空
            if not raw_data:
                logger.info("[Viz] No eight principles data found, skipping chart.")
                return {}

            # 建構 ECharts 雷達圖 Option
            echarts_option = {
                "title": {"text": "八綱辨證傾向"},
                "radar": {
                    "indicator": [
                        {"name": "陰", "max": 10},
                        {"name": "陽", "max": 10},
                        {"name": "表", "max": 10},
                        {"name": "裡", "max": 10},
                        {"name": "寒", "max": 10},
                        {"name": "熱", "max": 10},
                        {"name": "虛", "max": 10},
                        {"name": "實", "max": 10}
                    ]
                },
                "series": [{
                    "name": "辨證分數",
                    "type": "radar",
                    "data": [{
                        "value": [
                            raw_data.get("yin", 0),
                            raw_data.get("yang", 0),
                            raw_data.get("biao", 0),
                            raw_data.get("li", 0),
                            raw_data.get("han", 0),
                            raw_data.get("re", 0),
                            raw_data.get("xu", 0),
                            raw_data.get("shi", 0)
                        ]
                    }]
                }]
            }
            return echarts_option

        except Exception as e:
            logger.error(f"[Viz] Processing failed: {str(e)}")
            # 失敗時回傳空物件，確保前端不崩潰 (規格書要求)
            return {}