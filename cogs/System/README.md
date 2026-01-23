# 🛠️ 實作 Example：THSR 子介面與導航架構

本章節將說明如何實作 「主選單 (System Dashboard) ↔ 子選單 (THSR Dashboard)」的雙向導航系統。  
我們使用 Discord 的 edit_message 機制，讓使用者在不產生新訊息的情況下，原地切換介面。
## 📂 架構概覽

我們將修改以下三個檔案來完成此功能：

1.  **`cogs/System/ui/buttons.py`**：定義「前往 THSR」按鈕 (入口)。 
2.  **`cogs/THSR/ui/view.py`**：定義「THSR 子介面」與「工廠方法」。
3.  **`cogs/System/ui/view.py`**：將「前往 THSR」按鈕放入主控台。
---

## Step 1. 定義導航按鈕 (前往子選單)
**📂 檔案位置：** `cogs/System/ui/buttons.py`

這個按鈕負責呼叫 THSR_DashboardView 的靜態工廠方法，取得子介面並切換過去。

```python
import discord
from discord import ui

# =================================================================
# [System] 前往「THSR 高鐵模組」的導航按鈕
# =================================================================
class GoToTHSRButton(ui.Button):
    def __init__(self, bot):
        super().__init__(
            label="高鐵時刻表", 
            style=discord.ButtonStyle.primary, # 藍紫色
            emoji="🚄",
            row=0
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        # 💡 [關鍵技巧]：Lazy Import 避免循環引用
        # 從 THSR 模組引入 View
        from cogs.THSR.ui.view import THSR_DashboardView
        
        # 1. 直接呼叫 THSR_DashboardView 的靜態工廠方法
        # 這會回傳標準化的 (Embed, View)
        embed, view = THSR_DashboardView.create_dashboard_ui(self.bot)
        
        # 2. 切換過去 (原地變身)
        await interaction.response.edit_message(embed=embed, view=view)
```
## Step 2. 製作 THSR 子介面 (Sub-Interface)
**📂 檔案位置：** `cogs/THSR/ui/view.py`

這個檔案負責定義 THSR 模組的主選單 **(THSR_DashboardView)**。我們在這裡實作 靜態工廠方法，供外部（如 System 的按鈕）呼叫。

```python
import discord
from discord import ui

# 1. 引入 System 的返回鍵 (通用按鈕)
from ...System.ui.buttons import BackToMainButton

# 2. 引入 THSR 自己的功能按鈕 (例如「開啟查詢」按鈕)
from .buttons import OpenTHSRQueryButton

# ====================================================
# THSR 主選單 (Dashboard)
# ====================================================
class THSR_DashboardView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        
        # --- A. 加入 THSR 功能按鈕 ---
        # 這裡放置 THSR 模組的功能入口
        self.add_item(OpenTHSRQueryButton(bot)) 
        
        # --- B. 加入返回按鈕 ---
        # 這顆按鈕點下去後，會呼叫 MainControlView 重建主選單
        self.add_item(BackToMainButton(bot))

    @staticmethod
    def create_dashboard_ui(bot):
        """
        [工廠模式] 統一產生 THSR Dashboard 的 Embed 與 View
        供所有「前往 THSR」的按鈕呼叫使用
        """
        embed = discord.Embed(
            title="🚄 高鐵服務中心",
            description="> 歡迎使用高鐵查詢系統，請選擇您需要的服務：",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        # 設定縮圖與裝飾
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/3063/3063822.png")
        
        embed.add_field(
            name="功能說明", 
            value="🗓️ **查詢時刻表**：即時爬取高鐵官網班次\n🎫 **自動購票**：(開發中...)\n⚙️ **系統設定**：(開發中...)", 
            inline=False
        )
        
        embed.set_footer(text="Powered by Selenium • JustaFan0201")
        
        # 建立 View
        view = THSR_DashboardView(bot)
        
        return embed, view
```
## Step 3. 設定主介面入口 (Main Entry)
**📂 檔案位置：** `cogs/System/ui/view.py`

主介面 (MainControlView) 是整個 Bot 的首頁。我們將 Step 1 寫好的 GoToTHSRButton 放進來，作為進入 THSR 模組的入口。

```python
import discord
from discord import ui

# 引入定義好的按鈕
# GoToTHSRButton: 前往高鐵 (定義在 System/ui/buttons.py)
# StatusButton: 系統狀態 (定義在 System/ui/buttons.py)
from .buttons import GoToTHSRButton, StatusButton, GoToItineraryButton, GoToGmailButton

class MainControlView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        
        # --- 第一排：導航區 (Navigation) ---
        # 點擊這個按鈕，介面會切換成 THSR_DashboardView (進入子選單)
        self.add_item(GoToTHSRButton(bot))
        
        # 其他模組入口...
        self.add_item(GoToItineraryButton(bot))
        self.add_item(GoToGmailButton(bot))
        
        # --- 第二排：系統功能區 (System) ---
        self.add_item(StatusButton(bot))

    @staticmethod
    def create_dashboard_ui(bot):
        """
        [工廠模式] 統一產生 System Dashboard 的 Embed 與 View
        """
        embed = discord.Embed(
            title="Life Assistant 控制中心",
            description="> 歡迎使用全能助手，請點擊下方按鈕操作：",
            color=0x2b2d31,
            timestamp=discord.utils.utcnow()
        )
        # ... (Embed 內容設定) ...
        
        view = MainControlView(bot)
        return embed, view
```
## 流程總結 
1. 使用者在主選單點擊 「🚄 高鐵時刻表」 (GoToTHSRButton)。

2. 按鈕觸發 callback，呼叫 THSR_DashboardView.create_dashboard_ui(bot)。

3. 靜態方法回傳 THSR 的 Embed 與 View。

4. Discord 介面原地更新為 THSR 子選單。

5. 使用者在子選單點擊 「🔙 返回主選單」 (BackToMainButton)。

6.按鈕觸發 callback，呼叫 MainControlView.create_dashboard_ui(bot)。

Discord 介面原地更新回 System 主選單。

這樣就完成了完美的雙向導航！