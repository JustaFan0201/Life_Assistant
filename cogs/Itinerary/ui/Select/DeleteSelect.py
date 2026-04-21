import discord

class DeleteSelect(discord.ui.Select):
    def __init__(self, parent_view, options):
        self.parent_view = parent_view
        super().__init__(placeholder="選擇要刪除的行程", options=options)

    async def callback(self, interaction: discord.Interaction):
        from ..View.ConfirmDeleteView import ConfirmDeleteView
        event_id = int(self.values[0])
        await interaction.response.send_message(
            f"⚠️ 確定要刪除這筆行程嗎？", 
            view=ConfirmDeleteView(self.parent_view.cog, event_id), 
            ephemeral=True
        )