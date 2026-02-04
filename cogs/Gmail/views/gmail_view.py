import discord
from discord import ui
#from .gmail_view import EmailSendView 
from cogs.System.ui.buttons import BackToMainButton

class EmailSendView(discord.ui.Modal, title='寄件設定'):
    def __init__(self, cog, user_id, to_default=""):
        super().__init__()
        self.cog = cog
        self.user_id = user_id

        self.to_input = discord.ui.TextInput(
            label='收件人gmail (必填)', 
            placeholder='example@gmail.com',
            default=to_default
        )
        self.subject_input = discord.ui.TextInput(
            label='主旨 (建議填寫)', 
            placeholder="請輸入主旨", 
            required=False
        )
        self.content_input = discord.ui.TextInput(
            label='信件內容', 
            placeholder="請輸入內容", 
            style=discord.TextStyle.paragraph
        )
        
        self.add_item(self.to_input)
        self.add_item(self.subject_input)
        self.add_item(self.content_input)

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
            await interaction.followup.send(f'發生意外錯誤：{error}', ephemeral=True)
        else:
            await interaction.response.send_message('發生意外錯誤，請通知管理員', ephemeral=True)

class EmailReplyModal(discord.ui.Modal):
    content_input = discord.ui.TextInput(
        label='回覆內容',
        placeholder='請輸入您的回信內容...',
        style=discord.TextStyle.paragraph,
        required=True
    )

    def __init__(self, cog, receiver, original_subject):
        super().__init__(title=f"回覆：{receiver[:20]}...")
        self.cog = cog
        self.receiver = receiver
        self.subject = f"Re: {original_subject}" if not original_subject.startswith("Re:") else original_subject

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        data = {
            'to': self.receiver,
            'subject': self.subject,
            'content': self.content_input.value
        }

        success, report = await self.cog.tools.send_mail(data)

        if success:
            await interaction.followup.send(f"✅ 已成功回覆至 {self.receiver}", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ 回覆失敗: {report}", ephemeral=True)

class NewEmailNotificationView(discord.ui.View):
    def __init__(self, cog, email_info):
        super().__init__(timeout=None)
        self.cog = cog
        self.email_info = email_info

    @discord.ui.button(label="快速回覆", style=discord.ButtonStyle.primary, emoji="✍️")
    async def reply_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = EmailReplyModal(
            cog=self.cog, 
            receiver=self.email_info['from'], 
            original_subject=self.email_info['subject']
        )
        await interaction.response.send_modal(modal)

class AddEmailListView(discord.ui.Modal, title="新增常用email地址"):

    name_input = discord.ui.TextInput(
        label="聯絡人暱稱", 
        placeholder="例如：小明、老闆",
        min_length=1,
        max_length=20
    )

    address_input = discord.ui.TextInput(
        label="請輸入email地址", 
        style=discord.TextStyle.short,
        placeholder="example@gmail.com"
    )
    
    def __init__(self, cog, user_id):
        super().__init__()
        self.cog = cog
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            name = self.name_input.value
            email_value = self.address_input.value
            
            report = self.cog.list_tools.add_and_save(name, email_value, self.user_id)
            await interaction.followup.send(report, ephemeral=True)
            
        except Exception as e:
            print(f"Modal 提交錯誤: {e}")
            await interaction.followup.send(f"處理失敗 請告知管理員：{e}")
    

class GmailDashboardView(ui.View):
    def __init__(self, bot, gmail_cog, user_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.gmail_cog = gmail_cog
        self.user_id = user_id

        send_btn = ui.Button(label="撰寫郵件", style=discord.ButtonStyle.primary, emoji="✍️")
        send_btn.callback = self.send_callback
        self.add_item(send_btn)

        add_list_btn = ui.Button(label="添加常發送的email", style=discord.ButtonStyle.primary, emoji="➕")
        add_list_btn.callback = self.add_list_callback
        self.add_item(add_list_btn)

        manage_btn = ui.Button(label="管理聯絡人", style=discord.ButtonStyle.secondary, emoji="⚙️")
        manage_btn.callback = self.manage_callback
        self.add_item(manage_btn)

        try:
            from cogs.System.ui.buttons import BackToMainButton
            self.add_item(BackToMainButton(self.bot))
        except ImportError:
            print("⚠️ [GmailDashboardView] 無法匯入 BackToMainButton")

    async def send_callback(self, interaction: discord.Interaction):
        view = RecipientSelectView(cog=self.gmail_cog, user_id=self.user_id)
        await interaction.response.send_message("請選擇收件人或直接撰寫：", view=view, ephemeral=True)

    async def add_list_callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(AddEmailListView(cog=self.gmail_cog, user_id =self.user_id))

    async def manage_callback(self, interaction: discord.Interaction):
        view = ContactManageView(self.gmail_cog, self.user_id)
        db = self.gmail_cog.list_tools.read_db()
        if not db.get("data", {}).get(str(self.user_id)):
            return await interaction.response.send_message("您的清單目前是空的喔！", ephemeral=True)
            
        await interaction.response.send_message("請選擇您要管理的聯絡人：", view=view, ephemeral=True)

class RecipientSelectView(discord.ui.View):
    def __init__(self, cog, user_id):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id

        db = self.cog.list_tools.read_db()
        user_contacts = db.get("data", {}).get(str(user_id), {})

        if user_contacts:
            options = [
                discord.SelectOption(label=name, description=mail, value=mail)
                for name, mail in user_contacts.items()
            ]
            
            select = discord.ui.Select(placeholder="選擇常用聯絡人...", options=options)
            select.callback = self.select_callback
            self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        email = interaction.data['values'][0]
        await interaction.response.send_modal(EmailSendView(self.cog, self.user_id, to_default=email))

    @discord.ui.button(label="直接手動輸入", style=discord.ButtonStyle.secondary)
    async def manual(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_modal(EmailSendView(self.cog, self.user_id))

class ContactManageView(discord.ui.View):
    def __init__(self, cog, user_id):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id
        self.setup_select()

    def setup_select(self):
        db = self.cog.list_tools.read_db()
        user_contacts = db.get("data", {}).get(str(self.user_id), {})

        if not user_contacts:
            return

        options = [
            discord.SelectOption(label=name, description=mail, value=name)
            for name, mail in user_contacts.items()
        ]
        
        select = discord.ui.Select(placeholder="選擇要管理的聯絡人...", options=options)
        select.callback = self.manage_callback
        self.add_item(select)

    async def manage_callback(self, interaction: discord.Interaction):
        nickname = interaction.data['values'][0]
        view = ContactActionView(self.cog, self.user_id, nickname)
        await interaction.response.edit_message(content=f"正在管理：**{nickname}**，請選擇操作：", view=view)

class ContactActionView(discord.ui.View):
    def __init__(self, cog, user_id, nickname):
        super().__init__()
        self.cog = cog
        self.user_id = user_id
        self.nickname = nickname

    @discord.ui.button(label="修改 Email", style=discord.ButtonStyle.primary, emoji="✏️")
    async def edit_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EditEmailModal(self.cog, self.user_id, self.nickname))

    @discord.ui.button(label="刪除聯絡人", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def delete_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = self.cog.list_tools.delete_contact(self.user_id, self.nickname)
        await interaction.response.edit_message(content=result, view=None)

class EditEmailModal(discord.ui.Modal, title="修改聯絡人資料"):
    def __init__(self, cog, user_id, nickname):
        super().__init__()
        self.cog = cog
        self.user_id = user_id
        self.nickname = nickname
        
        self.email_input = discord.ui.TextInput(
            label=f"修改 {nickname} 的 Email",
            placeholder="請輸入新的 Email 地址"
        )
        self.add_item(self.email_input)

    async def on_submit(self, interaction: discord.Interaction):
        result = self.cog.list_tools.update_contact(self.user_id, self.nickname, self.email_input.value)
        await interaction.response.send_message(result, ephemeral=True)
