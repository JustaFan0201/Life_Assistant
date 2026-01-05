import os
import random
import json
from discord.ext import commands

class FoodCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
        config_file_name = "data.json"

        self.data = self._load_data(base_dir, config_file_name)
        
        self.breakfast_options = self._get_options("Breakfast_Choise")
        self.lunch_options = self._get_options("Lunch_Choise")
        self.dinner_options = self._get_options("Dinner_Choise")

    def _load_data(self, base_dir, filename):
        
        file_path = os.path.join(base_dir, filename)
        
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
            print(f"Cog 載入錯誤：無法從 {filename} 讀取數據。錯誤: {e}")
            return {}

    def _get_options(self, key_name):
        if self.data and key_name in self.data:
            return self.data[key_name].split(":")
        else:
            return ["找不到食物清單"]

    @commands.hybrid_command()
    async def 早餐吃什麼(self, ctx):
        choice = random.choice(self.breakfast_options)
        await ctx.send(choice)

    @commands.hybrid_command()
    async def 午餐吃什麼(self, ctx):
        choice = random.choice(self.lunch_options)
        await ctx.send(choice)

    @commands.hybrid_command()
    async def 晚餐吃什麼(self, ctx):
        choice = random.choice(self.dinner_options)
        await ctx.send(choice)


async def setup(bot):
    await bot.add_cog(FoodCommands(bot))
