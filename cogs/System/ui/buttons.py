import discord
from discord import ui

from database.db import SessionLocal
from database.models import User
import asyncio

class OpenDashboardButton(ui.Button):
    def __init__(self, bot):
        super().__init__(
            label="開啟生活助手", 
            style=discord.ButtonStyle.primary, 
            emoji="🚀", 
            custom_id="sys_open_dashboard"
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        try:
            await asyncio.to_thread(self._register_user_db, user.id, user.name)
        except Exception as e:
            print(f"❌ 使用者註冊失敗: {e}")

        from .view import MainControlView
        
        embed, view = MainControlView.create_dashboard_ui(self.bot)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    def _register_user_db(self, discord_id, username):
        with SessionLocal() as db:
            user = db.query(User).filter(User.discord_id == discord_id).first()
            if not user:
                new_user = User(discord_id=discord_id, username=username)
                db.add(new_user)
                db.commit()
                print(f"🆕 [Button] 新使用者註冊: {username} ({discord_id})")
            else:
                if user.username != username:
                    user.username = username
                    db.commit()

# 返回主選單按鈕
class BackToMainButton(ui.Button):
    def __init__(self, bot):
        super().__init__(
            label="返回主選單",
            style=discord.ButtonStyle.secondary,
            row=4
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        from .view import MainControlView 
        embed, view = MainControlView.create_dashboard_ui(self.bot)
        await interaction.response.edit_message(embed=embed, view=view)
        
# 前往 GPT UI按鈕
class GoToGPTButton(ui.Button):
    def __init__(self, bot):
        super().__init__(
            label="AI 助手功能", 
            style=discord.ButtonStyle.primary, 
            emoji="🤖",
            row=0
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        from ...GPT.ui.view import GPTDashboardView
        
        embed = discord.Embed(
            title="🤖 AI 助手控制台",
            description="這裡集合了所有 GPT 相關功能，請選擇：",
            color=0x1abc9c
        )
        embed.add_field(name="功能列表", value="🔮 運勢\n💬 對話\n⚙️ 設定", inline=False)
        
        view = GPTDashboardView(self.bot)
        
        await interaction.response.edit_message(embed=embed, view=view)

'''class GoToTHSRButton(ui.Button):
    def __init__(self, bot):
        super().__init__(
            label="高鐵功能服務", 
            style=discord.ButtonStyle.primary, 
            emoji="🚄",
            row=0
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        from cogs.THSR.ui.view import THSR_DashboardView
        embed, view = THSR_DashboardView.create_dashboard_ui(self.bot)
        await interaction.response.edit_message(embed=embed, view=view)'''

class GoToItineraryButton(ui.Button):
    def __init__(self, bot):
        super().__init__(
            label="行程管理", 
            style=discord.ButtonStyle.primary, 
            emoji="📅",
            row=0
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        itinerary_cog = self.bot.get_cog("Itinerary") 

        if not itinerary_cog:
            return await interaction.response.send_message("❌ 錯誤：找不到 Itinerary 模組。", ephemeral=True)

        try:
            from cogs.Itinerary.views.itinerary_view import ItineraryDashboardView
            sub_view = ItineraryDashboardView(self.bot, itinerary_cog) 
            
            sub_embed = discord.Embed(
                title="📅 個人行程管理系統",
                description="您可以查看、新增或刪除您的行程。",
                color=0x3498db
            )
            
            await interaction.response.edit_message(embed=sub_embed, view=sub_view)
            
        except Exception as e:
            await interaction.response.send_message(f"跳轉失敗，原因：{e}", ephemeral=True)

class GoToGmailButton(ui.Button):
    def __init__(self, bot):
        super().__init__(
            label="郵件管理", 
            style=discord.ButtonStyle.primary,
            emoji="📧",
            row=0 
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        # 1. 獲取 Gmail Cog
        gmail_cog = self.bot.get_cog("Gmail")
        user_id = interaction.user.id
        
        if gmail_cog:
            # 2. 直接呼叫 Cog 裡面的 UI 產生器
            embed, view = gmail_cog.create_gmail_dashboard_ui(user_id)
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.response.send_message("❌ 錯誤：找不到 Gmail 模組。", ephemeral=True)

