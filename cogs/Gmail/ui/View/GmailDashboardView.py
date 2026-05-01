import discord
from cogs.BasicDiscordObject import LockableView

from cogs.Gmail.ui.Button.SetupMailBtn import SetupMailBtn
from cogs.Gmail.ui.Button.HelpBtn import HelpBtn
from cogs.Gmail.ui.Button.AddCategoryBtn import AddCategoryBtn
from cogs.Gmail.ui.Select.ViewCategorySelect import ViewCategorySelect
from cogs.Gmail.ui.Button.GoToDeleteCategoryBtn import GoToDeleteCategoryBtn
class GmailDashboardView(LockableView):
    def __init__(self, bot, gmail_cog, user_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.gmail_cog = gmail_cog
        self.user_id = user_id

        categories = self.gmail_cog.db_manager.get_user_categories(self.user_id)
        if categories:
            self.add_item(ViewCategorySelect(self.bot, self.gmail_cog, self.user_id, categories))

        self.add_item(AddCategoryBtn(self.gmail_cog, self.user_id))
        self.add_item(GoToDeleteCategoryBtn(self.bot, self.gmail_cog, self.user_id))
        self.add_item(SetupMailBtn(self.gmail_cog))
        self.add_item(HelpBtn())


        try:
            from cogs.System.ui.Button.BackToMainButton import BackToMainButton
            self.add_item(BackToMainButton(self.bot, row=4))
        except: pass

    @staticmethod
    def create_ui(bot, gmail_cog, user_id):
        user_config = gmail_cog.db_manager.get_user_config(user_id)
        last_id = user_config.get('last_email_id') if user_config else "尚未設置"
        
        categories = gmail_cog.db_manager.get_user_categories(user_id)

        embed = discord.Embed(
            title="📧 Gmail 郵件管理中心",
            description=(
                "💡 透過 AI 自動幫你把繁雜的信件分門別類！\n"
                "你可以點擊「新增分類」來建立自訂規則。"
            ),
            color=0xEA4335
        )
        embed.add_field(name="📡 狀態", value="🟢 運作中", inline=True)
        embed.add_field(name="📧 信箱", value=f"`{user_config.get('email')}`" if user_config else "尚未設置", inline=True)
        
        view = GmailDashboardView(bot, gmail_cog, user_id)
        return embed, view