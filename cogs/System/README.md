# 🛠️ 實作example：GPT 子介面與導航架構

本章節將說明如何實作 **「主選單 (Main Menu) ↔ 子選單 (Sub Menu)」** 的雙向導航系統。我們使用 Discord 的 `edit_message` 機制，讓使用者在不產生新訊息的情況下，原地切換介面。

## 📂 架構概覽

我們將修改以下三個檔案來完成此功能：

1.  **`cogs/System/ui/buttons.py`**：定義通用按鈕(前往 GPT、返回主選單 寫好的 需要可以再加)。
2.  **`cogs/GPT/ui/view.py`**：定義「GPT 子介面」 (運勢、對話、開關)。
3.  **`cogs/System/ui/menu_view.py`**：將「前往 GPT」按鈕放入主控台。
4.  **`cogs/System/core.py`**：主要用於顯示主介面文字介紹。 
---

## Step 1. 定義導航按鈕
**📂 檔案位置：** `cogs/System/ui/buttons.py`

這裡有兩個關鍵按鈕：
1.  **`BackToMainButton`**：負責呼叫 System Core 重建主介面。
2.  **`GoToGPTButton`**：負責建立 GPT View 並切換過去。

```python
import discord
from discord import ui

# =================================================================
# 1. 通用的「返回主選單」按鈕 (所有子介面都能用)
# =================================================================
class BackToMainButton(ui.Button):
    def __init__(self, bot):
        super().__init__(
            label="返回主選單",
            style=discord.ButtonStyle.secondary, # 灰色
            row=4 # 建議固定放在最下面一排
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        # 1. 取得 SystemCog (主控台核心)
        system_cog = self.bot.get_cog("SystemCog")

        if system_cog:
            # 2. 呼叫 core.py 裡面的 create_dashboard_ui 方法
            # 💡 這樣可以確保「返回」時看到的介面，跟一開始輸入指令看到的是一模一樣的
            embed, view = system_cog.create_dashboard_ui()
            
            # 3. 編輯訊息，切換回主介面
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.response.send_message("❌ 錯誤：找不到系統核心模組。", ephemeral=True)

# =================================================================
# 2. 「前往 GPT」的導航按鈕
# =================================================================
class GoToGPTButton(ui.Button):
    def __init__(self, bot):
        super().__init__(
            label="AI 助手功能", 
            style=discord.ButtonStyle.primary, # 藍紫色
            emoji="🤖",
            row=0
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        # 💡 [關鍵技巧]：在函式內 import，避免循環引用錯誤 (Circular Import)
        # 因為 System 引用 GPT，GPT 又引用 System，寫在最上面會報錯
        from ...GPT.ui.view import GPTDashboardView 
        
        # 1. 建立 GPT 專屬的 View
        sub_view = GPTDashboardView(self.bot)
        
        # 2. 建立 GPT 專屬的 Embed (子選單說明)
        sub_embed = discord.Embed(
            title="🤖 AI 助手控制台",
            description="這裡集合了所有 GPT 相關功能，請選擇：",
            color=0x1abc9c # 湖水綠
        )
        sub_embed.add_field(name="功能列表", value="🔮 運勢\n💬 對話\n⚙️ 設定", inline=False)
        
        # 3. 切換過去 (原地變身)
        await interaction.response.edit_message(embed=sub_embed, view=sub_view)
```
## Step 2. 製作 GPT 子介面 (Sub-Interface)
**📂 檔案位置：** `cogs/GPT/ui/view.py`

這個檔案負責定義 GPT 功能專屬的介面容器。它會將 GPT 相關的功能按鈕（如運勢、對話）組裝起來，並在最後加上一顆通用的「返回鍵」。

```python
import discord
from discord import ui

# 1. 引入 System 的返回鍵 (使用相對路徑跨模組引用)
# System 在 GPT 的上一層的隔壁，所以用 ...
from ...System.ui.buttons import BackToMainButton

# 2. 引入 GPT 自己的功能按鈕
# 假設這些按鈕定義在同目錄下的 buttons.py
from .buttons import FortuneButton, ChatButton, ToggleReplyButton

class GPTDashboardView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        
        # --- A. 加入 GPT 功能按鈕 ---
        self.add_item(FortuneButton(bot))      # 🔮 運勢
        self.add_item(ChatButton(bot))         # 💬 對話 (Modal)
        self.add_item(ToggleReplyButton(bot))  # ⚙️ 開關
        
        # --- B. 加入返回按鈕 ---
        # 這顆按鈕點下去後，會呼叫 SystemCog 重建主選單
        self.add_item(BackToMainButton(bot))   # 🔙 返回
```
## Step 3. 設定主介面入口 (Main Entry)
**📂 檔案位置：** `cogs/System/ui/menu_view.py`

主介面（Dashboard）的 View 應該保持乾淨，只負責放置「導航按鈕」或是「全域功能按鈕」。這裡我們將 Step 1 製作的「前往 GPT」按鈕放進來，作為功能的入口。

```python
import discord
from discord import ui

# 引入在 Step 1 定義好的「前往 GPT 按鈕」與其他系統按鈕
# 因為 menu_view.py 和 buttons.py 都在同一個資料夾 (System/ui)，所以用 .buttons
from .buttons import GoToGPTButton, StatusButton

class MainControlView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        
        # --- 第一排：導航區 (Navigation) ---
        # 點擊這個按鈕，介面會切換成 GPTDashboardView (進入子選單)
        self.add_item(GoToGPTButton(bot))
        
        # 未來如果有搶票系統，可以加在這裡：
        # self.add_item(GoToTicketingButton(bot))
        
        # --- 第二排：系統功能區 (System) ---
        # 這種全域的功能 (如查 Ping 值)，可以直接放在主選單
        self.add_item(StatusButton(bot))