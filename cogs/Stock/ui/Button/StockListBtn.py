import discord
from cogs.BasicDiscordObject import SafeButton

class StockListBtn(SafeButton):
    def __init__(self, bot):
        super().__init__(
            label="詳細損益清單", 
            style=discord.ButtonStyle.success, 
            emoji="📋", 
            row=0
        )
        self.bot = bot

    async def do_action(self, interaction: discord.Interaction):
        stock_cog = self.bot.get_cog("Stock")
        if stock_cog:
            # SafeButton 已經執行了 lock_all (edit_message)
            # 所以 update_list_message 內部必須使用 edit_original_response
            await stock_cog.update_list_message(interaction, is_first=False)
        else:
            await interaction.response.send_message("❌ 找不到股票模組", ephemeral=True)
            await self.view.unlock_all()