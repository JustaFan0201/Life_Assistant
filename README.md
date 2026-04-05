#  Life Assistant |  Discord 生活助手


> **Life Assistant** 是一個基於 **Python** 與 **discord.py** 開發的模組化 Discord 機器人，旨在透過現代化的 UI 與自動化邏輯，成為伺服器中的助手。

---

## 📖 專案簡介 (Introduction)

本專案採用 **進階模組化架構 (Package-based Cogs)**，解決了傳統單一檔案開發的雜亂問題。透過將功能拆分為獨立的「專案包」，我們實現了以下設計目標：

**邏輯分離 (Logic Separation)**：每個功能 (如 GPT, Ticketing) 擁有獨立的命名空間。
**介面分離 (UI Separation)**：採用 **MVC 風格**，將 View (按鈕)、Modal (視窗) 與 Controller (邏輯) 分層管理。
**依賴隔離 (Dependency Isolation)**：各模組可獨立管理其工具函式 (Utils)。
**易於擴充 (Extensibility)**：採用 `__init__.py` 入口設計，功能隨插即用。

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

pip install -e .
```
### 3.啟動
```bash
python -m .\bot.py
```
### 4.設定
```bash
請在discord中 使用/set_dashboard_channel, /set_login_notify_channel等指令
設定使用機器人功能頻道
```
### 資料庫遷移功能
生成檔案
```bash
alembic revision --autogenerate -m "想要打的留言"
```
更新資料庫
```bash
alembic upgrade head
```
## 🚀 功能模組 (Features)。

所有的功能模組皆獨立存放於 `cogs/` 資料夾中，並由 `System` 模組進行統一調度。

### 1. 🎛️ 系統控制台 (System Dashboard)
* **常駐控制面板**：機器人啟動時，自動在指定頻道發送/更新 Dashboard，保持版面整潔。
* **視覺化操作**：使用 Embeds 與 Buttons 取代繁瑣的文字指令。
* **跨模組調度**：控制台可直接呼叫其他模組的共用邏輯。

### 2. 📊 生活日記 (Life Tracker)
* **自定義數據追蹤**：使用者可自由建立「主分類」（如：開銷、健身、學習）並定義專屬的「數值欄位」。
* **動態圖表生成**：整合 Matplotlib，根據紀錄自動產生「甜甜圈統計圖」，視覺化各項佔比。
* **智慧區間切換**：提供週、月、半年、一年等快速切換按鈕，並支援「自訂時間區間」功能。
* **數據持久化儲存**：採用 SQLAlchemy 進行資料庫管理，確保數萬筆紀錄也能高效讀取與遷移。
* **AI 智慧分析建議**：整合 Gemini AI，每週一自動根據上週數據產生個人化的生活建議與趨勢分析。
* **標籤化管理**：支援子分類（標籤）功能，並在刪除標籤時自動進行歷史紀錄重分組，確保資料完整性。

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
    ├─ Base.py              # Discord物件父類 可添加共用函式
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
    │
    ├─ LifeTracker/              # 生活日記模組
    │   ├─ __init__.py           # 模組入口：載入 Cog 並初始化資料庫
    │   ├─ LifeTrackerTasks.py   # 核心 Cog：處理每週 AI 總結任務與指令分發
    │   │
    │   ├─ utils/                # 工具層：後端邏輯與數據處理
    │   │   ├─ __init__.py      
    │   │   ├─ LifeTracker_Manager.py # 資料庫管理器：處理 CRUD、統計邏輯與 JSON 快照
    │   │   ├─ chart_generator.py     # 圖表引擎：繪製 Matplotlib 統計圖
    │   │   └─ gemini_analyzer.py      # AI 分析器：對接 Gemini API
    │   │
    │   └─ ui/                   # 介面層：遵循 MVC 模式
    │       ├─ __init__.py      
    │       ├─ View/             # 視圖層：各級控制面板
    │       │   ├─ LifeDashboardView.py       # 模組主入口介面
    │       │   ├─ CategoryDetailView.py      # 分類看板 (圖表與分頁清單)
    │       │   ├─ LogRecordView.py           # 紀錄數據專用視圖
    │       │   ├─ ManageSubcatView.py        # 子分類管理主視圖
    │       │   └─ DeleteCategorySelectView.py # 刪除分類確認視圖
    │       │
    │       ├─ Select/           # 選擇組件：下拉選單邏輯
    │       │   ├─ CategoryDashboardSelect.py # 主介面分類切換
    │       │   ├─ RangeSelect.py             # 統計區間切換 (週/月/年)
    │       │   ├─ SubcatSelect.py            # 紀錄時選擇標籤
    │       │   ├─ EditSubcatSelect.py        # 選擇欲編輯的標籤
    │       │   ├─ DeleteSubcatSelect.py      # 選擇欲刪除的標籤
    │       │   └─ DeleteCategorySelect.py    # 選擇欲刪除的主分類
    │       │
    │       ├─ Button/           # 按鈕組件：封裝互動行為
    │       │   ├─ SetupBtn.py             # 初始化設定按鈕
    │       │   ├─ LogRecordBtn.py         # 開啟紀錄視窗按鈕
    │       │   ├─ FillRecordBtn.py        # 填寫數據按鈕
    │       │   ├─ SubmitRecordBtn.py      # 提交紀錄按鈕
    │       │   ├─ ManageSubcatBtn.py      # 管理標籤按鈕
    │       │   ├─ AddSubCategoryBtn.py    # 新增子分類按鈕
    │       │   ├─ CustomRangeBtn.py       # 自定義區間按鈕
    │       │   ├─ ToggleChartBtn.py       # 切換圖表維度按鈕
    │       │   ├─ ToggleListModeBtn.py    # 切換清單/圖表模式按鈕
    │       │   ├─ ToggleDeleteBtn.py      # 切換刪除狀態按鈕
    │       │   ├─ ToggleDeleteBtn.py      # 切換刪除模式按鈕
    │       │   ├─ EditModeBtn.py          # 進入編輯模式按鈕
    │       │   ├─ PageBtn.py              # 清單分頁控制按鈕
    │       │   ├─ BackToDetailBtn.py      # 返回分類詳情按鈕
    │       │   └─ BackToLifeDashboardBtn.py # 返回生活日記主頁按鈕
    │       │
    │       └─ Modal/            # 視窗層：表單輸入介面
    │           ├─ SetupCategoryModal.py    # 初始建立分類表單
    │           ├─ AddSubCategoryModal.py   # 新增子分類標籤表單
    │           ├─ DynamicLogModal.py       # 根據欄位動態生成的紀錄表單
    │           ├─ InputValueModal.py       # 數值輸入修正表單
    │           ├─ EditSubcatNameModal.py   # 修改標籤名稱表單
    │           └─ SetRangeModal.py         # 設定自定義天數範圍
    ├─ if more.../
    


