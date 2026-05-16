import discord
from discord import ui
import traceback

class GoToGmailButton(ui.Button):
    def __init__(self, bot):
        super().__init__(
            label="郵件管理", 
            style=discord.ButtonStyle.primary,
            emoji="📧",
            row=0 
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            from cogs.Gmail.ui.View.GmailDashboardView import GmailDashboardView
            
            embed, view = GmailDashboardView.create_ui(interaction.user.id)

            await interaction.edit_original_response(embed=embed, view=view)

        except Exception as e:
            print(f"❌ Gmail 儀表板跳轉失敗: {e}")
            traceback.print_exc()
            
            await interaction.followup.send(f"❌ 系統發生錯誤，請查看終端機日誌。({e})", ephemeral=True)