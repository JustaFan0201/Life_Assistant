#  Life Assistant |  Discord 生活助手


> **Life Assistant** 是一個基於 **Python** 與 **discord.py** 開發的模組化 Discord 機器人，旨在透過現代化的 UI 與自動化邏輯，成為伺服器中的助手。

---

## 📖 專案簡介 (Introduction)

本專案採用 **進階模組化架構 (Package-based Cogs)**，徹底解決了傳統單一檔案開發的雜亂問題。透過將功能拆分為獨立的「專案包」，我們實現了以下設計目標：

* ✅ **邏輯分離 (Logic Separation)**：每個功能 (如 GPT, Ticketing) 擁有獨立的命名空間。
* ✅ **介面分離 (UI Separation)**：採用 **MVC 風格**，將 View (按鈕)、Modal (視窗) 與 Controller (邏輯) 分層管理。
* ✅ **依賴隔離 (Dependency Isolation)**：各模組可獨立管理其工具函式 (Utils)。
* ✅ **易於擴充 (Extensibility)**：採用 `__init__.py` 入口設計，功能隨插即用。

---
## 環境建置與使用
### 1.虛擬環境
```bash
#for windows NOTE: only for powershell not cmd  
cd Life_Assistant  
.\sync.ps1  
```
### 2.啟動
```bash
python .\bot.py
```
---


## 🚀 功能模組 (Features)。

所有的功能模組皆獨立存放於 `cogs/` 資料夾中，並由 `System` 模組進行統一調度。

### 1. 🎛️ 系統控制台 (System Dashboard)
* **常駐控制面板**：機器人啟動時，自動在指定頻道發送/更新 Dashboard，保持版面整潔。
* **視覺化操作**：使用 Embeds 與 Buttons 取代繁瑣的文字指令。
* **跨模組調度**：控制台可直接呼叫 GPT 或其他模組的共用邏輯。

### 2. 🤖 AI 助手 (GPT Integration)
* **智能對話**：支援與 AI 進行自然語言問答。
* **🔮 運勢生成**：隨機生成今日運勢與建議。
* **⚙️ 自動回覆系統**：
    * 可監聽特定頻道的對話並自動回應。
    * 具備 **開關功能 (Toggle)**，透過控制台一鍵啟動/暫停，無需輸入指令。

### 3. 🎫 搶票系統 (Ticketing System)
* **即時查詢**：快速查詢高鐵班次、時間與剩餘座位。
* **自動訂票**：機器人持續監控餘票，並在有票時協助自動下訂 (Automation)。

### 4. 📅 行程管理 (Itinerary Management)
* **視覺化日程表**：透過控制台一鍵查看當前安排，支援分頁顯示與過期行程自動標記。
* **互動式操作**：提供 Modal 視窗功能，讓使用者能快速新增、編輯或刪除行程資料。
* **主動提醒任務**：具備背景監控任務 (Tasks Loop)，定時掃描 JSON 資料庫。
* **在行程開始前自動發送 Discord 通知**：確保重要預約不遺漏。
* **本地資料庫同步**：所有行程資料持久化儲存於 JSON 檔案，確保資料在機器人重啟後依然存在。

### 5. 📧 郵件管理 (Gmail Management)
* **高效郵件輪詢 (Polling)**：採用高效 IMAP 輪詢機制取代不穩定長連線，確保在任何網路環境下都能穩定抓取新信。
* **新信即時通知**：偵測到新郵件時，自動發送包含發件人、主旨與內容摘要的精美 Embed 通知。
* **智慧防漏/防刷機制**：透過唯一 ID (UID) 比對技術，即使在檢查間隔內收到多封郵件也能依序處理。
* **嚴格過濾重複訊號**：保證同一封郵件絕不重複發送通知。
* **一鍵撰寫功能**：直接從儀表板開啟 Modal 撰寫郵件，並透過 SMTP 協定即時送出，實現無縫整合。

---

## 🎨 UI 與互動設計 (UI & Interaction)

本專案引入了 Discord 最新的 UI 元件，解決了傳統指令無法帶參數或互動性差的問題。

### 🎛️ 主控台元件 (Dashboard Components)
位於 `cogs/System/ui/`，整合了多種互動模式：

