import discord
from discord import ui
import asyncio
from datetime import datetime, timedelta

# 引入爬蟲與 System 的返回按鈕
from ..utils.thsr_scraper import get_thsr_schedule, STATION_MAP

# ====================================================
# 1. 最後一步：日期輸入表單 (Modal)
# ====================================================
class THSRDateModal(ui.Modal):
    def __init__(self, start_station, end_station):
        super().__init__(title="輸入查詢時間")
        self.start_station = start_station
        self.end_station = end_station
        
        default_date = (datetime.now() + timedelta(days=1)).strftime("%Y/%m/%d")
        
        # ★★★ 修正點：discord.py 使用 ui.TextInput (不是 InputText) ★★★
        self.add_item(ui.TextInput(
            label="出發日期 (YYYY/MM/DD)", 
            default=default_date,  # discord.py 使用 default 而不是 value
            placeholder="例如: 2026/01/18",
            min_length=10,
            max_length=10
        ))
        
        self.add_item(ui.TextInput(
            label="出發時間 (HH:MM)", 
            default="10:30",       # discord.py 使用 default
            placeholder="例如: 10:30",
            min_length=5,
            max_length=5
        ))

    async def on_submit(self, interaction: discord.Interaction):
        # ★★★ 修正點：discord.py 的 Modal 回呼函式名稱是 on_submit (不是 callback) ★★★
        
        # 取得輸入值 (children 順序對應上面的 add_item)
        date_input = self.children[0].value
        time_input = self.children[1].value
        
        # 簡單驗證格式
        try:
            datetime.strptime(date_input, "%Y/%m/%d")
        except ValueError:
            await interaction.response.send_message("❌ 日期格式錯誤，請依照 `YYYY/MM/DD` (例如 2026/01/18)", ephemeral=True)
            return

        # 這裡必須先 defer，因為爬蟲會跑很久
        await interaction.response.defer()
        
        msg = await interaction.followup.send(
            f"🔍 **正在查詢高鐵班次...**\n"
            f"🚄 `{self.start_station}` ➔ `{self.end_station}`\n"
            f"📅 `{date_input}` `{time_input}`\n"
            f"⏳ 機器人正在操作瀏覽器，請稍候約 5-10 秒..."
        )

        try:
            # 執行爬蟲
            result = await asyncio.to_thread(
                get_thsr_schedule, 
                start_station=self.start_station, 
                end_station=self.end_station, 
                search_date=date_input, 
                search_time=time_input
            )
            await msg.edit(content=result)
            
        except Exception as e:
            await msg.edit(content=f"❌ 查詢失敗: {e}")


# ====================================================
# 2. 中間層：車站選擇器 (View)
# ====================================================
class THSRStationSelectView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot 
        self.start_station = None
        self.end_station = None
        
        # 這裡才 import 避免循環引用
        from ...System.ui.buttons import BackToMainButton
        
        # 加入返回主選單 (Row 4)
        self.add_item(BackToMainButton(bot))

    def get_station_options(self):
        return [discord.SelectOption(label=s, value=s) for s in STATION_MAP.keys()]

    # --- 下拉選單 1: 出發站 ---
    # 參數順序: (interaction, select)
    @ui.select(placeholder="📍 請選擇 [出發站]", min_values=1, max_values=1, row=0)
    async def select_start(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.start_station = select.values[0]
        await self.update_button_state(interaction)

    # --- 下拉選單 2: 抵達站 ---
    # 參數順序: (interaction, select)
    @ui.select(placeholder="🏁 請選擇 [抵達站]", min_values=1, max_values=1, row=1)
    async def select_end(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.end_station = select.values[0]
        await self.update_button_state(interaction)

    # --- 狀態檢查核心邏輯 ---
    async def update_button_state(self, interaction: discord.Interaction):
        # 1. 找到「下一步」按鈕 (Row 2)
        confirm_btn = None
        for child in self.children:
            if isinstance(child, ui.Button) and child.row == 2:
                confirm_btn = child
                break
        
        if not confirm_btn: 
            await interaction.response.edit_message(view=self)
            return

        # 2. 邏輯判斷
        if self.start_station is None or self.end_station is None:
            confirm_btn.disabled = True
            confirm_btn.style = discord.ButtonStyle.secondary
            if self.start_station is None:
                confirm_btn.label = "請先選擇出發站"
            elif self.end_station is None:
                confirm_btn.label = "請先選擇抵達站"

        elif self.start_station == self.end_station:
            confirm_btn.disabled = True
            confirm_btn.label = "起點與終點不可相同"
            confirm_btn.style = discord.ButtonStyle.danger
            
        else:
            confirm_btn.disabled = False
            confirm_btn.label = f"下一步: {self.start_station} ➔ {self.end_station}"
            confirm_btn.style = discord.ButtonStyle.success

        # 3. 更新 UI
        await interaction.response.edit_message(view=self)

    # --- 下一步按鈕 (預設 Disabled) ---
    # 參數順序: (interaction, button)
    @ui.button(label="請先選擇車站", style=discord.ButtonStyle.secondary, disabled=True, row=2)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 跳出 Modal 讓使用者填日期
        modal = THSRDateModal(self.start_station, self.end_station)
        await interaction.response.send_modal(modal)

    # --- 填入選項 ---
    def fill_options(self):
        opts = self.get_station_options()
        self.children[0].options = opts
        self.children[1].options = opts