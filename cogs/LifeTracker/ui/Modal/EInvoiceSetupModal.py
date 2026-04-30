import discord
from cogs.BasicDiscordObject import ValidatedModal
from cogs.LifeTracker.utils import EInvoice_Manager
from cogs.LifeTracker.LifeTracker_config import MAX_PHONE_LENGTH,MAX_PASSWORD_LENGTH
class EInvoiceSetupModal(ValidatedModal, title="設定發票載具帳號"):
    phone = discord.ui.TextInput(
        label="手機號碼",
        placeholder="09開頭共10碼",
        max_length=MAX_PHONE_LENGTH,
        min_length=MAX_PHONE_LENGTH,
        required=True
    )
    
    password = discord.ui.TextInput(
        label="驗證碼 (密碼)",
        placeholder="請輸入財政部平台登入驗證碼",
        max_length=MAX_PASSWORD_LENGTH,
        required=True
    )

    def __init__(self, bot, category_id: int):
        super().__init__()
        self.bot = bot
        self.category_id = category_id

    async def execute_logic(self, interaction: discord.Interaction) -> str:
        phone_input = self.phone.value.strip()

        # 🌟 [新增] 手機號碼格式防呆驗證
        if not phone_input.isdigit():
            return "手機號碼格式錯誤：必須全部為數字！"
            
        if not phone_input.startswith("09"):
            return "手機號碼格式錯誤：必須以 09 開頭！"

        # 通過驗證，寫入資料庫
        success = EInvoice_Manager.save_config(
            user_id=interaction.user.id,
            phone=phone_input,
            raw_password=self.password.value
        )

        if not success:
            return "儲存發票設定時發生錯誤，請稍後再試或檢查輸入格式。"
            
        return None

    async def on_success(self, interaction: discord.Interaction):
        from cogs.LifeTracker.ui.View.EInvoicePlatformView import EInvoicePlatformView
        embed, view = EInvoicePlatformView.create_ui(self.bot, interaction.user.id, self.category_id)
        await interaction.response.edit_message(embed=embed, view=view)