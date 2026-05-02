import discord
from discord import ui
from cogs.Gmail.ui.Select.DeleteCategorySelect import DeleteCategorySelect
from cogs.Gmail.ui.Button.BackToGmailDashboardBtn import BackToGmailDashboardBtn
class DeleteCategoryView(ui.View):
    def __init__(self, bot, gmail_cog, user_id, categories):
        super().__init__(timeout=None)
        self.bot = bot
        self.gmail_cog = gmail_cog
        self.user_id = user_id
        
        self.add_item(DeleteCategorySelect(self.bot, self.gmail_cog, self.user_id, categories))
        self.add_item(BackToGmailDashboardBtn(self.bot, self.gmail_cog, self.user_id))


    @staticmethod
    def create_ui(bot, gmail_cog, user_id, categories):
        embed = discord.Embed(
            title="🗑️ 刪除郵件分類",
            description="⚠️ **警告：** 刪除分類後，**該分類下所有由 AI 整理的信件紀錄也會一併刪除**（不會刪除您真實信箱的信）。\n請從下方選單選擇要移除的分類。",
            color=0xED4245 # 使用危險的紅色
        )
        view = DeleteCategoryView(bot, gmail_cog, user_id, categories)
        return embed, view