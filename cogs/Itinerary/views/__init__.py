import discord
from datetime import datetime

class ItineraryButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
        # 定義在 self 裡，這就是「跨選單共用」的盒子
        self.new_data = {
            "year": None,
            "month": None,
            "date": None,
            "hour": None,
            "minute": None,
            "content": None
        }
