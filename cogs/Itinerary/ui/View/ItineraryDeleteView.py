import discord
from cogs.BasicDiscordObject import LockableView
from ..Select.DeleteSelect import DeleteSelect

class ItineraryDeleteView(LockableView):
    def __init__(self, cog, user_id, page=0):
        super().__init__(timeout=None)
        self.cog = cog
        self.user_id = user_id
        self.page = page
        
        formatted = self.cog.db_manager.get_formatted_list(user_id)
        start, end = page * 10, (page + 1) * 10
        current_data = formatted[start:end]

        if current_data:
            options = [discord.SelectOption(label=d['display'][:100], value=str(d['id'])) for d in current_data]
            self.add_item(DeleteSelect(self, options))

        try:
            from cogs.System.ui.buttons import BackToMainButton
            self.add_item(BackToMainButton(self.cog.bot))
        except ImportError: pass