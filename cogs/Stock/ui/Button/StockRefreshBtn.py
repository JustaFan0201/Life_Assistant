import discord
from cogs.BasicDiscordObject import SafeButton

class StockRefreshBtn(SafeButton):
    def __init__(self, bot):
        super().__init__(
            label="刷新現價損益", 
            style=discord.ButtonStyle.success, 
            emoji="🔄", 
            row=0
        )
        self.bot = bot

    async def do_action(self, interaction: discord.Interaction):
        """
        按下按鈕後執行的動作
        """
        # 取得 Stock Cog
        stock_cog = self.bot.get_cog("Stock")
        
        if stock_cog:
            await stock_cog.update_list_message(interaction, is_first=False)
        else:
            await interaction.followup.send("❌ 錯誤：找不到股票模組", ephemeral=True)
            # 發生錯誤解鎖按鈕，否則會卡住
            await self.view.unlock_all()