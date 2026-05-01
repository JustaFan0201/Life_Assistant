import discord
from discord import ui

class GoToDeleteCategoryBtn(ui.Button):
    def __init__(self, bot, gmail_cog, user_id):
        super().__init__(label="刪除分類", style=discord.ButtonStyle.danger, emoji="🗑️", row=1)
        self.bot = bot
        self.gmail_cog = gmail_cog
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        categories = self.gmail_cog.db_manager.get_user_categories(self.user_id)
        
        # 🌟 無痕更新防呆：如果沒分類可以刪，直接改寫目前的 embed 提示他
        if not categories:
            embed = interaction.message.embeds[0]
            embed.description = "⚠️ **目前沒有任何分類可以刪除喔！**\n\n" + (embed.description or "")
            await interaction.response.edit_message(embed=embed, view=self.view)
            return
        
        # 切換到刪除專屬畫面
        from cogs.Gmail.ui.View.DeleteCategoryView import DeleteCategoryView
        embed, view = DeleteCategoryView.create_ui(self.bot, self.gmail_cog, self.user_id, categories)
        await interaction.response.edit_message(embed=embed, view=view)