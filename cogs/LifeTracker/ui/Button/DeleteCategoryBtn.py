import discord
from cogs.Base import SafeButton

class DeleteCategoryBtn(SafeButton):
    def __init__(self, bot, categories, label="", emoji="➖", row=1):
        super().__init__(label=label, style=discord.ButtonStyle.danger, emoji=emoji, row=row)
        self.bot = bot
        self.categories = categories

    async def do_action(self, interaction: discord.Interaction):
        if not self.categories:
            return await interaction.followup.send("❌ 目前沒有分類可以刪除。", ephemeral=True)
            
        from cogs.LifeTracker.ui.View.DeleteCategorySelectView import DeleteCategorySelectView
        embed = discord.Embed(
            title="⚠️ 刪除主分類",
            description="請從下方選單選擇要刪除的分類。\n**注意：這會連同該分類下的所有紀錄與標籤一併刪除！**",
            color=discord.Color.red()
        )
        await interaction.edit_original_response(embed=embed, view=DeleteCategorySelectView(self.bot, self.categories))