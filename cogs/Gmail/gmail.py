import discord
import os
import asyncio
from discord.ext import commands
from .views.gmail_view import EmailSendView
from .utils.gmail_tool import EmailTools 
from discord import app_commands

class Gmail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tools = EmailTools()

    @app_commands.command(name="寄送郵件", description="寄送Gmail信件") 
    async def send_email(self, interaction: discord.Interaction ):
        view = EmailSendView(cog=self)
        await interaction.response.send_modal(view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Gmail(bot))