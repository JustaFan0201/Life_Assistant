import discord
from cogs.BasicDiscordObject import LockableView

from cogs.Gmail.ui.Button import AddCategoryBtn,GoToDeleteCategoryBtn,HelpBtn,SetupMailBtn
from cogs.Gmail.ui.Select import ViewCategorySelect
from cogs.Gmail.utils import EmailDatabaseManager
        
class GmailDashboardView(LockableView):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id

        categories = EmailDatabaseManager.get_user_categories(self.user_id)
        if categories:
            self.add_item(ViewCategorySelect(self.user_id, categories))

        self.add_item(AddCategoryBtn(self.user_id))
        self.add_item(GoToDeleteCategoryBtn(self.user_id))
        self.add_item(SetupMailBtn())
        self.add_item(HelpBtn(self.user_id))


        try:
            from cogs.System.ui.Button.BackToMainButton import BackToMainButton
            from bot import bot
            self.add_item(BackToMainButton(bot, row=4))
        except ImportError as e:
            print(f"無法載入 BackToMainButton: {e}")


    @staticmethod
    def create_ui(user_id):
        from cogs.Gmail.utils.Gmail_manager import EmailDatabaseManager
        user_config = EmailDatabaseManager.get_user_config(user_id)
        
        embed = discord.Embed(
            title="📧 Gmail 郵件管理中心",
            description=(
                "💡 透過 AI 自動幫你把繁雜的信件分門別類！\n"
                "你可以點擊「新增分類」來建立自訂規則。"
            ),
            color=0xEA4335
        )
        embed.add_field(name="📧 信箱", value=f"`{user_config.get('email')}`" if user_config else "尚未設置", inline=True)
        
        view = GmailDashboardView(user_id)
        return embed, view