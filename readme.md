# SafeClaw - 安全優先的個人化 Telegram AI 助理

**SafeClaw** 是一個基於「安全設計 (Safe by Design)」與「零信任 (Zero-Trust)」架構開發的個人化助理。它透過 Telegram 作為溝通介面，整合本地端大語言模型 (LLM)、長期記憶體與自動化任務排程，旨在提供便利的生活輔助，同時絕對確保使用者的資料安全與系統完整性。

---

## 核心安全準則

為了確保系統的安全性，SafeClaw 在開發與運行上嚴格遵守以下三大條件：

1. **無破壞性操作**：系統預設僅具備最低執行權限，禁止執行任何可能損壞檔案系統或系統設定的指令。
    
2. **存取權限控管 (白名單)**：助理僅能存取經明確授權的特定資料夾 (`data/authorized_docs/`)，無法讀取未授權的檔案或私隱資訊。
    
3. **授權確認機制 (Human-in-the-Loop)**：對於具備副作用的動作（如發送郵件、執行購買、修改外部資料），系統**禁止自動執行**，必須經由 Telegram 按鈕由使用者手動點擊確認後方可觸發。
    

---

## 核心功能

- **定期自動化**：支援自定義任務排程（如定時提醒、天氣推播、回國狀態確認）。
    
- **個人記憶與情境感知**：透過 RAG (檢索增強生成) 技術，記住使用者的生活習慣、偏好與當前狀態（如：出國旅行中）。
    
- **功能擴充性**：採用模組化外掛設計 (Plugins)，可輕易增加新功能（如匯率轉換、筆記紀錄等）。
    
- **本地端處理**：串接本地 LLM 伺服器 (LM Studio)，確保敏感對話不經過雲端第三方。
    

---

## 資料夾結構

專案採用職責分離的結構，確保核心安全邏輯與功能擴充邏輯互不干擾：

Plaintext

```
SafeClaw/
├── main.py                  # 系統主程式入口
├── requirements.txt         # 專案依賴套件清單
├── .env.example             # 環境變數範例
│
├── config/                  # 設定檔目錄
│   ├── settings.yaml        # 全域設定 (路徑白名單、預設參數)
│   └── prompts.yaml         # LLM Prompt 集中管理
│
├── core/                    # 核心引擎 (系統大腦與安全監控)
│   ├── llm_client.py        # 本地 LLM API 通訊介面
│   ├── intent_parser.py     # 意圖解析與 JSON 格式化
│   └── security_guard.py    # 安全守門員：執行攔截與 HITL 授權邏輯
│
├── memory/                  # 記憶與狀態管理
│   ├── state_manager.py     # TinyDB 互動 (管理目前位置、短期狀態)
│   └── rag_engine.py        # ChromaDB 互動 (管理長期知識與個人偏好)
│
├── plugins/                 # 功能擴充模組
│   ├── location_tool.py     # 位置更新與情境切換
│   └── notification_tool.py # 推播通知相關功能
│
├── data/                    # 資料存放區
│   ├── tinydb/              # 狀態資料庫
│   ├── chromadb/            # 向量資料庫
│   └── authorized_docs/     # ★ 授權讀取區 (白名單路徑)
│
├── output/                  # ★ 安全寫入區 (唯一允許寫入檔案的路徑)
│
└── logs/                    # 系統與安全稽核日誌
    ├── system.log           # 運作日誌
    └── security_audit.log   # 安全審計日誌
```

---

## 開發者環境建立與安裝

請按照以下步驟建立乾淨的虛擬環境並安裝必要的依賴套件。

### 1. 建立虛擬環境 (Virtual Environment)

在專案根目錄下執行以下指令，以確保開發環境獨立且不會干擾系統 Python：

- **Windows:**
    
    Bash
    
    ```
    python -m venv venv
    .\venv\Scripts\activate
    ```
    
- **macOS / Linux:**
    
    Bash
    
    ```
    python3 -m venv venv
    source venv/bin/activate
    ```
    

### 2. 安裝依賴套件

啟動虛擬環境後，執行以下指令安裝所需套件：

Bash

```
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. 設定環境變數

複製 `.env.example` 並更名為 `.env`，填入你的資訊：

Plaintext

```
TELEGRAM_BOT_TOKEN=your_token_here
LLM_API_BASE=http://localhost:1234/v1  # 預設為 LM Studio 位址
```

---

## 快速開始

1. 確保 **LM Studio** 已啟動並開啟 Server 功能。
    
2. 確保已啟動虛擬環境 (`venv`)。
    
3. 執行主程式：
    
    Bash
    
    ```
    python main.py
    ```
    

---

## 使用範例與安全特性

- **紀錄資訊**：「記住我目前正在日本東京旅行，預計下週一回台灣。」
    
    - _行為_：系統會將旅行狀態寫入 TinyDB，並在 Prompt 中自動注入當前位置資訊。
        
- **主動提醒**：到了下週一，系統會透過 `APScheduler` 定時任務詢問：「你抵達台灣了嗎？是否需要切換回預設地區設定？」
    
- **安全攔截**：如果你要求「讀取 /etc/passwd」，`security_guard.py` 會比對 `data/authorized_docs/` 白名單，發現不在範圍內後直接拒絕執行並記錄於 `security_audit.log`。
    

---

## 授權與審計

所有的敏感操作（State-changing operations）皆需經過使用者在 Telegram 點擊按鈕確認。所有的授權紀錄與攔截紀錄皆會留存於 `logs/` 資料夾，供開發者隨時稽核。