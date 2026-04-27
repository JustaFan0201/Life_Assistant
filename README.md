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
* **視覺化日程表**：整合 Matplotlib 動態生成「月曆圖」，並在同一個畫面上方顯示該月的重點行程。
* **動態月份選擇**：內建動態月份下拉選單 (MonthSelect)，自動計算最大偏移量，讓使用者能一鍵跳轉至「目前起至明年 12 月」的任何月份，無縫規劃未來行程。
* **互動式原地操作**：透過 Modal 視窗快速新增行程；刪除行程時採用「下拉選單連動解鎖按鈕」的原地狀態更新設計，大幅減少切換畫面的視覺干擾。
* **集中化設定管理**：導入 itinerary_config.py，將分頁數量、限制字數與 Emoji 映射集中管理。
* **關聯式資料庫與主動提醒**：利用關聯式資料庫，支援高效查詢；具備背景監控任務 (Tasks Loop)，定時檢查並在行程開始前自動發送專屬的 Discord 通知。

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
    ├─ Itinerary/                # 行程管理模組
    │  ├─ __init__.py            # 模組入口：載入 Cog
    │  ├─ itinerary_cog.py       # 核心 Cog：處理 Discord 指令轉發與提醒任務迴圈 (Tasks)
    │  ├─ itinerary_config.py    # 集中設定檔：管理常數、字數限制與 Emoji 映射
    │  │
    │  ├─ utils/                 # 工具層：後端邏輯與數據處理
    │  │  ├─ __init__.py       
    │  │  ├─ calendar_manager.py # 資料庫管理器
    │  │  └─ calendar_drawer.py  # 圖表引擎：整合 Matplotlib 動態繪製包含行程熱點的月曆圖片
    │  │
    │  └─ ui/                    # 介面層：遵循 MVC 模式與 SPA 設計
    │      ├─ __init__.py       
    │      ├─ View/              # 視圖層：控制面板與版面佈局
    │      │  ├─ ItineraryDashboardView.py # 模組主入口：整合月曆圖片、議程清單與所有操作的 SPA 看板
    │      │  └─ ItineraryDeleteView.py    # 刪除行程專用視圖
    │      │
    │      ├─ Select/            # 選擇組件：下拉選單邏輯
    │      │  ├─ MonthSelect.py  # 動態月份跳轉選單 (支援跳轉至明年 12 月)
    │      │  ├─ DeleteSelect.py # 選擇欲刪除的行程 (連動解鎖確認按鈕)
    │      │  └─ AddSelects.py   # 新增行程時的年份、月份、隱私與優先級設定選單
    │      │
    │      ├─ Button/            # 按鈕組件：封裝互動行為
    │      │  ├─ AddItemBtn.py   # 開啟新增行程流程
    │      │  ├─ DeleteItemBtn.py # 切換至刪除行程面板
    │      │  ├─ ConfirmDeleteBtn.py # 執行永久刪除資料庫紀錄
    │      │  ├─ NextPageBtn.py  # 智慧型下一頁 (自動適配 Dashboard 與 DeleteView)
    │      │  ├─ PrevPageBtn.py  # 智慧型上一頁
    │      │  └─ BackToItineraryDashboardBtn.py # 返回主看板
    │      │
    │      └─ Modal/             # 視窗層：表單輸入介面
    │          └─ ItineraryModal.py # 收集具體日期、時間與行程內容的彈窗
    │
    ├─ LifeTracker/              # 生活日記模組
    │   ├─ __init__.py           # 模組入口：載入 Cog 並初始化資料庫
    │   ├─ LifeTrackerTasks.py   # 核心 Cog：處理每週 AI 總結任務與指令分發
    │   │
    │   ├─ utils/                # 工具層：後端邏輯與數據處理
    │   │   ├─ __init__.py      
    │   │   ├─ LifeTracker_Manager.py # 資料庫管理器：處理 CRUD、統計邏輯與 JSON 快照
    │   │   ├─ chart_generator.py     # 圖表引擎：動態繪製 Matplotlib 統計圖
    │   │   └─ gemini_analyzer.py      # AI 分析器：對接 Gemini API 進行數據分析
    │   │
    │   └─ ui/                   # 介面層：遵循 MVC 模式
    │       ├─ __init__.py      
    │       ├─ View/             # 視圖層：各級控制面板 (Layouts)
    │       │   ├─ LifeDashboardView.py       # 模組主入口：分類選擇與概覽
    │       │   ├─ CategoryDetailView.py      # 分類看板：統計圖表與歷史清單
    │       │   ├─ RangeEditView.py           # 區間編輯模式：管理時間快捷選項
    │       │   ├─ LogRecordView.py           # 紀錄數據專用導覽視圖
    │       │   ├─ ManageSubcatView.py        # 子分類 (標籤) 管理主視圖
    │       │   └─ DeleteCategorySelectView.py # 刪除分類確認安全視圖
    │       │
    │       ├─ Select/           # 選擇組件：下拉選單邏輯 (Controllers)
    │       │   ├─ CategoryDashboardSelect.py # 主介面分類切換
    │       │   ├─ RangeSelect.py             # 支援「切換顯示」與「刪除區間」雙模式
    │       │   ├─ SubcatSelect.py            # 紀錄時選擇標籤
    │       │   ├─ EditSubcatSelect.py        # 選擇欲編輯的標籤
    │       │   ├─ DeleteSubcatSelect.py      # 選擇欲刪除的標籤
    │       │   └─ DeleteCategorySelect.py    # 選擇欲刪除的主分類
    │       │
    │       ├─ Button/           # 按鈕組件：封裝互動行為 (Actions)
    │       │   ├─ SetupBtn.py             # 初始化設定
    │       │   ├─ LogRecordBtn.py         # 開啟紀錄視窗
    │       │   ├─ FillRecordBtn.py        # 進入數據填充流程
    │       │   ├─ SubmitRecordBtn.py      # 提交數據至資料庫
    │       │   ├─ ManageSubcatBtn.py      # 管理標籤介面切換
    │       │   ├─ AddSubCategoryBtn.py    # 新增子分類標籤
    │       │   ├─ ToggleRangeEditBtn.py   # 進入時間區間編輯模式
    │       │   ├─ ToggleChartBtn.py       # 切換圖表統計維度
    │       │   ├─ ToggleListModeBtn.py    # 切換清單/圖表模式
    │       │   ├─ EditModeBtn.py          # 進入編輯模式
    │       │   ├─ PageBtn.py              # 歷史紀錄分頁控制
    │       │   ├─ BackToDetailBtn.py      # 返回分類詳情面板
    │       │   └─ BackToLifeDashboardBtn.py # 返回生活日記主分頁
    │       │
    │       └─ Modal/            # 視窗層：表單輸入介面 (Forms)
    │           ├─ SetupCategoryModal.py    # 初始建立分類 (定義欄位)
    │           ├─ AddSubCategoryModal.py   # 新增子分類標籤
    │           ├─ DynamicLogModal.py       # 根據分類欄位動態生成的紀錄表單
    │           ├─ InputValueModal.py       # 數值修正輸入
    │           ├─ EditSubcatNameModal.py   # 修改標籤名稱
    │           └─ SetRangeModal.py         # 自定義天數輸入 (支援年/月/週/天換算)
    ├─ if more.../
    


