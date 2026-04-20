import discord
from cogs.BasicDiscordObject import LockableView
from ..Button.ConfirmDeleteBtn import ConfirmDeleteBtn

class ConfirmDeleteView(LockableView):
    def __init__(self, cog, event_id):
        super().__init__(timeout=60)
        self.cog = cog
        self.event_id = event_id

        self.add_item(ConfirmDeleteBtn(self))