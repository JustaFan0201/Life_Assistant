# cogs\Itinerary\ui\View\ItineraryDeleteView.py
import discord
from cogs.BasicDiscordObject import LockableView
from cogs.Itinerary.ui.Select.DeleteSelect import DeleteSelect

class ItineraryDeleteView(LockableView):
    def __init__(self, cog, user_id, page=0, selected_event_id=None):
        super().__init__(timeout=None)
        self.cog = cog
        self.user_id = user_id
        self.page = page
        
        self.selected_event_id = selected_event_id
        
        formatted = self.cog.SessionLocal.get_formatted_list(user_id)
        start, end = page * 10, (page + 1) * 10
        current_data = formatted[start:end]

        # 1. 產生下拉選單 (Row 0)
        if current_data:
            options = [
                discord.SelectOption(
                    label=d['display'][:100], 
                    value=str(d['id']),
                    default=(str(d['id']) == str(self.selected_event_id)) # 確保翻頁或重整時保留狀態
                ) for d in current_data
            ]
            self.add_item(DeleteSelect(self, options))

        # 2. 翻頁按鈕 (Row 1)
        if formatted:
            from cogs.Itinerary.ui.Button.PrevPageBtn import PrevPageBtn
            from cogs.Itinerary.ui.Button.NextPageBtn import NextPageBtn
            
            max_page = max(0, (len(formatted) - 1) // 10)
            
            prev_btn = PrevPageBtn(self)
            prev_btn.disabled = (page == 0)
            self.add_item(prev_btn)
            
            next_btn = NextPageBtn(self)
            next_btn.disabled = (page >= max_page)
            self.add_item(next_btn)

        # 💡 3. 加入「確定刪除」按鈕 (Row 2)
        if current_data:
            from cogs.Itinerary.ui.Button.ConfirmDeleteBtn import ConfirmDeleteBtn
            confirm_btn = ConfirmDeleteBtn(self)
            # 如果沒有選中任何東西，按鈕就是灰色的
            confirm_btn.disabled = (self.selected_event_id is None)
            self.add_item(confirm_btn)

        # 4. 返回按鈕 (Row 2)
        try:
            from cogs.Itinerary.ui.Button.BackToItineraryDashboardBtn import BackToItineraryDashboardBtn
            self.add_item(BackToItineraryDashboardBtn(self.cog.bot, row=2))
        except ImportError: 
            pass

    @staticmethod
    def create_ui(cog, user_id, page=0):
        """💡 靜態生成入口"""
        formatted = cog.SessionLocal.get_formatted_list(user_id)
        
        if not formatted[page * 10 : (page + 1) * 10] and page > 0:
            page -= 1
        
        if not formatted:
            desc = (
                "您目前沒有任何已排定的行程可以刪除喔！\n"
                "快去點擊「新增行程」建立您的第一筆安排吧。"
            )
        else:
            desc = (
                "請從下方的下拉選單中，選擇您想要 **永久刪除** 的行程。\n\n"
                "💡 **操作提示：**\n"
                "• 點擊選單後，右下角的「確定刪除」按鈕會亮起。\n"
                "• ⚠️ 注意：刪除後資料將 **無法復原**。"
            )

        embed = discord.Embed(
            title="🗑️ 刪除行程管理",
            description=desc,
            color=discord.Color.red() 
        )
        
        if formatted:
            max_page = max(1, ((len(formatted) - 1) // 10) + 1)
            embed.set_footer(text=f"總計 {len(formatted)} 筆行程 | 目前頁數: {page + 1} / {max_page}")
        view = ItineraryDeleteView(cog, user_id, page)
        return embed, view