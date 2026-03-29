# core/llm_client.py
import os
import json
import logging
from typing import Type, TypeVar, Optional
from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

# ==========================================
# 1. 模組日誌設定
# ==========================================
logger = logging.getLogger("SafeClaw.LLMClient")

# ==========================================
# 2. 載入設定與初始化 OpenAI Client
# ==========================================
# LM Studio 預設提供與 OpenAI 相容的 API 伺服器
LLM_API_BASE = os.getenv("LLM_API_BASE", "http://localhost:1234/v1")
# 本地端伺服器通常不需要真實的 API Key，但 SDK 要求必填，給予佔位符即可
LLM_API_KEY = os.getenv("LLM_API_KEY", "lm-studio") 

try:
    client = AsyncOpenAI(
        base_url=LLM_API_BASE,
        api_key=LLM_API_KEY
    )
    logger.info(f"LLM Client 初始化成功，連線至: {LLM_API_BASE}")
except Exception as e:
    logger.error(f"LLM Client 初始化失敗: {e}")
    raise

# 用於型別提示的泛型
T = TypeVar('T', bound=BaseModel)

# ==========================================
# 3. 核心推論函式
# ==========================================
async def generate_text(messages: list[dict], temperature: float = 0.7, model: str = "local-model") -> str:
    """
    一般對話生成 (純文字回覆)。
    適用於普通的聊天、問候或總結資訊。
    """
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"[Text Generation Error] LLM 呼叫失敗: {e}")
        return "抱歉，我的大腦（LLM 伺服器）目前似乎無法連線或發生錯誤。"

async def analyze_intent(messages: list[dict], response_model: Type[T], model: str = "local-model") -> Optional[T]:
    """
    意圖解析 (強制結構化輸出)。
    搭配 Pydantic Model 使用，強制 LLM 輸出符合 JSON Schema 的資料。
    適用於判斷使用者是否要呼叫特定 Tool 或執行特定任務。
    
    Args:
        messages: 包含對話歷史與 System Prompt 的訊息列表。
        response_model: 預期的 Pydantic 資料模型。
        
    Returns:
        成功解析則回傳 Pydantic 物件，失敗則回傳 None。
    """
    # 為了提高開源模型生成 JSON 的穩定性，自動在最後一條訊息注入 Schema 提示
    schema_prompt = (
        f"\n\n請務必以純 JSON 格式輸出，並且嚴格遵守以下 JSON Schema 結構。\n"
        f"絕對不要包含任何其他解釋性文字，也不要使用 ```json 標記包裝：\n"
        f"{json.dumps(response_model.model_json_schema(), ensure_ascii=False)}"
    )
    
    injected_messages = list(messages)
    
    if injected_messages:
        injected_messages[-1] = {
            "role": injected_messages[-1]["role"],
            "content": injected_messages[-1]["content"] + schema_prompt
        }
    
    try:
        # 移除 response_format，讓相容性最大化
        response = await client.chat.completions.create(
            model=model,
            messages=injected_messages,
            temperature=0.1, # 意圖解析需要高度穩定性，調低 temperature
        )
        
        raw_text = response.choices[0].message.content.strip()
        logger.debug(f"[Intent JSON Raw Before Clean] {raw_text}")
        
        # 【本地模型特化處理】清除開源模型最愛亂加的 Markdown Code Block
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        elif raw_text.startswith("```"):
            raw_text = raw_text[3:]
            
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
            
        clean_json_str = raw_text.strip()
        logger.debug(f"[Intent JSON Cleaned] {clean_json_str}")
        
        # 使用 Pydantic 進行資料驗證與轉換
        parsed_data = response_model.model_validate_json(clean_json_str)
        return parsed_data
        
    except ValidationError as ve:
        logger.error(f"[Intent Parse Error] LLM 輸出的 JSON 不符合預期格式: {ve}\n原始輸出: {clean_json_str}")
        return None
    except Exception as e:
        logger.error(f"[Intent Request Error] 意圖解析請求失敗: {e}")
        return None