import discord
import os
from datetime import datetime, timezone, timedelta
from discord.ext import commands, tasks
from database.models import CalendarEvent, BotSettings
from .utils.calendar_manager import CalendarDatabaseManager

class Itinerary(commands.Cog):
    def __init__(self, bot, db_session):
        self.bot = bot
        self.db_session = db_session 
        self.SessionLocal = CalendarDatabaseManager(db_session)
        self.db_manager = self.SessionLocal
        self.last_check_minute = -1
        self.check_reminders.start()

    async def process_data_sql(self, interaction, time_obj, description, is_private, priority):
        clean_time = time_obj.replace(tzinfo=None, second=0, microsecond=0)
        success, report = self.SessionLocal.add_event(
            user_id=interaction.user.id,
            event_time=clean_time,
            description=description,
            is_private=is_private,
            priority=priority
        )   
        return success, report

    @tasks.loop(seconds=10.0)
    async def check_reminders(self):
        await self.bot.wait_until_ready()
        
        # 取得當前台灣時間 (UTC+8)
        tz_tw = timezone(timedelta(hours=8))
        now_tw = datetime.now(tz_tw).replace(tzinfo=None, second=0, microsecond=0)
        
        if self.last_check_minute == now_tw.minute:
            return
        self.last_check_minute = now_tw.minute

        priority_map = {"0": "🔴 緊急", "1": "🟡 重要", "2": "🟢 普通"}

        with self.db_session() as session:
            try:
                # 找出符合當前台灣時間的行程
                events = session.query(CalendarEvent).filter(
                    CalendarEvent.event_time == now_tw
                ).all()

                if not events:
                    return

                # 取得機器人設定
                settings = session.query(BotSettings).first() 

                for event in events:
                    try:
                        user = await self.bot.fetch_user(event.user_id)
                        if not user: continue

                        p_label = priority_map.get(str(event.priority), "🟢 普通")
                        embed = discord.Embed(
                            title=f"{p_label} | 行程提醒",
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

    def create_itinerary_dashboard_ui(self, user_id: int):
        from .ui.View.ItineraryDashboardView import ItineraryDashboardView
        
        embed, view, file = ItineraryDashboardView.create_ui(self, user_id)

        return embed, view, file