| 元件名稱 | 類型 | 功能描述 | 技術亮點 |
| :--- | :--- | :--- | :--- |
| **🔮 今日運勢** | `Button` | 呼叫 GPT 生成運勢 | **跨 Cog 呼叫** (System → GPT) |
| **💬 與 AI 對話** | `Button` | 彈出對話視窗 | 觸發 **Modal (模態視窗)** |
| **⚙️ 自動回覆** | `Button` | 切換監聽狀態 (On/Off) | **即時狀態更新** (Toggle Logic) |
| **ℹ️ 系統狀態** | `Button` | 顯示機器人延遲 (Latency) | **Ephemeral Message** (僅自己可見) |


### 📝 輸入視窗 (Modal)
> **解決方案：** 傳統按鈕無法讓使用者輸入參數。
* 點擊「與 AI 對話」後，系統彈出表單視窗。
* 使用者輸入文字後，後端接收並傳送給 GPT 處理，實現流暢的互動體驗。

---

## 📂 專案架構 (Project Structure)

本專案採用 **Package** 結構，並在 `System` 模組中實作了 **Core/UI 分層** 的設計模式。

```text
Life_Assistant/
│── bot.py                  # 機器人啟動核心 (Entry Point)
│── .env                    # 環境變數 (Token, Keys) - ⚠️ 請勿上傳
│── requirements.txt        # 依賴套件清單
│── sync.ps1                # Windows 自動化建置腳本
│── keep_alive.py           # 後端 Web Server (防止休眠)
│
└─ cogs/                    # 功能模組存放區 (Plugins)
    │
    ├─ Gmail/                   # Gmail 郵件管理模組
    │   ├─ __init__.py          # 模組入口：包含 setup(bot) 函式
    │   ├─ gmail.py             # 核心 Cog：處理定時輪詢 (Polling) 與產生儀表板 UI
    │   │
    │   ├─ utils/               # 工具層：負責連線與郵件解析
    │   │   ├─ __init__.py      
    │   │   └─ gmail_tool.py    # 處理 IMAP/SMTP 連線、郵件內容解析與 ID 比對
    │   │
    │   └─ views/               # 介面層：負責 Discord UI 互動
    │       ├─ __init__.py      
    │       └─ gmail_view.py    # 處理寄信 Modal (EmailSendView) 與新信通知介面 (NewEmailNotificationView)
    │
    ├─ GPT/                 # GPT功能  
    │   ├─ __init__.py 
    │   │ 
    │   ├─ ui/              # 介面層 (GPT子選單)
    │   │   ├─ view.py      # GPT Dashboard View
    │   │   └─ buttons.py   # GPT 功能按鈕
    │   ├─ utils/           # 工具層 (API 連線)
    │   │   └─ ask_gpt.py
    │   └─ src/             # 核心邏輯層
    │       ├─ fortune.py   # 運勢功能 (含共用邏輯)
    │       └─ reply.py     # 自動回覆與對話邏輯
    │
    ├─ System/              # UI  
    │   ├─ __init__.py      # 模組入口 (Setup)
    │   ├─ core.py          # 主要用於創造與顯示主介面文字介紹
    │   └─ ui/              # 介面：負責外觀與互動元件
    │       ├─ __init__.py
    │       ├─ menu_view.py # View 工廠：負責組裝按鈕
    │       └─ buttons.py   # 定義主介面需要或是在其他介面也需要的 Button 類別
    │
    ├─ Itinerary/               # 行程管理模組
    │   ├─ __init__.py          # 模組入口：包含 setup(bot) 函式
    │   ├─ itinerary.py         # 核心 Cog：處理 Discord 指令與任務迴圈 (Tasks)
    │   ├─ itinerary.json       # 本地資料庫：儲存使用者行程與提醒資訊 (建議列入 .gitignore) <----這個再說
    │   │
    │   ├─ utils/               # 工具層：純邏輯運算與檔案讀寫
    │   │   ├─ __init__.py      # 使其成為子套件
    │   │   └─ itinerary_tool.py # 處理 JSON 讀寫、排序、時間檢查與過期自檢
    │   │
    │   └─ views/               # 介面層：負責 Discord UI 互動
    │       ├─ __init__.py      # 使其成為子套件
    │       ├─ itinerary_view.py # 處理 Modal 彈窗輸入、下拉選單選取
    │       └─ view.py          # 通用的分頁或基礎介面元件
    │
    └─ Ticketing/           # 搶票系統
        └─ ...


