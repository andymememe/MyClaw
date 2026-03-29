專案規劃：安全優先的個人化 Telegram AI 助理
1. 專案概述

本專案旨在開發一個基於 Telegram 介面的個人化 AI 助理。該助理具備任務排程、個人資訊記憶、功能擴充及指令執行等能力。系統核心以「安全設計（Safe by Design）」與「零信任（Zero-Trust）」為原則，確保在提供高度便利性的同時，絕對禁止任何破壞性操作、越權資料存取及未經授權的外部行為。
2. 系統架構建議

為符合隱私與安全條件，建議採用以下技術堆疊：

    介面層 (UI/UX)： Telegram Bot API (提供即時通訊與互動按鈕)。

    大腦與推論層： Python 作為核心邏輯，搭配本地端 LLM 伺服器 (如 LM Studio) 進行意圖判斷與文字生成，確保資料不落陸。

    記憶體與資料層：

        對話與狀態紀錄： TinyDB (輕量、易於備份、適合單機作業)。

        知識庫與個人資訊： ChromaDB (向量資料庫，用於相似度檢索與 RAG 架構，讓助理「記住」你的生活習慣)。

    任務排程器： Python APScheduler (處理定期自動化任務)。

3. 核心功能模組 (Features)
3.1 意圖解析與執行引擎 (Task Execution)

    接收 Telegram 訊息後，由 LLM 解析使用者意圖（例如：查詢天氣、紀錄筆記、設定提醒）。

    透過定義嚴格的 JSON Schema 讓 LLM 輸出標準化指令，再由 Python 後端呼叫對應的內部函式。

3.2 個人資訊記憶模組 (Memory & RAG)

    主動紀錄： 當你告訴助理「我平常喜歡喝無糖綠茶」、「我的車牌是 ABC-1234」，系統會將其向量化存入 ChromaDB。

    被動提取： 當你要求助理規劃事情時，系統會先從 ChromaDB 檢索相關個人偏好作為 Context 餵給 LLM，讓回答更貼近你的生活。

3.3 定期自動化排程 (Automation)

    支援 Cron-like 語法或自然語言設定（例：「每週五下午 3 點提醒我交週報」）。

    定時觸發特定腳本（如：爬取特定網站的新聞摘要並推播至 Telegram）。

3.4 擴充功能系統 (Plugin System)

    採用模組化設計，每個擴充功能（Tool/Function）皆為獨立的 Python 腳本。

    透過 Function Calling 機制讓 LLM 知道目前有哪些工具可用。

4. 安全與防護機制 (Security Framework) - 核心重點

為滿足你的三項嚴格條件，系統必須實作以下防護牆：
4.1 防止破壞性操作 (Non-Destructive Operations)

    權限隔離： 助理執行的環境（如 Docker 容器）只賦予最低執行權限（Principle of Least Privilege）。

    唯讀模式預設： 任何檔案系統的存取預設為 Read-Only。如需寫入，只能寫入系統專屬的 output/ 資料夾，絕對禁止存取系統根目錄或執行 rm、del 等指令。

4.2 防止未授權資訊與檔案存取 (Restricted Access)

    路徑白名單 (Path Whitelisting)： 助理只能讀取預先授權的資料夾（例如 data/authorized_docs/）。

    內容過濾器： 在 LLM 回覆或讀取檔案前，加入一層正則表達式 (Regex) 或輕量化過濾模型，確保敏感資訊不會被異常拋出。

4.3 防止未授權外部動作 (Human-in-the-Loop, HITL)

    關鍵操作攔截： 針對「寄信」、「購買」、「API 修改資料」等狀態改變 (State-changing) 的操作，系統絕對不會自動執行。

    Telegram 授權按鈕： 當 LLM 判斷需要執行上述動作時，會先在 Telegram 發送一則包含 [確認執行] 與 [取消] 的 Inline Keyboard 訊息。只有在你親自點擊「確認」後，系統才會放行該 API 呼叫。

5. 開發階段規劃 (Roadmap)

    Phase 1: 基礎建設 (Week 1)

        建立 Telegram Bot 並完成基本 Echo 功能。

        串接本地 LLM，實作基本的對話與意圖識別。

    Phase 2: 記憶與排程 (Week 2)

        整合 TinyDB 儲存使用者對話狀態。

        整合 ChromaDB 實作個人資訊的儲存與 RAG 檢索。

        導入 APScheduler 完成定時推播功能。

    Phase 3: 擴充與安全鎖 (Week 3)

        建立 Plugin 介面，實作第一個工具（如：天氣查詢）。

        實作 HITL (Human-in-the-Loop) 授權機制： 針對敏感 Tool 加上 Telegram 按鈕確認邏輯。

        設定目錄存取權限與白名單過濾。

    Phase 4: 測試與優化 (Week 4)

        進行越權測試（嘗試誘騙 Bot 讀取未授權檔案或發送郵件），驗證安全防線。

        優化 LLM 的 Prompt 確保行為穩定不越界。