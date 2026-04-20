# cogs/Gmail/ui/View/GmailDashboardView.py
import discord
from cogs.BasicDiscordObject import LockableView

from ..Button.SendMailBtn import SendMailBtn
from ..Button.AddContactBtn import AddContactBtn
from ..Button.ManageContactBtn import ManageContactBtn
from ..Button.SetupMailBtn import SetupMailBtn
from ..Button.HelpBtn import HelpBtn

class GmailDashboardView(LockableView):
    def __init__(self, bot, gmail_cog, user_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.gmail_cog = gmail_cog
        self.user_id = user_id

        self.add_item(SendMailBtn(self.gmail_cog, self.user_id))
        self.add_item(AddContactBtn(self.gmail_cog, self.user_id))
        self.add_item(ManageContactBtn(self.gmail_cog, self.user_id))
        self.add_item(SetupMailBtn(self.gmail_cog))
        self.add_item(HelpBtn())

        try:
            from cogs.System.ui.buttons import BackToMainButton
            self.add_item(BackToMainButton(self.bot))
        except: pass