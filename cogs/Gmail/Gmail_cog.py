from discord.ext import commands, tasks
from cogs.Gmail.utils import EmailDatabaseManager, EmailTools
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
            # 目前資料庫中所有綁定信箱的使用者 ID
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
                if not user_config: 
                    continue

                user_email = user_config['email']
                user_password = user_config['password']
                last_id = user_config['last_email_id']

                if not user_email or not user_password: 
                    continue

                tools = EmailTools(user_email, user_password)
                
                try:
                    new_emails, drift_fix_id = await tools.get_unread_emails(last_id)
                except ValueError as ve:
                    # 處理驗證失敗
                    if str(ve) == "AUTH_FAILED":
                        print(f"[密碼錯誤] 使用者 {user_email} 驗證失敗。")
                        
                        # 發送私訊通知使用者
                        user = self.bot.get_user(int(user_id))
                        if user:
                            try:
                                msg = (
                                    f"⚠️ **Gmail 設定已被系統移除**\n"
                                    f"您先前綁定的帳號 `{user_email}` 登入失敗（帳號/密碼錯誤或授權失效）。\n"
                                    f"為了您的帳號安全，系統已**自動刪除**該筆錯誤的信箱設定。\n"
                                    f"請檢查您的「應用程式專用密碼」後，重新使用指令綁定以恢復功能。"
                                )
                                await user.send(msg)
                                print(f"已私訊通知使用者 {user_id}")
                            except Exception as dm_err:
                                print(f"無法私訊使用者 {user_id}: {dm_err}")
                        
                        # 資料庫刪除該筆錯誤
                        try:
                            with self.db_manager.session() as session:
                                config_to_delete = session.query(EmailConfig).filter_by(user_id=user_id).first()
                                if config_to_delete:
                                    session.delete(config_to_delete)
                                    session.commit()
                                    print(f"[資料刪除] 已強制移除使用者 {user_id} 的錯誤信箱設定")
                        except Exception as db_err:
                            print(f"刪除使用者資料庫紀錄時失敗: {db_err}")
                            
                        continue # 跳過該使用者後續的收信處理
                    raise ve
                
                except Exception as fetch_error:
                    # 處理一般連線錯誤（如網路不穩、逾時），單次跳過，不刪除資料
                    print(f"⚠️ [EmailTools] 使用者 {user_email} 暫時性抓取失敗: {fetch_error}")
                    continue 

                # 若有校正 ID
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

                        # 更新進度
                        self.db_manager.update_last_email_id(user_id, str(email_info['id']))
                    
            except Exception as e:
                print(f"⚠️ [輪詢異常] 使用者 {user_id} 發生未知錯誤: {e}")