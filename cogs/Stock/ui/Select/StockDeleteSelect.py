import discord
from discord import ui

class StockDeleteSelect(ui.Select):
    # 🌟 改為接收 parent_view
    def __init__(self, bot, stocks, parent_view):
        options = [
            discord.SelectOption(label=f"{s.stock_name} ({s.stock_symbol})", value=s.stock_symbol, emoji="📈")
            for s in stocks
        ]
        
        # 移除了原有的 cancel 選項，直接交給 BackBtn 處理返回
        super().__init__(placeholder="請選擇要移除的股票...", options=options, row=0)
        self.bot = bot
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            stock_cog = self.bot.get_cog("Stock")
            symbol = self.values[0]
            
            from cogs.Stock.utils.Stock_Manager import Stock_Manager
            # 執行刪除邏輯
            success, res_name = Stock_Manager.delete_stock(stock_cog.db_manager, interaction.user.id, symbol)
            
            # 🌟 刪除後，呼叫 parent_view 的靜態方法重新生成「刪除畫面」的最新狀態
            embed_new, view_new = self.parent_view.__class__.create_ui(stock_cog, interaction.user.id)
            
            if success:
                embed_new.title = "✅ 移除成功"
                embed_new.description = f"已成功移除 **{res_name} ({symbol})**。\n\n" + embed_new.description
                embed_new.color = discord.Color.green()
            else:
                embed_new.title = "❌ 移除失敗"
                embed_new.description = f"發生錯誤：{res_name}\n\n" + embed_new.description
                
            # 就地刷新畫面
            await interaction.edit_original_response(embed=embed_new, view=view_new)
                
        except Exception as e:
            print(f"❌ StockDeleteSelect 錯誤: {e}")
            await interaction.followup.send(f"❌ 執行錯誤: {e}", ephemeral=True)