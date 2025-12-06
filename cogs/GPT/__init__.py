from .src import FortuneCog
from .src import ReplyCog

async def setup(bot):
    await bot.add_cog(FortuneCog(bot))
    await bot.add_cog(ReplyCog(bot))
    print("GPT Package loaded (Source from src).")