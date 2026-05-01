import discord
from discord import ui
from cogs.Gmail.gmail_config import EMBED_COLOR_HELP
class HelpBtn(ui.Button):
    def __init__(self):
        super().__init__(label="使用教學", style=discord.ButtonStyle.secondary, emoji="📖")

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📖 Gmail 設置教學", color=EMBED_COLOR_HELP)
        embed.add_field(name="1. 開啟兩步驗證", value="前往 [Google 安全設定](https://myaccount.google.com/security) 開啟兩步驗證。", inline=False)
        embed.add_field(name="2. 產生應用程式密碼", value="前往 [應用程式密碼](https://myaccount.google.com/apppasswords) 產生一組 16 位密碼並複製。", inline=False)
        embed.add_field(name="3. 進行綁定", value="點擊「🔐 設置個人信箱」並輸入帳號與 16 位密碼即可。", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)