import discord
import os
from datetime import datetime, timezone, timedelta
from discord.ext import commands, tasks
from database.models import CalendarEvent, BotSettings
from database.calendar_manager import CalendarDatabaseManager

class Itinerary(commands.Cog):
    def __init__(self, bot, db_session):
        self.bot = bot
        self.db_session = db_session 
        self.db_manager = CalendarDatabaseManager(db_session)
        self.last_check_minute = -1
        self.check_reminders.start()

    async def process_data_sql(self, interaction, time_obj, description, is_private, priority):
        clean_time = time_obj.replace(tzinfo=None, second=0, microsecond=0)
        
        success, report = self.db_manager.add_event(
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

        tz_tw = timezone(timedelta(hours=8))
        now_tw = datetime.now(tz_tw).replace(tzinfo=None, second=0, microsecond=0)
        
        if self.last_check_minute == now_tw.minute:
            return
        self.last_check_minute = now_tw.minute

        #print(f"[時區比對] 目前台灣時間: {now_tw}")

        priority_map = {"0": "🔴 緊急", "1": "🟡 重要", "2": "🟢 普通"}

        with self.db_session() as session:
            try:
                session.query(CalendarEvent).filter(
                    CalendarEvent.event_time < (now_tw - timedelta(days=1))
                ).delete(synchronize_session=False)
            except Exception as e:
                print(f"❌ [清理失敗] {e}")
                
            events = session.query(CalendarEvent).filter(
                CalendarEvent.event_time == now_tw
            ).all()

            if not events:
                session.commit()
                return

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
                        await user.send(embed=embed)
                    else:
                        settings = session.query(BotSettings).filter_by(id=1).first()
                        channel_id = settings.calendar_notify_channel_id if settings else None
                        if channel_id:
                            channel = self.bot.get_channel(channel_id)
                            if channel:
                                await channel.send(content=f"{user.mention} 您的行程提醒：", embed=embed)
                            else:
                                await user.send(embed=embed)
                        else:
                            await user.send(embed=embed)

                    session.delete(event)
                except Exception as e:
                    print(f"❌ 發送出錯: {e}")
            
            session.commit()

    @check_reminders.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    def create_itinerary_dashboard_ui(self):
        embed = discord.Embed(
            title="📅 個人行程管理系統",
            description="您可以在這裡查看、新增或刪除您的行程。",
            color=discord.Color.blue()
        )
        from .views.itinerary_view import ItineraryDashboardView 
        view = ItineraryDashboardView(self.bot, self) 
        return embed, view

async def setup(bot):
    db_session = getattr(bot, "db_session", None)
    await bot.add_cog(Itinerary(bot, db_session))