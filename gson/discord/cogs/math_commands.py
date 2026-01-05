import discord
from discord.ext import commands

def math_output(ans: float):
    if ans.is_integer(): 
        if ans == 0:
            return "0.0"
        else:
            return int(ans)
    else: return ans

class MathCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command()
    async def add(self, ctx, a: float, b: float):
        ans = a + b
        ans = math_output(ans)
        await ctx.send(ans)

    @commands.hybrid_command()
    async def min(self, ctx, a: float, b: float):
        ans = a - b
        ans = math_output(ans)
        await ctx.send(ans)

    @commands.hybrid_command()
    async def mul(self, ctx, a: float, b: float):
        ans = a * b
        ans = math_output(ans)
        await ctx.send(ans)

    @commands.hybrid_command()
    async def div(self, ctx, a: float, b: float):
        if b == 0:
            await ctx.send("錯誤：除數不可為零")
        else:
            ans = a / b
            ans = math_output(ans)
            await ctx.send(ans)


async def setup(bot):
    await bot.add_cog(MathCommands(bot))
