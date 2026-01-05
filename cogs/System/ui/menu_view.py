import discord
from discord import ui
# 引入定義好的按鈕
from .buttons import FortuneButton, StatusButton, ChatButton, ToggleReplyButton

class MainControlView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        
        self.add_item(FortuneButton(bot))
        self.add_item(ChatButton(bot))
        
        self.add_item(ToggleReplyButton(bot))
        self.add_item(StatusButton(bot))