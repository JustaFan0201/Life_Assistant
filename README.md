# 多功能 Discord Bot 

##  專題簡介
本專題實作一個 **多功能 Discord Bot**，整合多種實用功能，讓使用者在伺服器中能方便地查詢資訊、互動及完成日常操作。  
機器人以 **Python + discord.py** 開發，並使用 **Cogs 架構** 將各模組功能分離，達到 **模組化、易於維護、互不衝突** 的設計。  

---

##  功能模組設計
機器人主要包含以下三大功能模組，每個模組獨立於 `cogs/` 資料夾中：  

### 1. 搶票系統（Ticketing System）
- 提供高鐵查詢班次功能（透過 **交通部 TDX API**）。  
- 使用者可輸入出發站、到達站、日期與時間，Bot 回覆對應班次。  
- 自動生成 **高鐵訂票連結**，點擊即可跳轉至官網訂票頁。  
- 提供 **訂票提醒功能**，在開放訂票時間通知使用者。  

 檔案：`cogs/ticketing.py`

---

### 2.  Google Drive 上傳系統
- 使用者可透過 Slash 指令上傳檔案，Bot 自動將檔案傳至 **Google Drive**。  
- 支援 OAuth 2.0 驗證，確保帳號安全性。  
- 上傳成功後，回傳檔案連結供使用者下載或分享。  

 檔案：`cogs/drive_upload.py`

---

### 3.  機器人互動功能
- 提供互動小功能，例如：  
  - `/hello` → Bot 回覆 "Hello, world!"  
  - `/roll` → 擲骰子功能，隨機回覆數字  
  - `/ping` → 測試延遲（Bot 回覆毫秒數）  
- 讓使用者體驗更有趣的互動過程。  

 檔案：`cogs/interactions.py`

---

##  架構
│── bot.py                # 主程式，負責啟動機器人與載入 Cogs  
│── .env                  # 儲存 Discord Bot Token（需自行建立） 
│── requirements.txt      # 相依套件清單   
│  
├─ cogs/                  # 各功能模組  
│   ├─ ticketing.py       # 搶票系統  
│   ├─ drive_upload.py    # Google Drive 上傳  
│   └─ interactions.py    # 基本互動功能  
│  
└─ credentials/           # Google API 憑證資料  
    └─ credentials.json  