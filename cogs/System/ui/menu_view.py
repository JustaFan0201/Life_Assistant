import discord
from discord import ui
#記得引入定義的按鈕
from .buttons import GoToGPTButton, StatusButton, GoToTHSRButton
#顯示主介面的按鈕 會需要新增前往想去的其他UI按鈕
class MainControlView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        
        self.add_item(GoToGPTButton(bot))
        self.add_item(GoToTHSRButton(bot))
        self.add_item(StatusButton(bot))