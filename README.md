##  專題簡介 (Introduction)

**Life Assistant** 是一個基於 **Python** 與 **discord.py** 開發的全能型 Discord 機器人，旨在成為伺服器中最強大的自動化助手。

本專案採用 **進階模組化架構 (Package-based Cogs)**，徹底解決了傳統單一檔案開發的雜亂問題。透過將功能拆分為獨立的「專案包」，我們實現了：

* ✅ **邏輯分離**：每個功能 (如搶票、GPT) 擁有獨立的資料夾與命名空間。
* ✅ **依賴隔離**：各模組可獨立管理其輔助檔案。
* ✅ **易於擴充**：採用 `__init__.py` 入口設計，隨插即用。
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
### 3.測試

如果在自己電腦測自己的bot bot.py中  
local_test改成True 或註解掉來測試  
但記得要commit上去時 改成False  
```
async def main():
    async with bot:
        await load_extensions()
        keep_alive(local_test=True)
        await bot.start(TOKEN)
```
---
##  功能模組 (Features)

所有的功能模組皆獨立存放於 `cogs/` 資料夾中：

### 1.  搶票系統 (Ticketing System)
*  即時查詢：快速查詢高鐵班次、時間與剩餘座位。
*  自動訂票：機器人持續監控餘票，並在有票時協助自動下訂 (Automation)。

### 2.  Google 整合系統 (開發中)
*  ...。

### 3.  行事曆系統 (開發中)
*  ...。

---

## 📂 專案架構 (Project Structure)

本專案採用 **Package** 結構，`cogs/` 下的每個資料夾都是一個獨立的 Python 套件。

```text
Life_Assistant/
│── bot.py                  #  機器人啟動核心 (Entry Point)
│── .env                    #  環境變數 (Token, Keys) - ⚠️ 請勿上傳
│── requirements.txt        #  依賴套件清單
│── sync.ps1                #  Windows 自動化建置腳本 (Auto Setup)
│── keep_alive.py           # 後端 讓機器人保持不下線
│
└─ cogs/                    #  功能模組存放區 (Plugins)
    ├─example.py            #  單個cog檔案範例
    │
    ├─ GPT/                 # [範例] GPT 模組包
    │   ├─ __init__.py      # 模組入口 (負責匯出 Cog)
    │   ├─ utils/           # 該專案專用的工具
    │   │   ├─ __init__.py  # 標示 utils 為工具
    │   │   └─ ask_gpt.py   # API 連線
    │   └─ src/             # 核心邏輯層
    │       ├─ __init__.py  # 標示 src 為套件
    │       ├─ fortune.py   # 功能 A
    │       └─ reply.py     # 功能 B
    │
    └─ Ticketing/           # [範例] 搶票模組包
        ├─ __init__.py
        └─ src/ ...