import discord
from cogs.BasicDiscordObject import SafeButton

class StockDeleteBtn(SafeButton):
    def __init__(self, bot):
        super().__init__(label="移除監控", style=discord.ButtonStyle.danger, emoji="🗑️", row=0)
        self.bot = bot

    async def do_action(self, interaction: discord.Interaction):
        try:
            from cogs.Stock.ui.View import StockDeleteView
            
            embed, view = StockDeleteView.create_ui(self.bot, interaction.user.id)
            
            if not interaction.response.is_done():
                await interaction.response.edit_message(embed=embed, view=view)
            else:
                await interaction.edit_original_response(embed=embed, view=view)
            
        except Exception as e:
            print(f"❌ StockDeleteBtn 錯誤: {e}")
            
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ 無法切換至刪除畫面: {e}", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ 無法切換至刪除畫面: {e}", ephemeral=True)