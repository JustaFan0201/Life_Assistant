import discord
from datetime import datetime

class ItineraryButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
        self.new_data = {
            "year": None,
            "month": None,
            "date": None,
            "hour": None,
            "minute": None,
            "content": None
        }
