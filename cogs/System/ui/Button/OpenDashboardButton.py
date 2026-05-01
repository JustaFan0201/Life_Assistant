import discord
from discord import ui
import asyncio
from cogs.System.utils.System_manager import SystemManager

class OpenDashboardButton(ui.Button):
    def __init__(self, bot):
        super().__init__(
            label="開啟生活助手", 
            style=discord.ButtonStyle.primary,
            custom_id="sys_open_dashboard"
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        try:
            await asyncio.to_thread(SystemManager.register_user, user.id, user.name)
        except Exception as e:
            print(f"❌ 使用者註冊失敗: {e}")

        from cogs.System.ui.View import MainControlView
        
        embed, view = MainControlView.create_dashboard_ui(self.bot)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)