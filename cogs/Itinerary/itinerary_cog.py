import discord
import os
from datetime import datetime, timezone, timedelta
from discord.ext import commands, tasks
from database.models import CalendarEvent, BotSettings
from .utils.calendar_manager import CalendarDatabaseManager

class Itinerary(commands.Cog):
    def __init__(self, bot, db_session):
        self.bot = bot
        
        self.db_session_maker = db_session
        self.db_manager = CalendarDatabaseManager(db_session)
        
        self.last_check_minute = -1
        self.check_reminders.start()

    @tasks.loop(seconds=10.0)
    async def check_reminders(self):
        await self.bot.wait_until_ready()
        
        # 取得當前台灣時間 (UTC+8)
        tz_tw = timezone(timedelta(hours=8))
        now_tw = datetime.now(tz_tw).replace(tzinfo=None, second=0, microsecond=0)
        
        if self.last_check_minute == now_tw.minute:
            return
        self.last_check_minute = now_tw.minute


        # 🌟 改用清理過名稱的 self.db_session_maker
        with self.db_session_maker() as session:
            try:
                # 找出符合當前台灣時間的行程
                events = session.query(CalendarEvent).filter(
                    CalendarEvent.event_time == now_tw
                ).all()

                if not events:
                    return
                settings = session.query(BotSettings).first() 
                for event in events:
                    try:
                        user = await self.bot.fetch_user(event.user_id)
                        if not user: continue

                        embed = discord.Embed(
                            title="📅 | 行程提醒",
                            description=f"**內容：{event.description}**",
                            color=discord.Color.gold()
                        )
                        
                        if event.is_private:
                            # 私人行程：直接傳送私訊
                            await user.send(embed=embed)
                        else:
                            # 公開行程：優先傳送至設定的頻道
                            channel_id = settings.calendar_notify_channel_id if settings else None
                            channel = self.bot.get_channel(channel_id) if channel_id else None
                            
                            if channel:
                                await channel.send(content=f"{user.mention} 您的公開行程提醒：", embed=embed)
                            else:
                                # 若找不到頻道，則備援發送私訊
                                await user.send(content="⚠️ 找不到公開通知頻道，改為私訊提醒：", embed=embed)

                        session.delete(event)
                    except Exception as e:
                        print(f"❌ 發送出錯: {e}")
                
                session.commit()
            except Exception as e:
                print(f"❌ 提醒任務發生錯誤: {e}")
                session.rollback()

                
    @check_reminders.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    @staticmethod
    def create_itinerary_dashboard_ui(user_id: int):
        from .ui.View.ItineraryDashboardView import ItineraryDashboardView
        
        embed, view, file = ItineraryDashboardView.create_ui(user_id)

        return embed, view, file