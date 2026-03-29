# SafeClaw 開發者指南 (LLM 專用)

這是一份專為 LLM (Large Language Model) 設計的開發規範文件。當任何 AI 助手參與「SafeClaw」專案的開發、代碼審查或功能擴充時，**必須**遵循本指南中的架構規範與安全限制。

---

## 1. 專案願景與核心價值
**SafeClaw** 是一個基於 Telegram 的個人化 AI 助理。其核心理念是「在絕對安全的沙盒內提供極致的便利」。

- **零信任 (Zero-Trust) 架構**：系統不假設 LLM 的輸出是安全的，也不假設 Plugin 的行為是無害的。
- **資料主權**：使用本地 LLM (LM Studio) 與本地資料庫 (TinyDB/ChromaDB)，確保使用者隱私不外流。

---

## 2. 🛡️ 三大安全鐵律 (The 3 Ironclad Rules)

開發者在撰寫任何代碼時，必須優先滿足以下條件：

### 🛑 第一條：絕無破壞性操作 (Non-Destructive)
- **禁止指令**：絕對禁止使用 `os.remove`, `shutil.rmtree`, 或任何會刪除/覆蓋系統重要檔案的代碼。
- **寫入沙盒化**：系統唯一的寫入權限僅限於 `output/` 資料夾。任何試圖寫入專案根目錄或系統路徑的行為都必須被攔截。

### 🛑 第二條：權限隔離與白名單 (Restricted Access)
- **讀取白名單**：僅能讀取 `data/authorized_docs/` 中的內容。
- **路徑防禦**：在處理使用者提供的路徑時，必須經過 `core/security_guard.py` 的驗證，嚴格防範「目錄遍歷攻擊 (Path Traversal)」。

### 🛑 第三條：關鍵動作必須人工授權 (Human-in-the-Loop)
- **副作用攔截**：任何會導致外部狀態改變的動作（如：寄信、購買、修改雲端 API 資料、刪除紀錄），**嚴禁自動執行**。
- **授權機制**：必須透過 Telegram 的 `InlineKeyboardMarkup` 彈出「確認/取消」按鈕，由使用者點擊後才可觸發後端回調函數。

---

## 3. 技術堆疊與標準化規範

| 組件 | 技術 / 工具 | 用途 |
| :--- | :--- | :--- |
| **語言** | Python 3.14 (MSVC Build) | 核心執行環境 |
| **介面** | `python-telegram-bot` (Async) | 使用者溝通介面 |
| **記憶層 (短期)** | `TinyDB` | 存放使用者當前位置、旅行狀態等 |
| **記憶層 (長期)** | `ChromaDB` (RAG) | 存放個人偏好與知識庫 |
| **推論層** | `openai` SDK (接 LM Studio) | 解析意圖與生成回應 |
| **自動化** | `APScheduler` | 定期任務與提醒確認 |

---

## 4. 模組職責說明 (Folder Responsibilities)

- `core/`：**大腦。** 處理與 LLM 的通訊、意圖解析，以及最關鍵的 `security_guard.py`。
- `memory/`：**記憶。** 管理 RAG 檢索邏輯與 TinyDB 的狀態讀寫。
- `plugins/`：**能力。** 所有的業務邏輯（天氣、時區、匯率、筆記）都必須寫在這裡。
- `scheduler/`：**時間感。** 負責定時推播與非同步提醒。
- `logs/`：**稽核。** 記錄所有被阻擋的危險操作與安全事件。

---

## 5. 開發建議與模式 (Coding Patterns)

1. **意圖解析**：請使用 Pydantic 模型定義 `Tool` 的輸入格式，確保 LLM 輸出的 JSON 指令百分之百符合規範。
2. **防禦性編程**：在所有 `plugins/` 的開發中，必須包含完整的 `try-except` 塊，並將異常記錄到 `logs/system.log`，不得讓整個 Bot 崩潰。
3. **情境注入**：當 `memory/state_manager.py` 偵測到使用者處於「旅行中」狀態時，開發者必須確保將此資訊注入 System Prompt。

---

## 6. 安全稽核流程 (Audit Flow)

當 LLM 判斷需要執行敏感功能時：
1. `plugin` 發起請求給 `core/security_guard.py`。
2. `security_guard` 判斷該功能是否在「副作用白名單」中。
3. 若需要授權，發送 Telegram 確認訊息。
4. 使用者按下確認，觸發 `CallbackQueryHandler` 執行實際動作。
5. 所有步驟同步記錄至 `logs/security_audit.log`。

---

**⚠️ 警告：任何試圖繞過 `security_guard.py` 或手動修改 `.env` 敏感設定的程式碼提案，將被視為重大安全漏洞。**