# cogs\Itinerary\ui\Select\AddSelects.py
import discord
from cogs.Itinerary import itinerary_config as conf
class SelectYear(discord.ui.Select):
    def __init__(self, parent_view):
        self.parent_view = parent_view
        current_year = parent_view.new_data["year"]
        
        # 💡 使用設定檔的年份範圍
        year_range = conf.ADD_YEAR_RANGE
        
        options = [
            discord.SelectOption(
                label=str(y), 
                value=str(y), 
                default=(str(y) == current_year)
            ) 
            for y in range(int(current_year), int(current_year) + year_range + 1)
        ]
        super().__init__(placeholder="選擇年份", row=0, options=options)
        
    async def callback(self, interaction: discord.Interaction):
        self.parent_view.new_data["year"] = self.values[0]
        await interaction.response.defer()

class SelectMonth(discord.ui.Select):
    def __init__(self, parent_view):
        self.parent_view = parent_view
        current_month = parent_view.new_data["month"]
        
        # 💡 自動根據 new_data 設定預設值
        options = [
            discord.SelectOption(
                label=f"{i}月", 
                value=str(i), 
                default=(str(i) == current_month)
            ) 
            for i in range(1, 13)
        ]
        super().__init__(placeholder="選擇月份", row=1, options=options)
        
    async def callback(self, interaction: discord.Interaction):
        self.parent_view.new_data["month"] = self.values[0]
        await interaction.response.defer()

class SelectPrivacy(discord.ui.Select):
    def __init__(self, parent_view):
        self.parent_view = parent_view
        # 預設為私人 (value="1")
        options = [
            discord.SelectOption(label="私人行程 (私訊提醒)", value="1", emoji="🔒", default=True),
            discord.SelectOption(label="公開行程 (頻道提醒)", value="0", emoji="🌍")
        ]
        super().__init__(placeholder="提醒模式", row=2, options=options)
        
    async def callback(self, interaction: discord.Interaction):
        self.parent_view.new_data["privacy"] = self.values[0]
        await interaction.response.defer()

class SelectPriority(discord.ui.Select):
    def __init__(self, parent_view):
        self.parent_view = parent_view
        # 預設為低 (value="2")
        options = [
            discord.SelectOption(label="緊急程度：高", value="0", emoji="🔴"),
            discord.SelectOption(label="緊急程度：中", value="1", emoji="🟡"),
            discord.SelectOption(label="緊急程度：低", value="2", emoji="🟢", default=True)
        ]
        super().__init__(placeholder="緊急程度", row=3, options=options)
        
    async def callback(self, interaction: discord.Interaction):
        self.parent_view.new_data["priority"] = self.values[0]
        await interaction.response.defer()