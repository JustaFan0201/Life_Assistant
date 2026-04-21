# cogs/Gmail/ui/Select/ContactSelects.py
import discord
from ..Modal.SendMailModal import EmailSendModal

class RecipientSelect(discord.ui.Select):
    def __init__(self, cog, user_id):
        self.cog = cog
        self.user_id = user_id
        user_contacts = self.cog.db_manager.get_all_contacts(user_id)
        
        options = []
        if user_contacts:
            options = [discord.SelectOption(label=name, description=mail, value=mail) for name, mail in user_contacts.items()]
        else:
            options = [discord.SelectOption(label="目前無聯絡人", value="none")]
            
        super().__init__(placeholder="選擇常用聯絡人...", options=options, disabled=not user_contacts)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(EmailSendModal(self.cog, self.user_id, to_default=self.values[0]))

class ContactManageSelect(discord.ui.Select):
    def __init__(self, cog, user_id):
        self.cog = cog
        self.user_id = user_id
        user_contacts = self.cog.db_manager.get_all_contacts(user_id)
        
        options = [discord.SelectOption(label=name, description=mail, value=name) for name, mail in user_contacts.items()]
        super().__init__(placeholder="選擇聯絡人進行操作...", options=options)

    async def callback(self, interaction: discord.Interaction):
        from ..View.ContactViews import ContactActionView
        nickname = self.values[0]
        await interaction.response.edit_message(content=f"管理聯絡人：**{nickname}**", view=ContactActionView(self.cog, self.user_id, nickname))