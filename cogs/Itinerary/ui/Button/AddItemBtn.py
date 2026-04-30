# cogs\Itinerary\ui\Button\AddItemBtn.py
import discord
import traceback
from cogs.BasicDiscordObject import SafeButton

class AddItemBtn(SafeButton):
    def __init__(self, parent_view):
        super().__init__(
            label="新增行程", 
            style=discord.ButtonStyle.primary, 
            emoji="➕"
        )
        self.parent_view = parent_view

    async def do_action(self, interaction: discord.Interaction):
        cog = self.parent_view.cog
        
        try:
            from cogs.Itinerary.ui.View.ItineraryAddView import ItineraryAddView
            embed, view = ItineraryAddView.create_ui(cog)
            
            if not interaction.response.is_done():
                await interaction.response.edit_message(embed=embed, view=view)
            else:
                await interaction.edit_original_response(embed=embed, view=view, attachments=[])
                
        except Exception as e:
            print(f"❌ AddItemBtn 執行失敗:")
            traceback.print_exc()
            
            if self.view and hasattr(self.view, 'unlock_all'):
                await self.view.unlock_all(interaction)
                
            await interaction.followup.send(f"⚠️ 無法開啟新增畫面：{e}", ephemeral=True)