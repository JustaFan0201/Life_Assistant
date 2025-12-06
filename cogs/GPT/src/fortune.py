import discord
from discord import app_commands
from discord.ext import commands
from ..utils import ask_gpt

class FortuneCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Fortune Module loaded.")

    @app_commands.command(name="fortune", description="Check your fortune for today.")
    async def fortune(self, interaction: discord.Interaction):
        await interaction.response.defer()
        prompt = "請以簡短有趣的方式，隨機生成一則今日運勢，給予一些建議做的事與不建議做的事情。"
        result = ask_gpt([{"role": "user", "content": prompt}])
        await interaction.followup.send(f"{result}")