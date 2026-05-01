import discord

# 🌟 引入剛剛寫好的三個獨立按鈕
from cogs.Gmail.ui.Button.PrevPageBtn import PrevPageBtn
from cogs.Gmail.ui.Button.NextPageBtn import NextPageBtn
from cogs.Gmail.ui.Button.BackToGmailDashboardBtn import BackToGmailDashboardBtn

class CategoryEmailPagerView(discord.ui.View):
    def __init__(self, bot, gmail_cog, user_id, category_name, emails, page=0):
        super().__init__(timeout=None)
        self.bot = bot
        self.gmail_cog = gmail_cog
        self.user_id = user_id
        self.category_name = category_name
        self.emails = emails
        self.page = page
        self.max_page = max(0, (len(emails) - 1) // 10)

        self._add_buttons()

    def _add_buttons(self):
        # 🌟 直接將外部引入的按鈕實例化並加入 View
        self.add_item(PrevPageBtn(disabled=(self.page == 0)))
        self.add_item(NextPageBtn(disabled=(self.page >= self.max_page)))
        self.add_item(BackToGmailDashboardBtn(self.bot, self.gmail_cog, self.user_id))

    def generate_embed(self):
        embed = discord.Embed(title=f"📂 分類信件：{self.category_name}", color=0xEA4335)
        if not self.emails:
            embed.description = "這個分類目前還沒有任何信件喔！"
            return embed

        start_idx = self.page * 10
        end_idx = start_idx + 10
        page_emails = self.emails[start_idx:end_idx]

        for i, email in enumerate(page_emails, 1):
            link_text = f" [🔗 直達 Gmail]({email['link']})" if email['link'] else ""
            embed.add_field(
                name=f"{start_idx + i}. {email['subject']}",
                value=f"✨ **AI摘要:** {email['summary']}\n📅 `{email['date']}`{link_text}",
                inline=False
            )
            
        embed.set_footer(text=f"第 {self.page + 1} / {self.max_page + 1} 頁 | 共 {len(self.emails)} 封")
        return embed