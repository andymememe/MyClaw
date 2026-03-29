import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ==========================================
# 1. 初始化安全沙盒與基礎目錄結構
# ==========================================
REQUIRED_DIRS = [
    "logs",
    "data/tinydb",
    "data/chromadb",
    "data/authorized_docs", # ★ 唯一授權讀取區
    "output",               # ★ 唯一授權寫入區
    "config",
    "core",
    "memory",
    "plugins",
    "scheduler"
]

for directory in REQUIRED_DIRS:
    os.makedirs(directory, exist_ok=True)

# 為了確保基礎檔案存在，建立空白的 security_audit.log
open("logs/security_audit.log", "a").close()

# ==========================================
# 2. 設定系統日誌 (Logging)
# ==========================================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("logs/system.log", encoding='utf-8'),
        logging.StreamHandler() # 同時輸出到終端機方便除錯
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
# 4. Telegram Bot 互動邏輯 (初期測試)
# ==========================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /start 指令"""
    user_name = update.effective_user.first_name
    welcome_text = (
        f"你好，{user_name}！我是 **SafeClaw**。\n"
        "我目前正在嚴格的安全沙盒中運行。\n\n"
        "我的大腦（LLM）與記憶模組尚未上線，請稍候開發進度。"
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_text, parse_mode='Markdown')

async def echo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理一般文字訊息 (目前為 Echo 測試模式)"""
    user_text = update.message.text
    logger.info(f"收到來自 {update.effective_user.first_name} 的訊息: {user_text}")
    
    # 這裡未來會將 user_text 交給 core.intent_parser 進行 LLM 解析
    reply_text = f"⚙️ [系統測試] 收到訊息：{user_text}\n(等待意圖解析引擎接入...)"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=reply_text)

# ==========================================
# 5. 系統主程式入口
# ==========================================
def main():
    logger.info("啟動 SafeClaw 系統初始化程序...")
    
    # 建立 Application 實例
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # 註冊指令與訊息處理器
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo_message))

    # 開始輪詢 (Polling) 接收 Telegram 訊息
    logger.info("🚀 SafeClaw 已上線，開始接收訊息...")
    app.run_polling()

if __name__ == '__main__':
    main()