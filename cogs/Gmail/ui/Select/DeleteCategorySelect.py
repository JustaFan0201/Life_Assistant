import discord
from discord import ui

class DeleteCategorySelect(ui.Select):
    def __init__(self, bot, gmail_cog, user_id, categories):
        self.bot = bot
        self.gmail_cog = gmail_cog
        self.user_id = user_id
        self.categories_map = {str(c['id']): c['name'] for c in categories}
        
        options = [discord.SelectOption(label=f"刪除: {c['name']}", value=str(c['id']), emoji="🗑️") for c in categories]
        super().__init__(placeholder="請選擇要永久刪除的分類...", min_values=1, max_values=1, options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        category_id = int(self.values[0])
        category_name = self.categories_map[str(category_id)]
        
        # 執行刪除
        success = self.gmail_cog.db_manager.delete_category(category_id)
        
        # 準備跳回主控台
        from cogs.Gmail.ui.View.GmailDashboardView import GmailDashboardView
        embed, view = GmailDashboardView.create_ui(self.bot, self.gmail_cog, self.user_id)
        
        # 🌟 無痕狀態更新：把刪除結果直接寫進主控台的簡介中
        if success:
            embed.description = f"🗑️ **已成功刪除分類：{category_name}**\n*(附帶的信件紀錄也已清除)*\n\n" + embed.description
        else:
            embed.description = f"❌ **刪除失敗，該分類可能已不存在。**\n\n" + embed.description
            
        await interaction.response.edit_message(embed=embed, view=view)