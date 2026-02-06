import discord
from discord import ui
import re
import json
from cogs.System.ui.buttons import BackToMainButton
from ..utils.gmail_tool import EmailTools



class GmailSetupModal(discord.ui.Modal, title="設置個人 Gmail 服務"):
    address = discord.ui.TextInput(
        label="Gmail 地址", 
        placeholder="example@gmail.com",
        min_length=5
    )
    password = discord.ui.TextInput(
        label="應用程式密碼 (App Password)", 
        placeholder="16 位數的應用程式密碼",
        style=discord.TextStyle.short
    )

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        clean_address = EmailTools()._extract_pure_email(self.address.value)
        report = self.cog.list_tools.save_user_config(
            interaction.user.id, 
            clean_address, 
            self.password.value
        )
        await interaction.followup.send(report, ephemeral=True)

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

        try:
            user_config = self.cog.list_tools.get_user_config(self.user_id)
            if not user_config:
                return await interaction.followup.send("❌ 您尚未設置個人信箱，請先點擊「設置個人信箱」。", ephemeral=True)

            clean_to = EmailTools()._extract_pure_email(self.to_input.value)
            data = {
                'to': clean_to,
                'subject': self.subject_input.value,
                'content': self.content_input.value
            }
            
            user_tools = EmailTools(user_config['email'], user_config['password'])
            success, report = await user_tools.send_mail(data)

            await interaction.followup.send(f"{'✅' if success else '❌'} {report}", ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"❌ 系統執行出錯: {e}", ephemeral=True)

class EmailReplyModal(discord.ui.Modal):
    content_input = discord.ui.TextInput(
        label='回覆內容',
        placeholder='請輸入您的回信內容...',
        style=discord.TextStyle.paragraph,
        required=True
    )

    def __init__(self, cog, user_id, receiver, original_subject):
        super().__init__(title=f"回覆：{receiver[:20]}...")
        self.cog = cog
        self.user_id = user_id
        self.receiver = receiver
        self.subject = f"Re: {original_subject}" if not original_subject.startswith("Re:") else original_subject

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        user_config = self.cog.list_tools.get_user_config(self.user_id)
        if not user_config:
            return await interaction.followup.send("❌ 找不到您的信箱設定。", ephemeral=True)
        
        clean_receiver = EmailTools()._extract_pure_email(self.receiver)

        data = {
            'to': clean_receiver,
            'subject': self.subject,
            'content': self.content_input.value
        }
        user_tools = EmailTools(user_config['email'], user_config['password'])
        success, report = await user_tools.send_mail(data)

        await interaction.followup.send(f"{'✅' if success else '❌'} {report}", ephemeral=True)

class AddEmailListView(discord.ui.Modal, title="新增常用聯絡人"):
    name_input = discord.ui.TextInput(label="聯絡人暱稱", placeholder="例如：小明", max_length=20)
    address_input = discord.ui.TextInput(label="Email 地址", placeholder="example@gmail.com")
    
    def __init__(self, cog, user_id):
        super().__init__()
        self.cog = cog
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        clean_address = EmailTools()._extract_pure_email(self.address_input.value)
        report = self.cog.list_tools.add_and_save(self.name_input.value, clean_address, self.user_id)
        await interaction.followup.send(report, ephemeral=True)

class EditEmailModal(discord.ui.Modal, title="修改聯絡人資料"):
    def __init__(self, cog, user_id, nickname):
        super().__init__()
        self.cog = cog
        self.user_id = user_id
        self.nickname = nickname
        self.email_input = discord.ui.TextInput(label=f"修改 {nickname} 的 Email", placeholder="新 Email 地址")
        self.add_item(self.email_input)

    async def on_submit(self, interaction: discord.Interaction):
        clean_address = EmailTools()._extract_pure_email(self.email_input.value)
        result = self.cog.list_tools.update_contact(self.user_id, self.nickname, clean_address)
        await interaction.response.send_message(result, ephemeral=True)

class NewEmailNotificationView(discord.ui.View):
    def __init__(self, cog, email_info, target_user_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.email_info = email_info
        self.target_user_id = target_user_id

    @discord.ui.button(label="快速回覆", style=discord.ButtonStyle.primary, emoji="✍️")
    async def reply_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target_user_id:
            return await interaction.response.send_message("⚠️ 這不是您的郵件，無法回覆。", ephemeral=True)
            
        modal = EmailReplyModal(self.cog, self.target_user_id, self.email_info['from'], self.email_info['subject'])
        await interaction.response.send_modal(modal)

class GmailDashboardView(ui.View):
    def __init__(self, bot, gmail_cog, user_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.gmail_cog = gmail_cog
        self.user_id = user_id

        buttons = [
            ("撰寫郵件", discord.ButtonStyle.primary, "✍️", self.send_callback),
            ("添加常用 Email", discord.ButtonStyle.primary, "➕", self.add_list_callback),
            ("管理聯絡人", discord.ButtonStyle.secondary, "⚙️", self.manage_callback),
            ("設置個人信箱", discord.ButtonStyle.success, "🔐", self.setup_callback)
        ]

        for label, style, emoji, callback in buttons:
            btn = ui.Button(label=label, style=style, emoji=emoji)
            btn.callback = callback
            self.add_item(btn)

        try:
            from cogs.System.ui.buttons import BackToMainButton
            self.add_item(BackToMainButton(self.bot))
        except:
            pass

    async def send_callback(self, interaction: discord.Interaction):
        view = RecipientSelectView(self.gmail_cog, self.user_id)
        await interaction.response.send_message("請選擇收件人：", view=view, ephemeral=True)

    async def add_list_callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(AddEmailListView(self.gmail_cog, self.user_id))

    async def manage_callback(self, interaction: discord.Interaction):
        db = self.gmail_cog.list_tools.read_db()
        if not db.get("data", {}).get(str(self.user_id)):
            return await interaction.response.send_message("您的聯絡人清單是空的。", ephemeral=True)
        await interaction.response.send_message("選擇要管理的聯絡人：", view=ContactManageView(self.gmail_cog, self.user_id), ephemeral=True)

    async def setup_callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(GmailSetupModal(self.gmail_cog))

class RecipientSelectView(discord.ui.View):
    def __init__(self, cog, user_id):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id
        db = self.cog.list_tools.read_db()
        user_contacts = db.get("data", {}).get(str(user_id), {})

        if user_contacts:
            options = [discord.SelectOption(label=name, description=mail, value=mail) for name, mail in user_contacts.items()]
            select = discord.ui.Select(placeholder="選擇常用聯絡人...", options=options)
            select.callback = self.select_callback
            self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(EmailSendView(self.cog, self.user_id, to_default=interaction.data['values'][0]))

    @discord.ui.button(label="直接手動輸入", style=discord.ButtonStyle.secondary)
    async def manual(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EmailSendView(self.cog, self.user_id))

class ContactManageView(discord.ui.View):
    def __init__(self, cog, user_id):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id
        db = self.cog.list_tools.read_db()
        user_contacts = db.get("data", {}).get(str(user_id), {})
        options = [discord.SelectOption(label=name, description=mail, value=name) for name, mail in user_contacts.items()]
        select = discord.ui.Select(placeholder="選擇聯絡人進行操作...", options=options)
        select.callback = self.manage_callback
        self.add_item(select)

    async def manage_callback(self, interaction: discord.Interaction):
        nickname = interaction.data['values'][0]
        await interaction.response.edit_message(content=f"管理聯絡人：**{nickname}**", view=ContactActionView(self.cog, self.user_id, nickname))

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