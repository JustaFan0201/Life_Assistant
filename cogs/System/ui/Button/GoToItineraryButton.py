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
        itinerary_cog = self.bot.get_cog("Itinerary") 

        if not itinerary_cog:
            return await interaction.response.send_message("❌ 錯誤：找不到 Itinerary 模組。", ephemeral=True)

        try:
            embed, view, file = itinerary_cog.create_itinerary_dashboard_ui(interaction.user.id)

            if not interaction.response.is_done():
                await interaction.response.edit_message(embed=embed, view=view, attachments=[file])
            else:
                await interaction.edit_original_response(embed=embed, view=view, attachments=[file])
            
        except Exception as e:
            await interaction.response.send_message(f"❌ 跳轉失敗，原因：{e}", ephemeral=True)