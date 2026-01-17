import discord
from discord import app_commands
from discord.ext import commands
from ..utils import ask_gpt

class FortuneCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("[GPT] Fortune Module loaded.")

    async def process_fortune_logic(self, interaction: discord.Interaction):
        if not interaction.response.is_done():
            await interaction.response.defer()

        try:
            prompt = "請以簡短有趣的方式，隨機生成一則今日運勢，給予一些建議做的事與不建議做的事情。"
            result = ask_gpt([{"role": "user", "content": prompt}])
            
            await interaction.followup.send(f"{result}",ephemeral=True)
            
        except Exception as e:
            print(f"Fortune Error: {e}")
            await interaction.followup.send("❌ 運勢生成失敗，請稍後再試。")


    @app_commands.command(name="fortune", description="Check your fortune for today.")
    async def fortune(self, interaction: discord.Interaction):
        await self.process_fortune_logic(interaction)