import discord
from datetime import datetime
from cogs.BasicDiscordObject import LockableView
from cogs.Itinerary import itinerary_config as conf
class ItineraryAddView(LockableView):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog
        
        now = datetime.now(conf.TW_TZ)

        self.new_data = {
            "year": str(now.year), 
            "month": str(now.month), 
            "day": str(now.day),
            "privacy": "1",
            "priority": "2"
        }

        from cogs.Itinerary.ui.Select import SelectYear, SelectMonth, SelectPrivacy, SelectPriority
        from cogs.Itinerary.ui.Button import NextStepBtn

        self.add_item(SelectYear(self))
        self.add_item(SelectMonth(self))
        self.add_item(SelectPrivacy(self))
        self.add_item(SelectPriority(self))
        self.add_item(NextStepBtn(self))

        try:
            from cogs.Itinerary.ui.Button import BackToItineraryDashboardBtn
            self.add_item(BackToItineraryDashboardBtn(self.cog.bot, row=4))
        except ImportError: 
            pass

    @staticmethod
    def create_ui(cog):
        """💡 靜態生成入口"""
        embed = discord.Embed(
            title="➕ 建立新行程",
            description=(
                "請先選擇行程的 **時間與隱私設定**。\n\n"
                "1️⃣ 選擇年份、月份\n"
                "2️⃣ 設定隱私（私人/公開）\n"
                "3️⃣ 設定優先權（高/中/低）\n"
                "4️⃣ 點擊「下一步」填寫日期與內容"
            ),
            color=discord.Color.blue()
        )
        
        view = ItineraryAddView(cog)
        return embed, view