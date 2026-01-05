import discord
from discord.ext import commands, tasks
import json
from datetime import timedelta, timezone
import os
import asyncio

#TAIWAN_TIMEZONE = datetime.timezone(datetime.timedelta(hours=8))
UTC_P8 = timezone(timedelta(hours=8))

class ItineraryCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.minutely_check.start()
        cog_dir = os.path.dirname(os.path.abspath(__file__))
        self.file_path = os.path.join(cog_dir, "Itinerary.json")

    def cog_unload(self):
        self.minutely_check.cancel()
        print("TestCog unloaded, minutely_check cancelled.")



    def readJson(self):
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {"data": []}
        
        if "data" not in data or not isinstance(data["data"], list):
             data["data"] = []
             
        if "data" not in data or not isinstance(data["data"], list):
             data["data"] = []
        if "counter" not in data or not isinstance(data["counter"], int):
             data["counter"] = len(data["data"])

        return data
    
    def writeJson(self, newdata):
        try:
            data = self.readJson()
            newdata["itinerary_id"] = data["counter"] + 1
            data["data"].append(newdata)
            data["counter"] = data["counter"] + 1

            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
                return True 
        
        except Exception as e:
            print(f"寫入 Itinerary.json 失敗: {e}")
            return False  

    def get_itinerary_by_id(self, data_container, target_id):
        itineraries = data_container.get("data", []) 

        target_id = int(target_id)
        
        for item in itineraries:
            item_id = item.get("itinerary_id")
            if item_id is not None and int(item_id) == target_id:
                return item
        return None

    @commands.hybrid_command(description="格式為西元年月日24小時至。")
    async def 行程表(self, ctx, item : str, year : str, month : str, date : str, hour : str , minute : str , note : str):
        
        ctx.defer(ephemeral=True)
        guild_id = ctx.guild.id

        timeFormessage = year + "/" + month + "/" + date + "的" + hour + ":" + minute
        newdata = {"itinerary_id": 0,"guild_id": guild_id, "item": item, "year": year, "month": month, "date": date, "hour": hour, "minute": minute, "note": note}

        if self.writeJson(newdata):
            await ctx.send(f"已更新行程: {item} 於 {timeFormessage} ## {note}")
            
    #------------------------------------------------------------------------------------------------------------

    @tasks.loop(minutes=1.0)
    #@tasks.loop(seconds= 5)
    async def minutely_check(self):
        
        try:
            now_utc8 = discord.utils.utcnow().astimezone(UTC_P8)
            print(f"[{self.bot.user.name}] Checkpoint @ {now_utc8.strftime('%H:%M:%S')}")

            now_time_dict = {
            "year": now_utc8.strftime("%Y"), 
            "month": now_utc8.strftime("%m"),
            "day": now_utc8.strftime("%d"),  
            "hour": now_utc8.strftime("%H"), 
            "minute": now_utc8.strftime("%M"),
            }

            data = self.readJson()
            for i in range(1,len(data["data"]) + 1):
                itinerary_data = self.get_itinerary_by_id(data, i)
                if itinerary_data is None: 
                    continue

                itinerary_time_dict = {
                    "year": itinerary_data.get("year"),
                    "month": itinerary_data.get("month"),
                    "day": itinerary_data.get("date"),
                    "hour": itinerary_data.get("hour"),
                    "minute": itinerary_data.get("minute"),
                }

                if now_time_dict == itinerary_time_dict:

                    target_guild_id = itinerary_data.get("guild_id")
                    guild = self.bot.get_guild(target_guild_id)

                    if guild is None:
                        print(f"[itinerary]error: Bot 不在 ID 為 {itinerary_data["guild_id"]} 的伺服器中。")
                        continue
                    
                    target_channel = guild.system_channel
                    if target_channel is None and guild.text_channels:
                        target_channel = guild.text_channels[0]


                    await target_channel.send(f"[行程表]提醒: {itinerary_data["item"]} ## {itinerary_data["note"]} ##")
                    print(f"[itinerary]success: sent itinerary")

        except Exception as e:
            print("="*40)
            print(f"循環任務 [minutely_check] 發生錯誤！")
            print(f"錯誤類型: {type(e).__name__}")
            print(f"錯誤訊息: {e}")
            # print(f"任務將嘗試在 5 秒後重新啟動...") # 任務會自動重啟，除非你在這裡呼叫 cancel()
            print("="*40)      
            

    @minutely_check.before_loop
    async def before_minutely_check(self):
        print("[itinerary] Waiting for bot to be ready...")
        await self.bot.wait_until_ready()
        print("[itinerary] Bot ready! starting minutely_check.")

        now = discord.utils.utcnow()
        secs_to_wait = 60 - now.second
        
        print(f"[itinerary] Waiting {secs_to_wait} seconds for the start of the next minute (00s).")
        await asyncio.sleep(secs_to_wait)
        print("[itinerary] Starting minutely_check now.")


async def setup(bot):
    await bot.add_cog(ItineraryCommands(bot))