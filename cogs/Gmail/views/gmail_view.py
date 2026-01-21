import discord

class EmailSendView(discord.ui.Modal, title = '寄件設定'):
    to_input = discord.ui.TextInput(label='收件人gmail (必填)', placeholder='example@gmail.com')
    subject_input = discord.ui.TextInput(label='主旨 (建議填寫)', placeholder="請輸入主旨", required=False)
    content_input = discord.ui.TextInput(label='信件內容', placeholder="請輸入內容", style=discord.TextStyle.paragraph)

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data = {
            'to': self.to_input.value,
            'subject': self.subject_input.value,
            'content': self.content_input.value
        }
        
        success, report = await self.cog.tools.send_mail(data)

        if success:
            await interaction.followup.send(f"✅ {report}", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ {report}", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        import traceback
        traceback.print_exc() 
        
        if interaction.response.is_done():
            await interaction.followup.send('發生意外錯誤，請查看主機後台。', ephemeral=True)
        else:
            await interaction.response.send_message('發生意外錯誤，請通知管理員。', ephemeral=True)