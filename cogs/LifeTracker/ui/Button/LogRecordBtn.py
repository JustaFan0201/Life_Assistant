import discord
from discord import ui
from cogs.LifeTracker.utils import LifeTrackerDatabaseManager

class LogRecordBtn(ui.Button):
    def __init__(self, bot, category_id, label="", emoji="➕", row=0):
        super().__init__(label=label, style=discord.ButtonStyle.success, emoji=emoji, row=row)
        self.bot = bot
        self.category_id = category_id

    async def callback(self, interaction: discord.Interaction):
        cat_info, subcats_info = LifeTrackerDatabaseManager.get_category_details(self.category_id)
        if not cat_info:
            await interaction.response.send_message("❌ 發生錯誤：找不到該分類資訊", ephemeral=True)
            return
            
        from cogs.LifeTracker.ui.View import LogRecordView
        
        view = LogRecordView(self.bot, self.category_id, cat_info, subcats_info)
        embed, final_view = view.build_ui()
        
        await interaction.response.edit_message(embed=embed, view=final_view, attachments=[])