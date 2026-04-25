import discord
from discord import ui
class DeleteCategoryBtn(ui.Button): 
    def __init__(self, bot, categories, label="刪除主分類", emoji="➖", row=1):
        super().__init__(label=label, style=discord.ButtonStyle.danger, emoji=emoji, row=row)
        self.bot = bot
        self.categories = categories

    async def callback(self, interaction: discord.Interaction):
        # 檢查邏輯
        if not self.categories:
            return await interaction.response.send_message("❌ 目前沒有分類可以刪除。", ephemeral=True)
            
        embed = discord.Embed(
            title="⚠️ 刪除主分類",
            description="請從下方選單選擇要刪除的分類。\n**注意：這會連同該分類下的所有紀錄與標籤一併刪除！**",
            color=discord.Color.red()
        )
        
        from cogs.LifeTracker.ui.View.DeleteCategorySelectView import DeleteCategorySelectView
        new_view = DeleteCategorySelectView(self.bot, self.categories)
        
        await interaction.response.edit_message(embed=embed, view=new_view)