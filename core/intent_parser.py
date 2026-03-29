# core/intent_parser.py
import logging
import json
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from core.llm_client import analyze_intent

# ==========================================
# 1. 模組日誌設定
# ==========================================
logger = logging.getLogger("SafeClaw.IntentParser")

# ==========================================
# 2. 定義 Pydantic 資料模型 (強制 JSON 結構)
# ==========================================
class ParsedIntent(BaseModel):
    """LLM 意圖解析的標準輸出結構"""
    intent_type: str = Field(
        description="意圖類型。可選值: 'direct_reply' (直接對話), 'tool_call' (需要呼叫擴充工具執行任務)"
    )
    tool_name: Optional[str] = Field(
        default=None, 
        description="若 intent_type 為 'tool_call'，填入精確的工具名稱；否則填 null。例如: 'update_location', 'get_weather'"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict, 
        description="呼叫工具所需的參數列表 (以鍵值對表示)。若無需工具則保持空字典。"
    )
    reply_text: Optional[str] = Field(
        default=None, 
        description="若 intent_type 為 'direct_reply'，填入要回覆給使用者的文字；若為 'tool_call' 則填 null。"
    )

# ==========================================
# 3. 意圖解析主程式
# ==========================================
async def parse_user_intent(
    user_text: str, 
    available_tools: List[dict] = None,
    context_state: dict = None
) -> ParsedIntent:
    """
    將使用者的自然語言輸入解析為嚴格的結構化指令。
    
    Args:
        user_text (str): 使用者的輸入文字。
        available_tools (list): 目前系統已註冊的擴充工具列表與說明。
        context_state (dict): 當下環境變數 (例如：出國狀態、所在位置)。
        
    Returns:
        ParsedIntent: 解析後的結構化意圖物件。
    """
    if available_tools is None:
        available_tools = []
        
    if context_state is None:
        context_state = {}

    # ---------------------------------------------------------
    # 步驟 A: 動態組合 System Prompt (情境與工具注入)
    # ---------------------------------------------------------
    system_prompt = (
        "你是一個名為 SafeClaw 的高階 AI 助理的「意圖解析引擎」。\n"
        "你的任務是判斷使用者的輸入是否需要呼叫特定的「擴充工具 (Tool)」，或是只需要「直接回覆 (Direct Reply)」。\n\n"
    )
    
    # 【開發指引：情境注入】將 TinyDB 中的狀態餵給 LLM
    if context_state:
        system_prompt += f"【目前系統與使用者狀態 (Context)】:\n{json.dumps(context_state, ensure_ascii=False, indent=2)}\n\n"
        
    # 將現有的 Plugins 註冊給 LLM 知道
    if available_tools:
        system_prompt += "【目前可用的擴充工具 (Available Tools)】:\n"
        for tool in available_tools:
            system_prompt += f"- 名稱: {tool['name']} | 說明: {tool['description']}\n"
        system_prompt += "\n若使用者的需求完全符合上述工具，請設定 intent_type 為 'tool_call' 並精準提取 parameters。\n"
    else:
        system_prompt += "【目前無可用的擴充工具】，請一律使用 'direct_reply'。\n"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_text}
    ]

    logger.info(f"[意圖解析] 開始分析使用者輸入: '{user_text}'")
    
    # ---------------------------------------------------------
    # 步驟 B: 呼叫底層 LLM 進行嚴格的 JSON 驗證解析
    # ---------------------------------------------------------
    parsed_result = await analyze_intent(
        messages=messages,
        response_model=ParsedIntent
    )
    
    # ---------------------------------------------------------
    # 步驟 C: 防呆與 Fallback 機制 (防禦性編程)
    # ---------------------------------------------------------
    if not parsed_result:
        logger.warning("[意圖解析] 解析失敗或格式驗證不通過，啟用 Fallback 回覆機制。")
        return ParsedIntent(
            intent_type="direct_reply",
            reply_text="抱歉，我的意圖解析模組目前有點混亂，無法準確轉換成系統指令。請換個方式再說一次。"
        )
        
    # 紀錄成功解析的結構
    logger.info(f"[意圖解析成功] 動作: {parsed_result.intent_type} | 工具: {parsed_result.tool_name}")
    logger.debug(f"[意圖詳細參數] {parsed_result.model_dump_json()}")
    
    return parsed_result