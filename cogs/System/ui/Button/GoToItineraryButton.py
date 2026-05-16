import discord
from discord import ui
import traceback

class GoToItineraryButton(ui.Button):
    def __init__(self, bot):
        super().__init__(
            label="行程管理", 
            style=discord.ButtonStyle.primary, 
            emoji="📅",
            row=0
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            from cogs.Itinerary.ui.View.ItineraryDashboardView import ItineraryDashboardView
            
            embed, view, file = ItineraryDashboardView.create_ui(interaction.user.id)
            
            await interaction.edit_original_response(embed=embed, view=view, attachments=[file])
            
        except Exception as e:
            print(f"❌ 行程表跳轉失敗: {e}")
            traceback.print_exc()
            await interaction.followup.send(f"❌ 跳轉失敗，原因：{e}", ephemeral=True)