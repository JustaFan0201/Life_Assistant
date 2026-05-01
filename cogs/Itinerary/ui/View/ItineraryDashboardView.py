# cogs\Itinerary\ui\View\ItineraryDashboardView.py
import discord
from datetime import datetime
from cogs.BasicDiscordObject import LockableView
from cogs.Itinerary.utils.calendar_drawer import generate_month_calendar
from cogs.Itinerary import itinerary_config as conf

class ItineraryDashboardView(LockableView):
    def __init__(self, cog, user_id, month_offset=0, page=0, total_items=0):
        super().__init__(timeout=conf.TIMEOUT_VIEW_DEFAULT)
        self.cog = cog
        self.user_id = user_id
        self.month_offset = month_offset
        self.page = page
        
        # Row 0: 核心操作 (新增/刪除行程)
        from cogs.Itinerary.ui.Button.AddItemBtn import AddItemBtn
        from cogs.Itinerary.ui.Button.DeleteItemBtn import DeleteItemBtn
        self.add_item(AddItemBtn(self))
        self.add_item(DeleteItemBtn(self))

        # 💡 Row 1: 全新的月份下拉選單 (直接取代原本的兩個按鈕)
        from cogs.Itinerary.ui.Select.MonthSelect import MonthSelect
        self.add_item(MonthSelect(self))

        # Row 2: 清單翻頁 (有資料才顯示按鈕)
        if total_items > 0:
            from cogs.Itinerary.ui.Button.PrevPageBtn import PrevPageBtn
            from cogs.Itinerary.ui.Button.NextPageBtn import NextPageBtn
            
            max_page = max(0, (total_items - 1) // conf.ITEMS_PER_PAGE)
            
            prev_page_btn = PrevPageBtn(self, row=2)
            prev_page_btn.disabled = (page == 0)
            self.add_item(prev_page_btn)
            
            next_page_btn = NextPageBtn(self, row=2)
            next_page_btn.disabled = (page >= max_page)
            self.add_item(next_page_btn)

        # Row 3: 返回系統
        try:
            from cogs.System.ui.Button import BackToMainButton
            self.add_item(BackToMainButton(self.cog.bot, row=0))
        except ImportError:
            pass

    @staticmethod
    def create_ui(cog, user_id, month_offset=0, page=0):
        now = datetime.now(conf.TW_TZ)
        now_naive = now.replace(tzinfo=None)
        
        target_month = now.month + month_offset
        target_year = now.year + (target_month - 1) // 12
        target_month = (target_month - 1) % 12 + 1
        
        # 1. 撈出該月份所有行程並切片
        all_events = cog.db_manager.get_user_events(user_id)
        month_events = [ev for ev in all_events if ev.event_time.year == target_year and ev.event_time.month == target_month]
        
        total_items = len(month_events)
        start = page * conf.ITEMS_PER_PAGE
        end = (page + 1) * conf.ITEMS_PER_PAGE
        current_items = month_events[start:end]
        
        # 2. 生成月曆圖片
        event_days = list(set(ev.event_time.day for ev in month_events))
        img_buffer = generate_month_calendar(target_year, target_month, event_days)
        file = discord.File(fp=img_buffer, filename="calendar.png")

        # 3. 組裝清單 Embed
        desc_list = [
            f"📅 **目標時間：`{target_year} / {target_month:02d}`**",
            "💡 橘色圈圈代表當天有排程。點擊上方選單快速跳轉。",
            "──────────────────"
        ]
        
        if not month_events:
            desc_list.append("\n*📝 這個月份暫時沒有安排行程喔！*")
        else:
            for i, ev in enumerate(current_items, start + 1):
                time_str = ev.event_time.strftime("%d號 %H:%M")
                p_emoji = conf.PRIORITY_MAP.get(str(ev.priority), "🟢")
                privacy_emoji = conf.PRIVACY_MAP.get(ev.is_private, "🌍")
                
                summary = ev.description
                if len(summary) > conf.MAX_DESC_PREVIEW_LEN:
                    summary = summary[:conf.MAX_DESC_PREVIEW_LEN] + "..."
                    
                if ev.event_time < now_naive:
                    desc_list.append(f"{privacy_emoji}{p_emoji} **#{i}** | `~~{time_str}~~` - ~~{summary}~~ (已過期)")
                else:
                    desc_list.append(f"{privacy_emoji}{p_emoji} **#{i}** | `{time_str}` - {summary}")

        embed = discord.Embed(
            title="📔 個人行程看板",
            description="\n".join(desc_list),
            color=discord.Color.blue()
        )
        embed.set_image(url="attachment://calendar.png")
        
        max_page = max(1, ((total_items - 1) // 10) + 1) if total_items > 0 else 1
        embed.set_footer(text=f"第 {page + 1} / {max_page} 頁 | 當月共 {total_items} 筆行程 | 更新: {now.strftime('%H:%M')}")
        
        view = ItineraryDashboardView(cog, user_id, month_offset, page, total_items)
        return embed, view, file