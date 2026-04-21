import discord
from datetime import datetime, timezone, timedelta
from cogs.BasicDiscordObject import LockableView
from ..Select.AddSelects import SelectYear, SelectMonth, SelectPrivacy, SelectPriority
from ..Button.NextStepBtn import NextStepBtn

class ItineraryAddView(LockableView):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
        
        # 使用台灣時區 (UTC+8)
        tz_tw = timezone(timedelta(hours=8))
        now = datetime.now(tz_tw)
        
        self.new_data = {
            "year": str(now.year), 
            "month": str(now.month), 
            "day": str(now.day),
            "privacy": "1",
            "priority": "2" 
        }

        try:
            from cogs.System.ui.buttons import BackToMainButton
            self.add_item(BackToMainButton(self.cog.bot))
        except ImportError: pass

        self.add_item(SelectYear(self))
        self.add_item(SelectMonth(self))
        self.add_item(SelectPrivacy(self))
        self.add_item(SelectPriority(self))
        self.add_item(NextStepBtn(self))