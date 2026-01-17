import discord
from discord import ui
#從 System 模組引入返回主選單按鈕
from ...System.ui.buttons import BackToMainButton
# 引入定義好的按鈕
from .buttons import FortuneButton, ChatButton, ToggleReplyButton
#定義 GPT 模組的主要介面
class GPTDashboardView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        
        self.add_item(FortuneButton(bot))
        self.add_item(ChatButton(bot))
        self.add_item(ToggleReplyButton(bot))
        
        self.add_item(BackToMainButton(bot))