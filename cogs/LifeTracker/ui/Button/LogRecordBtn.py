import discord
from cogs.BasicDiscordObject import SafeButton
from cogs.LifeTracker.utils import LifeTracker_Manager

class LogRecordBtn(SafeButton):
    def __init__(self, bot, category_id, label="", emoji="➕", row=0):
        super().__init__(label=label, style=discord.ButtonStyle.success, emoji=emoji, row=row)
        self.bot = bot
        self.category_id = category_id

    async def do_action(self, interaction: discord.Interaction):
        cat_info, subcats_info = LifeTracker_Manager.get_category_details(self.category_id)
        if not cat_info:
            await interaction.followup.send("❌ 發生錯誤：找不到該分類資訊", ephemeral=True)
            return
            
        from cogs.LifeTracker.ui.View.LogRecordView import LogRecordView
        
        view = LogRecordView(self.bot, self.category_id, cat_info, subcats_info)
        embed, final_view = view.build_ui()
        
        await interaction.edit_original_response(embed=embed, view=final_view, attachments=[])