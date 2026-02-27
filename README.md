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
### 2.設定
```bash
請參考example.env內容
```
### 3.啟動
```bash
python .\bot.py
```
### 4.設定
```bash
請在discord中 使用/set_dashboard_channel, /set_login_notify_channel等指令
設定使用機器人功能頻道
```
---


## 🚀 功能模組 (Features)。

所有的功能模組皆獨立存放於 `cogs/` 資料夾中，並由 `System` 模組進行統一調度。

### 1. 🎛️ 系統控制台 (System Dashboard)
* **常駐控制面板**：機器人啟動時，自動在指定頻道發送/更新 Dashboard，保持版面整潔。
* **視覺化操作**：使用 Embeds 與 Buttons 取代繁瑣的文字指令。
* **跨模組調度**：控制台可直接呼叫其他模組的共用邏輯。

### 2. 🎫 高鐵服務系統 (THSR System)
* **線上訂票**：依照使用者的車次條件查詢高鐵班次，完成線上訂票並將其添加進車票庫中。
* **定時訂票**：設定好下定車次與預定時間，機器人持續訂票，並將其添加進車票庫中。
* **車票記錄**：查看過去車票紀錄與定時訂票紀錄。
* **設定個資**：設定身分證、信箱、手機號碼、TGO帳號，在購票時自動輸入。

### 3. 📅 行程管理 (Itinerary Management)
* **視覺化日程表**：透過控制台一鍵查看當前安排，支援分頁顯示與過期行程自動標記。
* **互動式操作**：提供 Modal 視窗功能，讓使用者能快速新增、編輯或刪除行程資料。
* **主動提醒任務**：具備背景監控任務 (Tasks Loop)，定時掃描 JSON 資料庫。
* **在行程開始前自動發送 Discord 通知**：確保重要預約不遺漏。
* **本地資料庫同步**：所有行程資料持久化儲存於 JSON 檔案，確保資料在機器人重啟後依然存在。

### 4. 📧 郵件管理 (Gmail Management)
* **高效郵件輪詢 (Polling)**：採用高效 IMAP 輪詢機制取代不穩定長連線，確保在任何網路環境下都能穩定抓取新信。
* **新信即時通知**：偵測到新郵件時，自動發送包含發件人、主旨與內容摘要的精美 Embed 通知。
* **智慧防漏/防刷機制**：透過唯一 ID (UID) 比對技術，即使在檢查間隔內收到多封郵件也能依序處理。
* **嚴格過濾重複訊號**：保證同一封郵件絕不重複發送通知。
* **一鍵撰寫功能**：直接從儀表板開啟 Modal 撰寫郵件，並透過 SMTP 協定即時送出，實現無縫整合。




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
    │       └─ gmail_view.py    # 處理寄信 Modal (EmailSendView) 與新信通知介面(NewEmailNotificationView)
    │
    ├─ THSR/           # 高鐵服務系統
    │   ├─ __init__.py 
    │   ├─ dashboard.py 
    │   │ 
    │   ├─ ui/              # 介面層 (THSR子選單)
    │   │   ├─ view.py      # THSR Dashboard View
    │   │   └─ buttons.py   # THSR 功能按鈕
    │   ├─ utils/           # 工具層 
    │   │   └─ 
    │   └─ src/                 # 核心邏輯層
    │       ├─__init__.py
    │       ├─ AutoBooking.py   # 訂票功能
    │       └─ GetTimeStamp.py  # 查詢車次時間功能
    │
    ├─ System/              # UI  
    │   ├─ __init__.py      # 模組入口 (Setup)
    │   ├─ dashboard.py     # 主介面 連接其他服務入口
    │   └─ ui/              # 介面：負責外觀與互動元件
    │       ├─ __init__.py
    │       ├─ view.py      # 顯示的文字介面外觀
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
    ├─ if more.../
    


