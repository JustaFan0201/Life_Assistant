import discord
import os
import asyncio
import aioimaplib
from discord.ext import commands, tasks
from .views.gmail_view import EmailSendView, EmailReplyModal, NewEmailNotificationView
from .utils.gmail_tool import EmailTools 
from discord import app_commands

class Gmail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tools = EmailTools()
        channel_id = os.getenv("DISCORD_NOTIFY_CHANNEL_ID")
        self.notify_channel_id = int(channel_id) if channel_id else None 
        self.last_email_id = None   

    
    async def cog_load(self):
        if not self.test_check_mail.is_running():
            self.test_check_mail.start()

    @app_commands.command(name="寄送郵件", description="寄送Gmail信件") 
    async def send_email(self, interaction: discord.Interaction ):
        view = EmailSendView(cog=self)
        await interaction.response.send_modal(view)

    @tasks.loop(seconds=30)
    async def test_check_mail(self):
        await self.bot.wait_until_ready()
        new_emails = await self.tools.get_unread_emails(self.last_email_id)
        
        if new_emails:
            for email_info in new_emails:
                if self.last_email_id is not None:
                    print(f"測試用:發現新郵件: {email_info['subject']}")
                    await self.send_inbox_notification(email_info)

                self.last_email_id = email_info['id']
            
    async def send_inbox_notification(self, info):
        channel = self.bot.get_channel(self.notify_channel_id)
        if not channel: return

        embed = discord.Embed(
            title="📬 收到新郵件！",
            description=f"**主旨:** {info['subject']}",
            color=0xEA4335
        )
        
        embed.add_field(name="👤 寄件者", value=f"`{info['from']}`", inline=False)
        
        content = info['body'] if info['body'] else "（無文字內容）"
        embed.add_field(name="📝 內容摘要", value=f"```\n{content}\n```", inline=False)
        
        if info.get('date'):
            embed.set_footer(text=f"收信時間: {info['date']}")

        view = NewEmailNotificationView(self, info)
        await channel.send(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(Gmail(bot))