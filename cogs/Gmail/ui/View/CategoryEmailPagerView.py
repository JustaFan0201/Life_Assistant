import discord
from email.utils import parsedate_to_datetime

from cogs.Gmail.ui.Button import PrevPageBtn,NextPageBtn,BackToGmailDashboardBtn

class CategoryEmailPagerView(discord.ui.View):
    def __init__(self, user_id, category_name, emails, page=0):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.category_name = category_name
        self.emails = emails
        self.page = page
        self.max_page = max(0, (len(emails) - 1) // 10)

        self._add_buttons()

    def _add_buttons(self):
        self.add_item(PrevPageBtn(disabled=(self.page == 0)))
        self.add_item(NextPageBtn(disabled=(self.page >= self.max_page)))
        self.add_item(BackToGmailDashboardBtn(self.user_id))

    def _format_date(self, raw_date):
        """🌟 內部工具：將 Email 原始日期字串轉換為乾淨的格式"""
        try:
            if not raw_date or raw_date == "未知時間":
                return "未知時間"
            
            # 將 "Fri, 8 May 2026 16:09:09 +0800" 轉成 datetime 物件
            dt = parsedate_to_datetime(raw_date)
            
            # 格式化為你喜歡的樣子，例如 2026/05/08 16:09
            return dt.strftime("%Y/%m/%d %H:%M")
        except Exception:
            return raw_date

    def generate_embed(self):
        embed = discord.Embed(title=f"📂 分類信件：{self.category_name}", color=0xEA4335)
        if not self.emails:
            embed.description = "這個分類目前還沒有任何信件喔！"
            return embed

        start_idx = self.page * 10
        end_idx = start_idx + 10
        page_emails = self.emails[start_idx:end_idx]

        for i, email in enumerate(page_emails, 1):
            link_text = f" [🔗 Gmail連結]({email['link']})" if email['link'] else ""
            
            clean_date = self._format_date(email['date'])
            
            embed.add_field(
                name=f"{start_idx + i}. {email['subject']}",
                value=f"✨ **AI摘要:** {email['summary']}\n📅 `{clean_date}`{link_text}",
                inline=False
            )
            
        embed.set_footer(text=f"第 {self.page + 1} / {self.max_page + 1} 頁 | 共 {len(self.emails)} 封")
        return embed