import discord
from discord import ui
import asyncio

# 引入爬蟲
from ..src.GetTimeStamp import get_thsr_schedule

# [Dashboard] 開啟查詢按鈕
class OpenTHSRQueryButton(ui.Button):
    def __init__(self, bot):
        super().__init__(label="查詢時刻表", style=discord.ButtonStyle.primary, emoji="🗓️", row=0)
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        from .view import THSRQueryView
        embed, view = THSRQueryView.create_new_ui(self.bot)
        await interaction.response.edit_message(embed=embed, view=view)

# 1. 查詢執行按鈕
class THSRSearchButton(ui.Button):
    def __init__(self):
        super().__init__(label="查詢", style=discord.ButtonStyle.success, row=4, disabled=True)

    async def callback(self, interaction: discord.Interaction):
        view = self.view # 這是 THSRQueryView
        await interaction.response.defer()
        
        # 顯示載入中...
        ticket_info = (
            f"> 🚄 **起訖**：`{view.start_station}` ➔ `{view.end_station}`\n"
            f"> 📅 **時間**：`{view.date_val}` 　⏰ `{view.time_val}`\n"
            f"> 🎫 **設定**：`{view.trip_type}` ／ `{view.ticket_type}`"
        )

        loading_embed = discord.Embed(
            title="🔍 正在搜尋班次...", 
            description=f"{ticket_info}\n\n⏳ **正在連線至高鐵官網擷取資料，請稍候...**", 
            color=discord.Color.from_rgb(0, 162, 232)
        )
        # 可以加上一個動態的 Loading圖示 (選用)
        loading_embed.set_thumbnail(url="https://i.imgur.com/uUEmznY.gif")
        await interaction.edit_original_response(embed=loading_embed, view=None)

        try:
            result_data = await asyncio.to_thread(
                get_thsr_schedule, 
                view.start_station, 
                view.end_station, 
                view.date_val, 
                view.time_val,
                view.ticket_type,
                view.trip_type
            )
            
            # 建立結果 Embed
            if isinstance(result_data, dict) and "data" in result_data:
                final_embed = discord.Embed(
                    title=f"🚄 {result_data['start']} ➔ {result_data['end']}",
                    description=f"📅 **{result_data['date']}** ({view.time_val} 後)\n🎫 {view.trip_type} / {view.ticket_type}",
                    color=0xec6c00
                )
                if not result_data['data']:
                     final_embed.description += "\n⚠️ 查無班次"
                else:
                    for train in result_data['data']:
                        val = f"`{train['dep']} ➔ {train['arr']}`\n⏱️ {train['duration']} | 🏷️ {train['discount']}"
                        final_embed.add_field(name=f"🚅 {train['id']}", value=val, inline=True)
            else:
                final_embed = discord.Embed(title="❌ 查詢失敗", description=str(result_data.get('error')), color=discord.Color.red())

            # ★★★ 關鍵：呼叫 view.py 裡的 THSRResultView ★★★
            from .view import THSRResultView
            await interaction.edit_original_response(embed=final_embed, view=THSRResultView(view.bot, view))
            
        except Exception as e:
            print(f"Error: {e}")
            from .view import THSRResultView
            err = discord.Embed(title="❌ 系統錯誤", description=str(e), color=discord.Color.red())
            await interaction.edit_original_response(embed=err, view=THSRResultView(view.bot, view))

# 2. 交換按鈕
class THSRSwapButton(ui.Button):
    def __init__(self):
        super().__init__(emoji="🔁", style=discord.ButtonStyle.secondary, row=4)
    async def callback(self, interaction: discord.Interaction):
        self.view.start_station, self.view.end_station = self.view.end_station, self.view.start_station
        await self.view.refresh_ui(interaction)

# 3. 票種按鈕
class THSRTicketTypeButton(ui.Button):
    def __init__(self, current_type="全票"):
        super().__init__(label=current_type, style=discord.ButtonStyle.secondary, row=4)
    async def callback(self, interaction: discord.Interaction):
        types = ["全票", "大學生", "早鳥"]
        self.view.ticket_type = types[(types.index(self.view.ticket_type) + 1) % 3]
        self.label = self.view.ticket_type
        await self.view.refresh_ui(interaction)

# 4. 行程按鈕
class THSRTripTypeButton(ui.Button):
    def __init__(self, current_type="單程"):
        super().__init__(label=current_type, style=discord.ButtonStyle.secondary, row=4)
    async def callback(self, interaction: discord.Interaction):
        types = ["單程", "來回"]
        self.view.trip_type = types[(types.index(self.view.trip_type) + 1) % 2]
        self.label = self.view.trip_type
        await self.view.refresh_ui(interaction)

# 5. 回主頁按鈕
class THSRHomeButton(ui.Button):
    def __init__(self, bot):
        super().__init__(label="主頁", style=discord.ButtonStyle.danger, row=4)
        self.bot = bot
    async def callback(self, interaction: discord.Interaction):
        from .view import THSR_DashboardView
        embed, view = THSR_DashboardView.create_dashboard_ui(self.bot)
        await interaction.response.edit_message(embed=embed, view=view)