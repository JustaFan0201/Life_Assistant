# cogs/Gmail/gmail_cog.py
import discord
import os
from discord.ext import commands, tasks
from cogs.Gmail.utils import EmailDatabaseManager,EmailTools
from cogs.System.utils import SystemManager
from cogs.Gmail.utils import Gmail_AI_Analyzer
from database.models import EmailConfig
class Gmail(commands.Cog):
    def __init__(self, bot, db_session):
        self.bot = bot
        self.db_manager = EmailDatabaseManager(db_session)

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
                user_config = self.db_manager.get_user_config(user_id)
                if not user_config: continue

                user_email = user_config['email']
                user_password = user_config['password']
                last_id = user_config['last_email_id']

                if not user_email or not user_password: continue

                tools = EmailTools(user_email, user_password)
                new_emails = await tools.get_unread_emails(last_id)
                
                if new_emails:
                    # 1. 收到新信！先撈出這個使用者設定了哪些分類
                    user_categories = self.db_manager.get_user_categories(user_id)

                    for email_info in new_emails:
                        print(f"🔍 正在呼叫 AI 分析信件：{email_info['subject']} ...")
                        
                        # 2. 呼叫 AI 大腦進行分類與摘要
                        cat_name, summary = await Gmail_AI_Analyzer.analyze_and_classify_email(
                            subject=email_info['subject'],
                            body=email_info['body'],
                            categories=user_categories
                        )
                        
                        # 把 AI 分析結果塞進 info 裡
                        email_info['ai_summary'] = summary
                        email_info['category'] = cat_name

                        # 3. 如果 AI 有成功配對到分類，寫入資料庫！
                        if cat_name:
                            target_cat = next((c for c in user_categories if c['name'] == cat_name), None)
                            if target_cat:
                                self.db_manager.save_categorized_email(target_cat['id'], email_info, summary)
                                print(f"📁 已將信件歸檔至分類 [{cat_name}]")

                        # 4. 無論如何都會更新最後的 ID (已移除私訊通知)
                        self.db_manager.update_last_email_id(user_id, str(email_info['id']))
                    
            except Exception as e:
                print(f"[輪詢錯誤] 使用者 {user_id}: {e}")
