import discord
from discord import ui

# 從 System 模組引入返回主選單按鈕
from ...System.ui.buttons import BackToMainButton

# 引入定義好的 Ticket 功能按鈕
from .buttons import OpenTHSRQueryButton

# 定義 Ticket 模組的主要介面
class TicketDashboardView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        
        # 加入功能按鈕
        self.add_item(OpenTHSRQueryButton(bot))
        
        # 如果有其他 Ticket 功能，加在這裡
        # self.add_item(CheckPriceButton(bot))
        
        # 加入返回 System 主選單的按鈕
        self.add_item(BackToMainButton(bot))