import discord

class SelectYear(discord.ui.Select):
    def __init__(self, parent_view):
        self.parent_view = parent_view
        current_year = parent_view.new_data["year"]
        
        options = [
            discord.SelectOption(label=str(y), value=str(y), default=(str(y) == current_year)) 
            for y in range(2026, 2029)
        ]
        super().__init__(placeholder="年分", row=0, options=options)
        
    async def callback(self, interaction):
        self.parent_view.new_data["year"] = self.values[0]
        await interaction.response.defer()

class SelectMonth(discord.ui.Select):
    def __init__(self, parent_view):
        self.parent_view = parent_view
        current_month = parent_view.new_data["month"]
        options = [
            discord.SelectOption(label=f"{i}月", value=str(i), default=(str(i) == current_month)) 
            for i in range(1, 13)
        ]
        super().__init__(placeholder="月分", row=1, options=options)
        
    async def callback(self, interaction):
        self.parent_view.new_data["month"] = self.values[0]
        await interaction.response.defer()

class SelectPrivacy(discord.ui.Select):
    def __init__(self, parent_view):
        self.parent_view = parent_view
        options = [
            discord.SelectOption(label="私人行程 (私訊提醒)", value="1", emoji="🔒"),
            discord.SelectOption(label="公開行程 (頻道提醒)", value="0", emoji="🌍")
        ]
        super().__init__(placeholder="提醒模式", row=2, options=options)
    async def callback(self, interaction):
        self.parent_view.new_data["privacy"] = self.values[0]
        await interaction.response.defer()

class SelectPriority(discord.ui.Select):
    def __init__(self, parent_view):
        self.parent_view = parent_view
        options = [
            discord.SelectOption(label="緊急程度：高", value="0", emoji="🔴"),
            discord.SelectOption(label="緊急程度：中", value="1", emoji="🟡"),
            discord.SelectOption(label="緊急程度：低", value="2", emoji="🟢")
        ]
        super().__init__(placeholder="緊急程度 (預設低)", row=3, options=options)
    async def callback(self, interaction):
        self.parent_view.new_data["priority"] = self.values[0]
        await interaction.response.defer()