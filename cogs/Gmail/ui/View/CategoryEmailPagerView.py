import discord

class CategoryEmailPagerView(discord.ui.View):
    def __init__(self, bot, gmail_cog, user_id, category_name, emails, page=0):
        super().__init__(timeout=None)
        self.bot = bot
        self.gmail_cog = gmail_cog
        self.user_id = user_id
        self.category_name = category_name
        self.emails = emails
        self.page = page
        # 計算最大頁數 (0-indexed)
        self.max_page = max(0, (len(emails) - 1) // 10)

        self._add_buttons()

    def _add_buttons(self):
        # 翻頁按鈕的邏輯控制
        prev_btn = discord.ui.Button(label="◀ 上一頁", style=discord.ButtonStyle.primary, disabled=(self.page == 0))
        prev_btn.callback = self.go_prev
        self.add_item(prev_btn)

        next_btn = discord.ui.Button(label="下一頁 ▶", style=discord.ButtonStyle.primary, disabled=(self.page >= self.max_page))
        next_btn.callback = self.go_next
        self.add_item(next_btn)

        back_btn = discord.ui.Button(label="返回管理中心", style=discord.ButtonStyle.danger)
        back_btn.callback = self.go_back
        self.add_item(back_btn)

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

    async def go_prev(self, interaction: discord.Interaction):
        self.page -= 1
        self.clear_items()
        self._add_buttons()
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

    async def go_next(self, interaction: discord.Interaction):
        self.page += 1
        self.clear_items()
        self._add_buttons()
        await interaction.response.edit_message(embed=self.generate_embed(), view=self)

    async def go_back(self, interaction: discord.Interaction):
        from .GmailDashboardView import GmailDashboardView
        embed, view = GmailDashboardView.create_ui(self.bot, self.gmail_cog, self.user_id)
        await interaction.response.edit_message(embed=embed, view=view)