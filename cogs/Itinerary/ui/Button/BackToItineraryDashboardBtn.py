import discord
from cogs.BasicDiscordObject import SafeButton
from cogs.Itinerary.itinerary_cog import Itinerary

class BackToItineraryDashboardBtn(SafeButton):
    def __init__(self, label="返回行程看板", emoji="🔙", row=2):
        super().__init__(
            label=label, 
            style=discord.ButtonStyle.danger, 
            emoji=emoji, 
            row=row
        )

    async def do_action(self, interaction: discord.Interaction):
        try:
            embed, view, file = Itinerary.create_itinerary_dashboard_ui(interaction.user.id)

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