import discord
from cogs.BasicDiscordObject import SafeButton

class ConfirmDeleteBtn(SafeButton):
    def __init__(self, parent_view):
        super().__init__(label="確認刪除", style=discord.ButtonStyle.danger, emoji="🗑️")
        self.parent_view = parent_view

    async def do_action(self, interaction: discord.Interaction):
        success, msg = self.parent_view.cog.db_manager.delete_event_by_id(
            self.parent_view.event_id, 
            interaction.user.id
        )
        # SafeButton 已經消耗了 response，使用 edit_original_response 刷新畫面
        await interaction.edit_original_response(content=msg, view=None)