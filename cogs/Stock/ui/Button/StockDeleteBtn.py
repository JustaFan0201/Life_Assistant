import discord
from cogs.BasicDiscordObject import SafeButton

class StockDeleteBtn(SafeButton):
    def __init__(self, bot):
        super().__init__(label="移除監控", style=discord.ButtonStyle.danger, emoji="🗑️", row=0)
        self.bot = bot

    async def do_action(self, interaction: discord.Interaction):
        try:
            from cogs.Stock.ui.View import StockDeleteView
            stock_cog = self.bot.get_cog("Stock")
            
            # 產生專屬的刪除畫面
            embed, view = StockDeleteView.create_ui(stock_cog, interaction.user.id)
            
            # 🌟 [修正] 動態判斷 Interaction 狀態，避免重複回應導致崩潰
            if not interaction.response.is_done():
                await interaction.response.edit_message(embed=embed, view=view)
            else:
                await interaction.edit_original_response(embed=embed, view=view)
            
        except Exception as e:
            print(f"❌ StockDeleteBtn 錯誤: {e}")
            
            # 🌟 錯誤處理也要加上狀態判斷
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ 無法切換至刪除畫面: {e}", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ 無法切換至刪除畫面: {e}", ephemeral=True)