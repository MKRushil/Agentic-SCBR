"""JSON數據處理工具"""
import json
from typing import Any, Dict
from pathlib import Path

class JSONHandler:
    """JSON處理器"""

    @staticmethod
    def load_json(filepath: str) -> Dict[str, Any]:
        """讀取JSON文件"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def save_json(data: Dict[str, Any], filepath: str, indent: int = 2) -> None:
        """保存JSON文件"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)

    @staticmethod
    def parse_json_string(json_str: str) -> Dict[str, Any]:
        """解析JSON字符串"""
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            # 嘗試提取JSON部分
            import re
            json_match = re.search(r'\{.*\}', json_str, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            raise e

    @staticmethod
    def to_json_string(data: Dict[str, Any], indent: int = 2) -> str:
        """轉換為JSON字符串"""
        return json.dumps(data, ensure_ascii=False, indent=indent)
