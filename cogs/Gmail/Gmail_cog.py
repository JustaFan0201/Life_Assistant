# cogs/Gmail/Gmail_cog.py
from discord.ext import commands, tasks
from cogs.Gmail.utils import EmailDatabaseManager,EmailTools
from cogs.Gmail.utils import Gmail_AI_Analyzer
from database.models import EmailConfig


class Gmail(commands.Cog):
    def __init__(self, bot, db_session):
        self.bot = bot
        self.db_manager = EmailDatabaseManager(db_session)

    async def cog_load(self):
        if not self.test_check_mail.is_running():
            self.test_check_mail.start()
            print("[Gmail] 背景收信排程已成功啟動！")

    @tasks.loop(seconds=30)
    async def test_check_mail(self):
        await self.bot.wait_until_ready()
        try:
            with self.db_manager.session() as session:
                user_ids = [c.user_id for c in session.query(EmailConfig.user_id).all()]
        except Exception as e:
            print(f"[資料庫輪詢] 查詢設定失敗: {e}")
            return

        if not user_ids:
            return

        for user_id in user_ids:
            try:
                user_config = EmailDatabaseManager.get_user_config(user_id)
                if not user_config: continue

                user_email = user_config['email']
                user_password = user_config['password']
                last_id = user_config['last_email_id']

                if not user_email or not user_password: continue

                tools = EmailTools(user_email, user_password)
                
                try:
                    new_emails, drift_fix_id = await tools.get_unread_emails(last_id)
                except Exception as fetch_error:
                    # 如果抓取失敗，印出錯誤並跳過此使用者
                    print(f"❌ [EmailTools] 使用者 {user_email} 抓取失敗: {fetch_error}")
                    continue 

                # 如果有校正 ID，且抓取過程沒崩潰才更新
                if drift_fix_id:
                    self.db_manager.update_last_email_id(user_id, drift_fix_id)
                    print(f"🔧 [自動修復] 使用者 {user_email} ID 校正為: {drift_fix_id}")
        
                if new_emails:
                    user_categories = EmailDatabaseManager.get_user_categories(user_id)

                    for email_info in new_emails:
                        print(f"🔍 分析信件：{email_info['subject']} ...")
                        
                        # AI 分析
                        cat_name, summary = await Gmail_AI_Analyzer.analyze_and_classify_email(
                            subject=email_info['subject'],
                            body=email_info['body'],
                            categories=user_categories
                        )
                        
                        email_info['ai_summary'] = summary
                        email_info['category'] = cat_name

                        if cat_name:
                            target_cat = next((c for c in user_categories if c['name'] == cat_name), None)
                            if target_cat:
                                self.db_manager.save_categorized_email(target_cat['id'], email_info, summary)
                                print(f"📁 歸檔至 [{cat_name}]")
                        else:
                            print(f"⏩ 未符合分類，略過。")

                        self.db_manager.update_last_email_id(user_id, str(email_info['id']))
                    
            except Exception as e:
                print(f"⚠️ [輪詢異常] 使用者 {user_id} 發生未知錯誤: {e}")
