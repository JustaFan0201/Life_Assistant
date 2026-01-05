import random
from discord.ext import commands

class GameCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.left = 0
        self.right = 100
        self.rannum = 0
        self.end = True

    @commands.hybrid_command()
    async def 抽籤(self, ctx, max: int):
        if max < 1:
            await ctx.send("抽籤的上限數字必須大於或等於 1")
            return
            
        await ctx.send(random.randint(1, max))

    @commands.hybrid_command()
    async def 猜數字(self, ctx, ans: int):

        if self.end:
            self.end = False
            self.rannum = random.randint(1, 99)
            self.left = 0
            self.right = 100
            
        if 1 <= ans <= 99:
            if ans == self.rannum:
                await ctx.send(f"太好了! 你猜對了，數字就是 {self.rannum}！")
                # 遊戲重置
                self.end = True
                self.left = 0
                self.right = 100
            else:
                if self.left < ans < self.right:
                    if ans > self.rannum:
                        self.right = ans
                    elif ans < self.rannum:
                        self.left = ans
                        
                    await ctx.send(f"猜錯了，請繼續猜！目前範圍是 **{self.left} ~ {self.right}**")
                else:
                    await ctx.send(f"猜錯了。請猜測範圍在 {self.left} ~ {self.right} 之間")
        else: 
            await ctx.send("錯。請輸入 1 到 99 之間的數字。")



async def setup(bot):
    await bot.add_cog(GameCommands(bot))