import discord
from cogs.BasicDiscordObject import LockableView
from ..Button.ViewListBtn import ViewListBtn
from ..Button.AddItemBtn import AddItemBtn
from ..Button.DeleteItemBtn import DeleteItemBtn

class ItineraryDashboardView(LockableView):
    def __init__(self, bot, cog):
        super().__init__(timeout=None)
        self.bot = bot
        self.cog = cog
        
        try:
            from cogs.System.ui.buttons import BackToMainButton
            self.add_item(BackToMainButton(self.bot))
        except ImportError:
            pass

        self.add_item(ViewListBtn(self))
        self.add_item(AddItemBtn(self))
        self.add_item(DeleteItemBtn(self))