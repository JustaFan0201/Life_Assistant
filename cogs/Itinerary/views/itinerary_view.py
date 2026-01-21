import discord
from datetime import datetime, timezone
from discord import ui
from cogs.System.ui.buttons import BackToMainButton


class ItineraryModal(discord.ui.Modal, title="新增我的行程"):
    # content = discord.ui.TextInput(label="內容")

    date_input = discord.ui.TextInput(
        label="日期 (1-31)", 
        placeholder="例如: 2", 
        min_length=1, 
        max_length=2
    )

    time_input = discord.ui.TextInput(
        label="時間 (時:分)", 
        placeholder="例如: 01:02", 
        min_length=4, 
        max_length=5
    )

    content_input = discord.ui.TextInput(
        label="行程內容", 
        style=discord.TextStyle.paragraph, 
        placeholder="請輸入行程細節..."
    )

    def __init__(self, time_data, cog):
        super().__init__()

        self.time_data = time_data
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):


        data = {
            "year": self.time_data.get('year', '未選'),
            "month": self.time_data.get('month', '未選'),
            "date": self.date_input.value,
            "hour": None,
            "minute": None,
            "time": self.time_input.value,
            "content": self.content_input.value,
            "priority": self.time_data.get("priority", '未選')
        }

        report = await self.cog.process_data(interaction, data)
        await interaction.response.send_message(report)



