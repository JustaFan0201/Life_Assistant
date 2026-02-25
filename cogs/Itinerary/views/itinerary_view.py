import discord
from datetime import datetime, timezone, timedelta
from discord import ui
from cogs.System.ui.buttons import BackToMainButton

class ItineraryModal(discord.ui.Modal, title="新增我的行程"):
    date_input = discord.ui.TextInput(label="日期 (1-31)", placeholder="例如: 2", min_length=1, max_length=2)
    time_input = discord.ui.TextInput(label="時間 (時:分)", placeholder="例如: 08:30", min_length=4, max_length=5)
    content_input = discord.ui.TextInput(label="行程內容", style=discord.TextStyle.paragraph, placeholder="請輸入行程細節...")

    def __init__(self, time_data, cog):
        super().__init__()
        self.time_data = time_data
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            year = int(self.time_data.get('year'))
            month = int(self.time_data.get('month'))
            day = int(self.date_input.value)
            time_parts = self.time_input.value.split(':')
            
            event_time = datetime(year, month, day, int(time_parts[0]), int(time_parts[1]))
            
            clean_time = event_time.replace(tzinfo=None)
            
            success, report = await self.cog.process_data_sql(
                interaction, 
                time_obj=clean_time, 
                description=self.content_input.value,
                is_private=(self.time_data.get('privacy') == "1"),
                priority=self.time_data.get('priority', "2") 
            )
            await interaction.followup.send(report, ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ 輸入格式錯誤：{e}", ephemeral=True)

class ItineraryAddView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
        self.new_data = {
            "year": str(datetime.now().year), 
            "month": str(datetime.now().month), 
            "privacy": "1",
            "priority": "2" 
        }
        self.add_item(BackToMainButton(self.cog.bot))

    @discord.ui.select(placeholder="年分", row=0, options=[discord.SelectOption(label=str(y), value=str(y)) for y in range(2026, 2029)])
    async def select_year(self, interaction, select):
        self.new_data["year"] = select.values[0]
        await interaction.response.defer()

    @discord.ui.select(placeholder="月分", row=1, options=[discord.SelectOption(label=f"{i}月", value=str(i)) for i in range(1, 13)])
    async def select_month(self, interaction, select):
        self.new_data["month"] = select.values[0]
        await interaction.response.defer()

    @discord.ui.select(placeholder="提醒模式", row=2, options=[
        discord.SelectOption(label="私人行程 (私訊提醒)", value="1", emoji="🔒"),
        discord.SelectOption(label="公開行程 (頻道提醒)", value="0", emoji="🌍")
    ])
    async def select_privacy(self, interaction, select):
        self.new_data["privacy"] = select.values[0]
        await interaction.response.defer()

    @discord.ui.select(placeholder="緊急程度 (預設低)", row=3, options=[
        discord.SelectOption(label="緊急程度：高", value="0", emoji="🔴"),
        discord.SelectOption(label="緊急程度：中", value="1", emoji="🟡"),
        discord.SelectOption(label="緊急程度：低", value="2", emoji="🟢")
    ])
    async def select_priority(self, interaction, select):
        self.new_data["priority"] = select.values[0]
        await interaction.response.defer()
    
    @discord.ui.button(label="下一步：填寫細節", style=discord.ButtonStyle.primary, row=4)
    async def next_step(self, interaction, button):
        await interaction.response.send_modal(ItineraryModal(self.new_data, self.cog))

class ViewPageSelect(discord.ui.View):
    def __init__(self, cog, user_id, page=0):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id
        self.page = page

        self.data_list = self.cog.db_manager.get_user_events(user_id)
        count = len(self.data_list)
        start, end = page * 10, (page + 1) * 10
        current_items = self.data_list[start:end]

        tz_tw = timezone(timedelta(hours=8))
        self.embed = discord.Embed(title="📅 您的行程表", color=0xE0A04A, timestamp=datetime.now(tz_tw))
        
        priority_map = {"0": "🔴", "1": "🟡", "2": "🟢"}

        if not current_items:
            self.embed.description = "目前沒有任何行程"
        else:
            for i, item in enumerate(current_items, start + 1):
                time_str = item.event_time.strftime("%Y-%m-%d %H:%M")
                privacy_emoji = "🔒" if item.is_private else "🌍"
                p_emoji = priority_map.get(str(item.priority), "🟢")

                self.embed.add_field(
                    name=f"{privacy_emoji}{p_emoji} #{i} | {time_str}",
                    value=item.description or "無內容",
                    inline=False
                )
            self.embed.set_footer(text=f"第 {page+1} 頁 | 共有 {count} 筆行程")

        self.add_item(BackToMainButton(self.cog.bot))
        if self.page > 0:
            btn = ui.Button(label="❮ 上一頁", row=1); btn.callback = self.prev_page; self.add_item(btn)
        if count > end:
            btn = ui.Button(label="下一頁 ❯", row=1); btn.callback = self.next_page; self.add_item(btn)

    async def prev_page(self, interaction):
        view = ViewPageSelect(self.cog, self.user_id, self.page - 1)
        await interaction.response.edit_message(embed=view.embed, view=view)

    async def next_page(self, interaction):
        view = ViewPageSelect(self.cog, self.user_id, self.page + 1)
        await interaction.response.edit_message(embed=view.embed, view=view)

class ItineraryDeleteView(discord.ui.View):
    def __init__(self, cog, user_id, page=0):
        super().__init__(timeout=None)
        self.cog = cog
        self.user_id = user_id
        self.page = page
        
        formatted = self.cog.db_manager.get_formatted_list(user_id)
        start, end = page * 10, (page + 1) * 10
        current_data = formatted[start:end]

        if current_data:
            options = [discord.SelectOption(label=d['display'][:100], value=str(d['id'])) for d in current_data]
            select = ui.Select(placeholder="選擇要刪除的行程", options=options)
            select.callback = self.select_callback
            self.add_item(select)

        self.add_item(BackToMainButton(self.cog.bot))

    async def select_callback(self, interaction: discord.Interaction):
        event_id = int(interaction.data['values'][0])
        await interaction.response.send_message(
            f"⚠️ 確定要刪除這筆行程嗎？", 
            view=ConfirmDeleteView(self.cog, event_id), 
            ephemeral=True
        )

class ConfirmDeleteView(discord.ui.View):
    def __init__(self, cog, event_id):
        super().__init__(timeout=60)
        self.cog = cog
        self.event_id = event_id

    @discord.ui.button(label="確認刪除", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def confirm_btn(self, interaction, button):
        success, msg = self.cog.db_manager.delete_event_by_id(self.event_id, interaction.user.id)
        await interaction.response.edit_message(content=msg, view=None)

class ItineraryDashboardView(ui.View):
    def __init__(self, bot, cog):
        super().__init__(timeout=None)
        self.bot, self.cog = bot, cog
        self.add_item(BackToMainButton(self.bot))

    @ui.button(label="查看行程表v4", style=discord.ButtonStyle.success, emoji="📋")
    async def view_list(self, interaction, button):
        view = ViewPageSelect(self.cog, interaction.user.id)
        await interaction.response.edit_message(embed=view.embed, view=view)

    @ui.button(label="新增行程", style=discord.ButtonStyle.primary, emoji="➕")
    async def add_item_btn(self, interaction, button):
        await interaction.response.edit_message(embed=discord.Embed(title="➕ 新增行程", color=0x3498db), view=ItineraryAddView(self.cog))

    @ui.button(label="刪除行程", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def delete_item_btn(self, interaction, button):
        await interaction.response.edit_message(content="請選擇項目：", embed=None, view=ItineraryDeleteView(self.cog, interaction.user.id))