import discord
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

    async def _send_single_event_reminder(self, session, event, settings, now_tw):
        try:
            user = await self.bot.fetch_user(event.user_id)
            if not user: 
                return
            
            time_difference = event.event_time - now_tw
            is_one_hour_ahead = time_difference.total_seconds() > 1800

            if is_one_hour_ahead:
                title_text = "⏳ | 行程即將在 1 小時後開始"
                color_theme = discord.Color.blue()
                content_prefix = "提醒您，您有一個即將到來的行程："
            else:
                title_text = "📅 | 行程提醒"
                color_theme = discord.Color.gold()
                content_prefix = "您的行程時間已到："

            embed = discord.Embed(
                title=title_text,
                description=f"**內容：{event.description}**\n🔔 預定時間：`{event.event_time.strftime('%Y-%m-%d %H:%M')}`",
                color=color_theme
            )
            
            if event.is_private:
                await user.send(embed=embed)
            else:
                channel_id = settings.calendar_notify_channel_id if settings else None
                channel = self.bot.get_channel(channel_id) if channel_id else None
                
                if channel:
                    await channel.send(content=f"{user.mention} {content_prefix}", embed=embed)
                else:
                    # 若找不到頻道，則備援發送私訊
                    await user.send(content=f"⚠️ 找不到公開通知頻道，改為私訊提醒：\n{content_prefix}", embed=embed)

            if not is_one_hour_ahead:
                session.delete(event)
        except Exception as e:
            print(f"❌ 發送出錯: {e}")

    async def _process_events(self, session, events, settings, now_tw):
        for event in events:
            await self._send_single_event_reminder(session, event, settings, now_tw)

    @tasks.loop(seconds=10.0)
    async def check_reminders(self):
        await self.bot.wait_until_ready()
        
        # 取得當前台灣時間 (UTC+8)
        tz_tw = timezone(timedelta(hours=8))
        now_tw = datetime.now(tz_tw).replace(tzinfo=None)
        
        if self.last_check_minute == now_tw.minute:
            return
        self.last_check_minute = now_tw.minute
        current_minute_start = now_tw.replace(second=0, microsecond=0)
        current_minute_end = current_minute_start + timedelta(minutes=1)

        one_hour_later_start = current_minute_start + timedelta(hours=1)
        one_hour_later_end = one_hour_later_start + timedelta(minutes=1)

        with self.db_session_maker() as session:
            try:
                events = session.query(CalendarEvent).filter(
                    (
                        (CalendarEvent.event_time >= current_minute_start) & 
                        (CalendarEvent.event_time < current_minute_end)
                    ) | 
                    (
                        (CalendarEvent.event_time >= one_hour_later_start) & 
                        (CalendarEvent.event_time < one_hour_later_end)
                    )
                ).all()

                if not events:
                    return
                settings = session.query(BotSettings).first() 
                await self._process_events(session, events, settings, current_minute_start)

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