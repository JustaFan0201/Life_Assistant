import discord
from discord import ui
from ..View.ContactViews import ContactManageView

class ManageContactBtn(ui.Button):
    def __init__(self, cog, user_id):
        super().__init__(label="管理聯絡人", style=discord.ButtonStyle.secondary, emoji="⚙️")
        self.cog = cog
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        contacts = self.cog.db_manager.get_all_contacts(self.user_id)
        if not contacts:
            await interaction.response.send_message("您的聯絡人清單是空的。", ephemeral=True)
            return
        await interaction.response.send_message("選擇要管理的聯絡人：", view=ContactManageView(self.cog, self.user_id), ephemeral=True)