# main.py
import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# 引入我們開發的核心模組
from core.intent_parser import parse_user_intent

# ==========================================
# 1. 初始化安全沙盒與基礎目錄結構
# ==========================================
REQUIRED_DIRS = [
    "logs",
    "data/tinydb",
    "data/chromadb",
    "data/authorized_docs",
    "output",
    "config",
    "core",
    "memory",
    "plugins",
    "scheduler"
]

for directory in REQUIRED_DIRS:
    os.makedirs(directory, exist_ok=True)

open("logs/security_audit.log", "a").close()

# ==========================================
# 2. 設定系統日誌 (Logging)
# ==========================================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("logs/system.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SafeClaw.Main")

# ==========================================
# 3. 載入環境變數與核心設定
# ==========================================
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "your_token_here":
    logger.error("⚠️ 未設定正確的 TELEGRAM_BOT_TOKEN，請檢查 .env 檔案！")
    exit(1)

# ==========================================
# 4. 模擬註冊的擴充工具 (Mock Tools for Testing)
# ==========================================
# 這些是假工具，用來測試 LLM 是否能正確辨識意圖並產出對應的 JSON
MOCK_TOOLS = [
    {
        "name": "get_weather",
        "description": "查詢特定地點的目前天氣資訊。使用者提及天氣、氣溫時呼叫。參數需包含 'location'。"
    },
    {
        "name": "update_location",
        "description": "更新使用者的目前所在國家或城市。當使用者說「我抵達XX了」、「我在XX旅行」時呼叫。參數需包含 'location'。"
    }
]

# ==========================================
# 5. Telegram Bot 互動邏輯
# ==========================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /start 指令"""
    user_name = update.effective_user.first_name
    welcome_text = (
        f"你好，{user_name}！我是 **SafeClaw**。\n"
        "我的大腦與意圖解析引擎已經上線！你可以試著跟我聊天，或是要求我查天氣、紀錄位置來測試我的判斷能力。"
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理一般文字訊息，交由 LLM 解析意圖"""
    user_text = update.message.text
    logger.info(f"收到來自 {update.effective_user.first_name} 的訊息: {user_text}")
    
    # 1. 提升使用者體驗：先發送等待訊息
    processing_msg = await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="🧠 腦波運轉中，請稍候..."
    )

    try:
        # 2. 呼叫核心意圖解析器
        parsed_intent = await parse_user_intent(
            user_text=user_text,
            available_tools=MOCK_TOOLS,
            # 模擬情境狀態：你可以把 is_traveling 改成 True 看看 LLM 的反應變化
            context_state={"is_traveling": False, "location": "台灣"} 
        )

        # 3. 根據解析結果做出不同回應
        if parsed_intent.intent_type == "direct_reply":
            # 純聊天模式
            await processing_msg.edit_text(parsed_intent.reply_text)
            
        elif parsed_intent.intent_type == "tool_call":
            # 呼叫工具模式 (目前僅印出參數供測試)
            response_text = (
                "⚙️ **[系統觸發] 意圖解析為工具呼叫**\n"
                f"🔹 **目標工具:** `{parsed_intent.tool_name}`\n"
                f"🔹 **解析參數:** `{parsed_intent.parameters}`\n\n"
                "*(註：目前外掛系統尚未實作，此為意圖解析測試)*"
            )
            await processing_msg.edit_text(response_text, parse_mode='Markdown')
            
    except Exception as e:
        logger.error(f"訊息處理失敗: {e}")
        await processing_msg.edit_text("❌ 抱歉，我的處理中樞發生了異常，請查看系統日誌。")

# ==========================================
# 6. 系統主程式入口
# ==========================================
def main():
    logger.info("啟動 SafeClaw 系統初始化程序...")
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    logger.info("🚀 SafeClaw 大腦已連接，開始接收訊息...")
    app.run_polling()

if __name__ == '__main__':
    main()