class ItineraryAddView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
        self.new_data = {
            "year": str(datetime.now().year),
            "month": str(datetime.now().month),
            "date": None,
            "hour": None,
            "minute": None,
            "content": None,
            "priority": None
        }
        self.add_item(BackToMainButton(self.cog.bot))

    current_year = datetime.now().year

    @discord.ui.select(
        placeholder = "年分(預設為今年)",
        row=0,
        options=[discord.SelectOption(label=str(y), value=str(y)) 
                 for y in range(datetime.now().year, datetime.now().year + 3)]
    )
    async def select_year(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.new_data["year"] = select.values[0]
        await interaction.response.defer()

    @discord.ui.select(
        placeholder = "月分(預設為這個月)",
        row=1,
        options= [discord.SelectOption(label=f"{i}月", value=str(i)) for i in range(1, 13)]
    )
    async def select_month(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.new_data["month"] = select.values[0]
        await interaction.response.defer()

    @discord.ui.select(
        placeholder = "優先級(必選項)",
        row=2,
        options= [discord.SelectOption(label="緊急", value="0", emoji="🔴"),
                  discord.SelectOption(label="重要", value="1", emoji="🟡"),
                  discord.SelectOption(label="普通", value="2", emoji="🟢")]
    )
    async def select_priority(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.new_data["priority"] = select.values[0]
        await interaction.response.defer()
    
    @discord.ui.button(label="下一步：填寫細節", style=discord.ButtonStyle.primary, row=3)
    async def next_step(self, interaction: discord.Interaction, button: discord.ui.Button):

        modal = ItineraryModal(time_data=self.new_data, cog=self.cog)
        await interaction.response.send_modal(modal)

class ViewPageSelect(discord.ui.View):
    def __init__(self, cog, data_list, page= 0):
        super().__init__(timeout=60)
        self.cog = cog
        self.page = page
        self.data_list = data_list  

        count = len(self.data_list)
        items_per_page = 10
        start = page * items_per_page
        end = start + 10

        self.embed = discord.Embed(
            title= "您的行程表",
            description= "以下是目前儲存的所有行程內容：",
            color= 0xE0A04A,
            timestamp= datetime.now(timezone.utc)
        )

        if count == 0:
            self.embed.description = "目前沒有任何行程"
        else:
            priority_map = ["🔴", "🟡", "🟢"]
            current_items = data_list[start:end]
            
            for i, item in enumerate(current_items):
                actual_index = start + i + 1 
                
                try:
                    p_emoji = priority_map[int(item.get('priority', 2))]
                    
                    year = item.get('year', '2026')
                    month = int(item.get('month') or 1)
                    date = int(item.get('date') or 1)
                    hour = int(item.get('hour') or 0)
                    minute = int(item.get('minute') or 0)

                    time_str = f"{year}-{month:02d}-{date:02d} {hour:02d}:{minute:02d}"

                    self.embed.add_field(
                        name = f"{p_emoji} #{actual_index} | {time_str}",
                        value = item['content'],
                        inline = False
                    )
                except (KeyError, ValueError, IndexError) as e:
                    print(f"資料格式錯誤：{e}")
                    continue

            self.embed.set_footer(text=f"共有 {count} 筆行程")

        self.add_item(BackToMainButton(self.cog.bot))
    
        if self.page > 0:
                btn_prev = discord.ui.Button(label="❮ 上一頁", style=discord.ButtonStyle.gray, row=1)
                btn_prev.callback = self.prev_page
                self.add_item(btn_prev)

        if len(self.data_list) > end:
                btn_next = discord.ui.Button(label="下一頁 ❯", style=discord.ButtonStyle.gray, row=1)
                btn_next.callback = self.next_page
                self.add_item(btn_next)
        
    
    async def prev_page(self, interaction: discord.Interaction):
        new_view = ViewPageSelect(self.cog, self.data_list, page=self.page - 1)
        await interaction.response.edit_message(embed=new_view.embed, view=new_view)

    async def next_page(self, interaction: discord.Interaction):
        new_view = ViewPageSelect(self.cog, self.data_list, page=self.page + 1)
        await interaction.response.edit_message(embed=new_view.embed, view=new_view)

    

class ItineraryDeleteView(discord.ui.View):
    def __init__(self, cog, data_list, page=0):
        super().__init__(timeout=None)
        self.cog = cog
        self.data_list = data_list
        self.page = page
        self.selected_index = None

        items_per_page = 10
        start = self.page * items_per_page
        end = start + items_per_page
        current_page_data = self.data_list[start:end]

        options = []
        for i in range(len(current_page_data)):
            actual_index = start + i + 1 
            label = current_page_data[i]
            
            options.append(discord.SelectOption(label=label[:100],value=str(actual_index)))

        if options:
            self.select = discord.ui.Select(
                placeholder=f"第 {self.page + 1} 頁：請選擇要刪除的行程",
                options=options,
                row=0
            )
            self.select.callback = self.select_callback
            self.add_item(self.select)

        if self.page > 0:
            btn_prev = discord.ui.Button(label="❮ 上一頁", style=discord.ButtonStyle.gray, row=1)
            btn_prev.callback = self.prev_page
            self.add_item(btn_prev)

        if len(self.data_list) > end:
            btn_next = discord.ui.Button(label="下一頁 ❯", style=discord.ButtonStyle.gray, row=1)
            btn_next.callback = self.next_page
            self.add_item(btn_next)
        
        self.add_item(BackToMainButton(self.cog.bot))

    async def select_callback(self, interaction: discord.Interaction):
        self.selected_index = int(self.select.values[0])
        
        confirm_view = ConfirmDeleteView(self.cog, self.selected_index, self.data_list[self.selected_index-1])
        
        await interaction.response.send_message(
            f"⚠️ 確定要刪除這筆嗎？\n> {self.data_list[self.selected_index-1]}", 
            view=confirm_view, 
            ephemeral=True
        )
    
    async def prev_page(self, interaction: discord.Interaction):
        new_view = ItineraryDeleteView(self.cog, self.data_list, page=self.page - 1)
        await interaction.response.edit_message(view=new_view)

    async def next_page(self, interaction: discord.Interaction):
        new_view = ItineraryDeleteView(self.cog, self.data_list, page=self.page + 1)
        await interaction.response.edit_message(view=new_view)

class ConfirmDeleteView(discord.ui.View):
    def __init__(self, cog, index, content_text):
        super().__init__(timeout=60)
        self.cog = cog
        self.index = index
        self.content_text = content_text

        self.add_item(BackToMainButton(self.cog.bot))

    @discord.ui.button(label="確認刪除", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def confirm_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        
        await interaction.response.defer(ephemeral=True)
        success, report_msg = await self.cog.delete_data(self.index)
        
        if success:
            await interaction.edit_original_response(content=report_msg, view=None)
        else:
            await interaction.followup.send(content=report_msg, ephemeral=True)

    @discord.ui.button(label="取消", style=discord.ButtonStyle.secondary)
    async def cancel_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="已取消刪除操作。", view=None)
    

class ItineraryDashboardView(ui.View):
    def __init__(self, bot, cog):
        super().__init__(timeout=None)
        self.bot = bot
        self.cog = cog
        self.add_item(BackToMainButton(self.bot))

    @ui.button(label="查看行程表", style=discord.ButtonStyle.success, emoji="📋", row=0)
    async def view_list(self, interaction: discord.Interaction, button: ui.Button):
        data_list = await self.cog.get_all_data()
        new_view = ViewPageSelect(self.cog, data_list)
        await interaction.response.edit_message(content=None, embed=new_view.embed, view=new_view)

    @ui.button(label="新增行程", style=discord.ButtonStyle.primary, emoji="➕", row=0)
    async def add_item_btn(self, interaction: discord.Interaction, button: ui.Button):
        new_view = ItineraryAddView(self.cog)
        embed = discord.Embed(title="➕ 新增行程", description="請選擇時間與優先級", color=0x3498db)
        await interaction.response.edit_message(content=None, embed=embed, view=new_view)

    @ui.button(label="刪除行程", style=discord.ButtonStyle.danger, emoji="🗑️", row=0)
    async def delete_item_btn(self, interaction: discord.Interaction, button: ui.Button):
        data_list = await self.cog.get_delete_list()
        new_view = ItineraryDeleteView(self.cog, data_list)
        await interaction.response.edit_message(content="請選擇要刪除的項目：", embed=None, view=new_view)