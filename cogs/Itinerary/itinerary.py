import discord
import os
from datetime import datetime
import asyncio
from discord.ext import commands, tasks
from .views.itinerary_view import ItineraryAddView, ItineraryDeleteView, ViewPageSelect
from .utils.itinerary_tool import ItineraryTools
from discord import app_commands


class Itinerary(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.tools = ItineraryTools(current_dir)
        self.last_check_minute = -1
        self.check_reminders.start()
        

    @app_commands.command(name="新增行程", description="開啟選單來規劃新的行程")
    async def add_plan(self, interaction: discord.Interaction):
        view = ItineraryAddView(cog = self)
        await interaction.response.send_message("點選下方選項開始規劃行程：", view=view)

    async def process_data(self, interaction, raw_data):
        count, success, info = self.tools .add_and_save(raw_data, interaction.channel.id)
        
        if success:
            return f"成功添加！現在有 {count} 個行程。"
        else:
            return f"添加失敗 目前有 {count} 個行程。\n{info}" 
        
    @app_commands.command(name="查看行程", description="顯示目前所有的行程規劃")
    async def view_plans(self, interaction: discord.Interaction):
        data_list = self.tools.get_data_list()
        view = ViewPageSelect(cog=self, data_list=data_list)    
        await interaction.response.send_message(embed = view.embed, view = view)

    @app_commands.command(name="刪除行程", description="刪除指定的行程")
    async def delete_plan(self, interaction: discord.Interaction):
        data_list = self.tools.view_delete_list()
        view = ItineraryDeleteView(cog=self, data_list = data_list)
        await interaction.response.send_message("點選下方選項刪除行程：", view=view)
        
    async def delete_data(self, selected_index):
        count, success, info = self.tools .delete(selected_index)

        if success:
            msg = f"成功刪除！現在有 {count} 個行程。"
        else:
            msg = f"刪除失敗 目前有 {count} 個行程。\n{info}" 
        
        return success, msg
        
    @tasks.loop(seconds=5.0)
    async def check_reminders(self):
        now = datetime.now()
        if self.last_check_minute != now.minute:
            print(f"檢查中... 現在時間: {now.hour}:{now.minute}")
            
            success, output, channel_id = self.tools.mantion_check(now.minute)

            if success:
                channel = self.bot.get_channel(channel_id)
            
                if channel:
                    await channel.send(output)
                else:
                    print(f"無法在頻道 {channel_id} 發送提醒")
                
            self.last_check_minute = now.minute

            if success:
                self.tools.data_self_check()


    @check_reminders.before_loop
    async def before_check(self):
        print("正在等待機器人準備就緒...")
        await self.bot.wait_until_ready()
        print("機器人已就緒，開始計算對齊時間...")
        
        try:
            now = datetime.now()
            print(f"DEBUG: 現在秒數是 {now.second}")
        except Exception as e:
            print(f"計算出錯了: {e}")
                
        seconds_to_wait = 60 - now.second
        
        if seconds_to_wait > 0:
            print(f"需要等待 {seconds_to_wait} 秒以對齊分鐘...")
            await asyncio.sleep(seconds_to_wait)
        print("時間已對齊，開始執行提醒任務！")
        
        
async def setup(bot):
    #await bot.add_cog(Itinerary(bot))
    print("Itinerary Package loaded.")