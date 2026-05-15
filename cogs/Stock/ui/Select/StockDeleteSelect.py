import discord
from discord import ui
from cogs.Stock.utils import Stock_Manager

class StockDeleteSelect(ui.Select):
    def __init__(self, bot, stocks, parent_view):
        options = [
            discord.SelectOption(label=f"{s.stock_name} ({s.stock_symbol})", value=s.stock_symbol, emoji="📈")
            for s in stocks
        ]
        super().__init__(placeholder="請選擇要移除的股票...", options=options, row=0)
        self.bot = bot
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        try:
            symbol = self.values[0]
            
            success, res_name = Stock_Manager.delete_stock(interaction.user.id, symbol)
            
            from cogs.Stock.ui.View.StockDeleteView import StockDeleteView
            embed_new, view_new = StockDeleteView.create_ui(self.bot, interaction.user.id)
            
            if success:
                embed_new.title = "✅ 移除成功"
                embed_new.description = f"已成功從清單移除：**{res_name} ({symbol})**\n{'-'*30}\n{embed_new.description}"
                embed_new.color = discord.Color.green()
            else:
                embed_new.title = "❌ 移除失敗"
                embed_new.description = f"錯誤原因：{res_name}\n\n" + embed_new.description
                
            await interaction.edit_original_response(embed=embed_new, view=view_new)
                
        except Exception as e:
            print(f"❌ StockDeleteSelect 錯誤: {e}")
            await interaction.followup.send(f"❌ 執行錯誤: {e}", ephemeral=True)