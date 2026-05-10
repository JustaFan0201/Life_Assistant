import discord
from discord import ui

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

        Itinerary_cog = self.bot.get_cog("Itinerary") 
        user_id = interaction.user.id
        if not Itinerary_cog:
            return await interaction.followup.send("❌ 錯誤：找不到 Itinerary 模組。", ephemeral=True)

        try:
            embed, view, file = Itinerary_cog.create_itinerary_dashboard_ui(user_id)
            await interaction.edit_original_response(embed=embed, view=view, attachments=[file])
            
        except Exception as e:
            error_msg = f"系統發生錯誤，請查看終端機日誌。({e})"
            await interaction.followup.send(error_msg, ephemeral=True)