# core/security_guard.py
import logging
from pathlib import Path
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# ==========================================
# 1. 獨立的安全性稽核日誌 (Audit Logger)
# ==========================================
security_logger = logging.getLogger("SafeClaw.SecurityAudit")
security_logger.setLevel(logging.INFO)

# 確保所有安全事件都寫入專屬的 audit log
audit_handler = logging.FileHandler("logs/security_audit.log", encoding='utf-8')
audit_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
# 避免重複綁定 handler
if not security_logger.handlers:
    security_logger.addHandler(audit_handler)

# ==========================================
# 2. 定義系統絕對邊界 (Sandboxes)
# ==========================================
# 使用 __file__ 抓取專案根目錄，避免因為執行目錄不同導致相對路徑解析錯誤
BASE_DIR = Path(__file__).resolve().parent.parent
AUTHORIZED_READ_DIR = (BASE_DIR / "data" / "authorized_docs").resolve()
AUTHORIZED_WRITE_DIR = (BASE_DIR / "output").resolve()

# ==========================================
# 3. 自定義安全例外 (Security Exceptions)
# ==========================================
class SecurityViolationError(Exception):
    """當發生違反 SafeClaw 安全鐵律的操作時拋出此例外"""
    pass

# ==========================================
# 4. 核心防禦邏輯 (Path Validation)
# ==========================================
def _is_safe_path(target_path: Path, allowed_base_path: Path) -> bool:
    """
    核心防禦機制：防範目錄遍歷 (Path Traversal) 攻擊。
    透過 resolve() 解析所有 '../' 與捷徑，並檢查是否確實位於允許的父目錄下。
    """
    try:
        resolved_target = target_path.resolve()
        # 檢查 allowed_base_path 是否為 target 的上層目錄，或剛好等於該目錄
        return allowed_base_path in resolved_target.parents or allowed_base_path == resolved_target
    except Exception as e:
        security_logger.error(f"[解析錯誤] 路徑解析失敗: {target_path} - 錯誤: {e}")
        return False

def verify_read_access(file_path: str | Path) -> Path:
    """
    【守則 2: 權限隔離】檢查是否允許讀取。
    僅允許讀取 data/authorized_docs/ 內的檔案。
    回傳安全的絕對路徑 Path 物件，若越權則拋出 SecurityViolationError。
    """
    target = Path(file_path)
    if _is_safe_path(target, AUTHORIZED_READ_DIR):
        security_logger.info(f"[✅ 授權讀取] 存取路徑: {target.resolve()}")
        return target.resolve()
    else:
        security_logger.warning(f"[🚨 越權阻擋] 嘗試非法讀取: {target}")
        raise SecurityViolationError(f"越權操作：禁止讀取 '{file_path}' (僅限 data/authorized_docs 目錄)")

def verify_write_access(file_path: str | Path) -> Path:
    """
    【守則 1: 寫入沙盒化】檢查是否允許寫入或建立檔案。
    僅允許寫入 output/ 內的檔案。絕對禁止刪除指令。
    回傳安全的絕對路徑 Path 物件，若越權則拋出 SecurityViolationError。
    """
    target = Path(file_path)
    if _is_safe_path(target, AUTHORIZED_WRITE_DIR):
        security_logger.info(f"[✅ 授權寫入] 目標路徑: {target.resolve()}")
        return target.resolve()
    else:
        security_logger.warning(f"[🚨 越權阻擋] 嘗試非法寫入: {target}")
        raise SecurityViolationError(f"越權操作：禁止寫入 '{file_path}' (僅限 output 目錄)")

# ==========================================
# 5. 人工授權機制 (Human-in-the-Loop)
# ==========================================
def generate_hitl_keyboard(action_name: str, payload: str = "") -> InlineKeyboardMarkup:
    """
    【守則 3: 關鍵動作授權】產生確認與取消的 Telegram 按鈕。
    
    Args:
        action_name (str): 準備執行的動作名稱 (例如 'send_email', 'buy_ticket')
        payload (str): 夾帶的額外資訊，將透過 callback_data 傳回 (Telegram 限制 callback_data 最長 64 bytes)
        
    Returns:
        InlineKeyboardMarkup: 包含確認與取消按鈕的 Telegram 鍵盤物件
    """
    # 組合 callback_data，供 Telegram Handler 辨識
    # 格式例如: "hitl:yes:send_email:12345"
    approve_data = f"hitl:yes:{action_name}:{payload}"[:64]
    reject_data = f"hitl:no:{action_name}:{payload}"[:64]
    
    keyboard = [
        [
            InlineKeyboardButton("✅ 確認執行", callback_data=approve_data),
            InlineKeyboardButton("❌ 取消", callback_data=reject_data)
        ]
    ]
    security_logger.info(f"[🛡️ 請求授權] 正在為動作 '{action_name}' 產生 HITL 確認按鈕。")
    return InlineKeyboardMarkup(keyboard)