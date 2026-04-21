import discord
from datetime import datetime, timezone, timedelta
from cogs.BasicDiscordObject import LockableView
from ..Button.PrevPageBtn import PrevPageBtn
from ..Button.NextPageBtn import NextPageBtn

class ViewPageSelect(LockableView):
    def __init__(self, cog, user_id, page=0):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id
        self.page = page

        self.data_list = self.cog.db_manager.get_user_events(user_id)
        count = len(self.data_list)
        start, end = page * 10, (page + 1) * 10
        current_items = self.data_list[start:end]
        
        tz_tw = timezone(timedelta(hours=8))
        self.embed = discord.Embed(title="📅 您的行程表", color=0xE0A04A, timestamp=datetime.now(tz_tw))
        priority_map = {"0": "🔴", "1": "🟡", "2": "🟢"}

        if not current_items:
            self.embed.description = "目前沒有任何行程"
        else:
            for i, item in enumerate(current_items, start + 1):
                time_str = item.event_time.strftime("%Y-%m-%d %H:%M")
                
                privacy_emoji = "🔒" if item.is_private else "🌍"
                p_emoji = priority_map.get(str(item.priority), "🟢")

                self.embed.add_field(
                    name=f"{privacy_emoji}{p_emoji} #{i} | {time_str}",
                    value=item.description or "無內容",
                    inline=False
                )
            self.embed.set_footer(text=f"第 {page+1} 頁 | 共有 {count} 筆行程")

        try:
            from cogs.System.ui.buttons import BackToMainButton
            self.add_item(BackToMainButton(self.cog.bot))
        except ImportError: pass

        if self.page > 0:
            self.add_item(PrevPageBtn(self))
        if count > end:
            self.add_item(NextPageBtn(self))