import discord
from discord import ui

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
        try:
            gmail_cog = self.bot.get_cog("Gmail")
            user_id = interaction.user.id
            
            if gmail_cog:
                from cogs.Gmail.ui.View.GmailDashboardView import GmailDashboardView
                embed, view = GmailDashboardView.create_ui(self.bot, gmail_cog, user_id)
                
                if not interaction.response.is_done():
                    await interaction.response.edit_message(embed=embed, view=view)
                else:
                    await interaction.edit_original_response(embed=embed, view=view)
            else:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ 錯誤：找不到 Gmail 模組。", ephemeral=True)
                else:
                    await interaction.followup.send("❌ 錯誤：找不到 Gmail 模組。", ephemeral=True)

        except Exception as e:
            
            error_msg = f"系統發生錯誤，請查看終端機日誌。({e})"
            if not interaction.response.is_done():
                await interaction.response.send_message(error_msg, ephemeral=True)
            else:
                await interaction.followup.send(error_msg, ephemeral=True)