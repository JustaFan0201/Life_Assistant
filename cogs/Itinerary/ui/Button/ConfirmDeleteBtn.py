# cogs\Itinerary\ui\Button\ConfirmDeleteBtn.py
import discord
from cogs.BasicDiscordObject import SafeButton

class ConfirmDeleteBtn(SafeButton):
    def __init__(self, parent_view):
        super().__init__(
            label="確定刪除", 
            style=discord.ButtonStyle.danger, 
            emoji="⚠️", 
            row=2, 
            disabled=True
        )
        self.parent_view = parent_view

    async def do_action(self, interaction: discord.Interaction):
        event_id = getattr(self.parent_view, 'selected_event_id', None)
        
        if not event_id:
            return await interaction.response.defer()

        success, msg = self.parent_view.cog.db_manager.delete_event_by_id(event_id, interaction.user.id)

        embed, view = self.parent_view.__class__.create_ui(
            self.parent_view.cog, 
            interaction.user.id, 
            self.parent_view.page
        )
        
        if success:
            embed.color = discord.Color.green()
            embed.title = "✅ 行程已成功刪除！"
        else:
            embed.color = discord.Color.red()
            embed.title = f"❌ 刪除失敗：{msg}"

        if not interaction.response.is_done():
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.edit_original_response(embed=embed, view=view, attachments=[])