import discord
from cogs.BasicDiscordObject import SafeButton

class BackToItineraryDashboardBtn(SafeButton):
    def __init__(self, bot, label="返回行程看板", emoji="🔙", row=2):
        super().__init__(
            label=label, 
            style=discord.ButtonStyle.danger, 
            emoji=emoji, 
            row=row
        )
        self.bot = bot

    async def do_action(self, interaction: discord.Interaction):
        itinerary_cog = self.bot.get_cog("Itinerary")

        if not itinerary_cog:
            if self.view and hasattr(self.view, 'unlock_all'):
                await self.view.unlock_all(interaction)
            return await interaction.followup.send("❌ 錯誤：找不到 Itinerary 模組。", ephemeral=True)

        try:
            embed, view, file = itinerary_cog.create_itinerary_dashboard_ui(interaction.user.id)

            if not interaction.response.is_done():
                await interaction.response.edit_message(embed=embed, view=view, attachments=[file])
            else:
                await interaction.edit_original_response(embed=embed, view=view, attachments=[file])
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            
            if self.view and hasattr(self.view, 'unlock_all'):
                await self.view.unlock_all(interaction)
            await interaction.followup.send(f"❌ 返回失敗：{e}", ephemeral=True)