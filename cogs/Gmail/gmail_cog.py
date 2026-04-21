# cogs/Gmail/gmail_cog.py
import discord
import os
from discord.ext import commands, tasks
from .utils.gmail_tool import EmailTools 
from .utils.gmail_manager import EmailDatabaseManager, EmailConfig

class Gmail(commands.Cog):
    def __init__(self, bot, db_session):
        self.bot = bot
        self.SessionLocal = EmailDatabaseManager(db_session)
        
        channel_id = os.getenv("DISCORD_NOTIFY_CHANNEL_ID")
        self.notify_channel_id = int(channel_id) if channel_id else None 

    async def cog_load(self):
        if not self.test_check_mail.is_running():
            self.test_check_mail.start()

    @tasks.loop(seconds=30)
    async def test_check_mail(self):
        await self.bot.wait_until_ready()
        
        try:
            with self.SessionLocal.Session() as session:
                user_ids = [c.user_id for c in session.query(EmailConfig.user_id).all()]
        except Exception as e:
            print(f"[資料庫輪詢] 查詢設定失敗: {e}")
            return

        if not user_ids:
            return

        for user_id in user_ids:
            try:
                user_config = self.SessionLocal.get_user_config(user_id)

                if not user_config:
                    continue

                user_email = user_config['email']
                user_password = user_config['password']
                last_id = user_config['last_email_id']

                if not user_email or not user_password:
                    continue

                tools = EmailTools(user_email, user_password)
                new_emails = await tools.get_unread_emails(last_id)
                
                if new_emails:
                    for email_info in new_emails:
                        # 只有在 last_id 已經存在時（非首次初始化）才發送通知
                        if last_id is not None:
                            await self.send_private_notification(email_info, user_id)

                        # 無論如何都會更新最後的 ID
                        self.db_manager.update_last_email_id(user_id, str(email_info['id']))
                    
            except Exception as e:
                # 保留這個錯誤列印，萬一未來有問題才知道是哪個使用者卡住
                print(f"[輪詢錯誤] 使用者 {user_id}: {e}")

    async def send_private_notification(self, info, user_id):
        from .ui.View.NotificationView import NewEmailNotificationView
        from .gmail_config import MAX_EMAIL_BODY_LENGTH
        
        try:
            user = await self.bot.fetch_user(user_id)
            if not user: return

            embed = discord.Embed(
                title="📬 您有一封新郵件",
                description=f"**主旨:** {info['subject']}",
                color=0xEA4335
            )
            embed.add_field(name="👤 寄件者", value=f"`{info['from']}`", inline=False)
            
            content = info['body'] if info['body'] else "（無文字內容）"
            if len(content) > MAX_EMAIL_BODY_LENGTH:
                content = content[:MAX_EMAIL_BODY_LENGTH] + "..."
                
            embed.add_field(name="📝 內容摘要", value=f"```\n{content}\n```", inline=False)
            
            if info.get('date'):
                embed.set_footer(text=f"收信時間: {info['date']}")

            view = NewEmailNotificationView(self, info, user_id) 
            await user.send(embed=embed, view=view)
            
        except discord.Forbidden:
            print(f"❌ 無法私訊使用者 {user_id}。")
        except Exception as e:
            print(f"⚠️ 發送通知錯誤: {e}")

    def create_gmail_dashboard_ui(self, user_id):
        from .ui.View.GmailDashboardView import GmailDashboardView
        
        user_config = self.SessionLocal.get_user_config(user_id)
        last_id = user_config.get('last_email_id') if user_config else "尚未設置"

        embed = discord.Embed(
            title="📧 Gmail 郵件管理中心",
            description=(
                "點擊下方按鈕管理您的郵件與聯絡人。\n"
                "通知將透過**私訊**發送。\n\n"
                "💡 **首次使用？** 請點擊下方「使用教學」按鈕。"
            ),
            color=0xEA4335
        )
        embed.add_field(name="📡 狀態", value="🟢 運作中", inline=True)
        embed.add_field(name="🆔 最後同步 ID", value=f"`{last_id or '等待新郵件'}`", inline=True)
        
        view = GmailDashboardView(self.bot, self, user_id)
        return embed, view

async def setup(bot):
    session_factory = getattr(bot, "db_session", None)
    
    if session_factory is None:
        print("⚠️ 警告：機器人尚未初始化 db_session，Gmail 模組可能無法正常運作。")

    await bot.add_cog(Gmail(bot, session_factory))
    print("✅ Gmail 模組已成功載入並註冊至 Cog 列表")