import discord
from discord import ui

class EditSubcatSelect(ui.Select):
    def __init__(self, bot, category_id, subcats):
        self.bot = bot
        self.category_id = category_id
        self.subcats = subcats
        
        # 建立選項清單
        options = [
            discord.SelectOption(label=f"修改：{s['name']}", value=str(s['id']), emoji="📝") 
            for s in subcats
        ]
        
        super().__init__(
            placeholder="📝 請選擇要修改名稱的標籤...", 
            min_values=1, 
            max_values=1, 
            options=options[:25]
        )

    async def callback(self, interaction: discord.Interaction):
        subcat_id = int(self.values[0])
        # 找出原本的名稱傳給 Modal
        old_name = next(s['name'] for s in self.subcats if s['id'] == subcat_id)
        
        from cogs.LifeTracker.ui.Modal.EditSubcatNameModal import EditSubcatNameModal
        await interaction.response.send_modal(
            EditSubcatNameModal(self.bot, self.category_id, subcat_id, old_name)
        )