# cogs\Itinerary\ui\Button\DeleteItemBtn.py
import discord
from cogs.BasicDiscordObject import SafeButton

class DeleteItemBtn(SafeButton):
    def __init__(self, parent_view):
        super().__init__(
            label="刪除行程", 
            style=discord.ButtonStyle.danger, 
            emoji="🗑️"
        )
        self.parent_view = parent_view

    async def do_action(self, interaction: discord.Interaction):
        cog = self.parent_view.cog
        
        try:
            from ..View.ItineraryDeleteView import ItineraryDeleteView
            
            embed, view = ItineraryDeleteView.create_ui(cog, interaction.user.id)
            
            if not interaction.response.is_done():
                await interaction.response.edit_message(content=None, embed=embed, view=view)
            else:
                await interaction.edit_original_response(content=None, embed=embed, view=view, attachments=[])
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            
            if self.view and hasattr(self.view, 'unlock_all'):
                await self.view.unlock_all(interaction)
            await interaction.followup.send(f"⚠️ 無法開啟刪除畫面：{e}", ephemeral=True)