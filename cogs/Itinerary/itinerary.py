import discord
import os
from datetime import datetime, timezone, timedelta
import asyncio
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
        clean_time = time_obj.replace(second=0, microsecond=0)
        
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
        now_with_tz = datetime.now(tz_tw)
        now_naive = now_with_tz.replace(tzinfo=None, second=0, microsecond=0)
        
        if self.last_check_minute == now_naive.minute:
            return
        self.last_check_minute = now_naive.minute

        print(f"[行程檢查] 伺服器判定台灣時間: {now_naive}")

        priority_map = {"0": "🔴 緊急", "1": "🟡 重要", "2": "🟢 普通"}

        with self.db_session() as session:
            try:
                expired_count = session.query(CalendarEvent).filter(
                    CalendarEvent.event_time < (now_naive - timedelta(hours=1))
                ).delete(synchronize_session=False)
                
                if expired_count > 0:
                    print(f"[自動清理] 已刪除 {expired_count} 筆過期行程。")
            except Exception as e:
                print(f"[清理失敗] {e}")

            events = session.query(CalendarEvent).filter(
                CalendarEvent.event_time == now_naive
            ).all()

            if not events:
                session.commit()
                return

            print(f"[通知] 找到 {len(events)} 筆行程準備發送")

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
                        try:
                            await user.send(embed=embed)
                        except:
                            print(f"❌ 無法私訊使用者 {event.user_id}")
                    else:
                        settings = session.query(BotSettings).filter_by(id=1).first()
                        channel_id = settings.calendar_notify_channel_id if settings else None
                        
                        if channel_id:
                            channel = self.bot.get_channel(channel_id)
                            if channel:
                                await channel.send(content=f"{user.mention} 您的行程提醒：", embed=embed)
                            else:
                                await user.send(content="⚠️ 通知頻道失效，改以私訊提醒：", embed=embed)
                        else:
                            await user.send(content="⚠️ 未設定通知頻道，改以私訊提醒：", embed=embed)

                    session.delete(event)
                except Exception as e:
                    print(f"❌ 發送提醒出錯: {e}")
            
            session.commit()

    @check_reminders.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    def create_itinerary_dashboard_ui(self):
        embed = discord.Embed(
            title="📅 個人行程管理系統",
            description="您可以在這裡查看、新增或刪除您的行程。\n💡 **提示：** 公開行程將發送到系統設定的通知頻道。",
            color=discord.Color.blue()
        )
        from .views.itinerary_view import ItineraryDashboardView 
        view = ItineraryDashboardView(self.bot, self) 
        return embed, view

async def setup(bot):
    db_session = getattr(bot, "db_session", None)
    await bot.add_cog(Itinerary(bot, db_session))
    print("Itinerary Package loaded with SQL support.")