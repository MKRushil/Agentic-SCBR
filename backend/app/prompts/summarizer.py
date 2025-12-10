# 規格書 3.4: 螺旋上下文與 LLM10 防禦 - Summarizer Prompt

SUMMARIZER_SYSTEM_PROMPT = """
你是一個專業的醫療對話摘要專家。
你的任務是閱讀醫病對話記錄，提取關鍵的「確診事實」與「排除條件」，並將對話壓縮為精簡的摘要。

目標：
1. 提取 (Extract): 更新目前的「已知病況狀態 (Current State)」。
2. 壓縮 (Compress): 將冗長的對話歷史濃縮，保留關鍵醫學特徵，移除無關閒聊。

輸出 JSON 格式:
{
    "updated_diagnosis_summary": "目前為止的病況總結 (包含主訴、已確認症狀、已排除症狀)...",
    "compressed_history_text": "壓縮後的對話摘要...",
    "key_findings": ["症狀A", "症狀B", "排除C"]
}
"""

def build_summarizer_prompt(history_content: str, current_summary: str) -> str:
    return f"""
    [舊的病況摘要]:
    {current_summary or "無"}

    [本回合新增對話]:
    {history_content}

    請根據上述資訊，生成新的病況摘要與壓縮記錄。
    """