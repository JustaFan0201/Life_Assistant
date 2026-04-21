import discord
from cogs.BasicDiscordObject import SafeButton

class StockDeleteBtn(SafeButton):
    def __init__(self, bot):
        super().__init__(label="移除監控", style=discord.ButtonStyle.danger, emoji="🗑️", row=0)
        self.bot = bot

    async def do_action(self, interaction: discord.Interaction):
        try:
            from ...utils.Stock_Manager import Stock_Manager
            from ..Select.StockDeleteSelect import StockDeleteSelect
            
            stock_cog = self.bot.get_cog("Stock")
            stocks = Stock_Manager.get_user_stocks(stock_cog.db_manager, interaction.user.id)
            
            if not stocks:
                await interaction.followup.send("⚠️ 你的清單目前是空的。", ephemeral=True)
                return await self.view.unlock_all()

            view = discord.ui.View(timeout=60)
            view.add_item(StockDeleteSelect(self.bot, stocks, interaction)) 
            
            await interaction.followup.send("請選擇要移除的標的 (或點選取消)：", view=view, ephemeral=True)
            
            # 點完後立即解鎖主介面，讓使用者可以點其他按鈕
            await self.view.unlock_all()
            
        except Exception as e:
            print(f"❌ StockDeleteBtn 錯誤: {e}")
            await self.view.unlock_all()