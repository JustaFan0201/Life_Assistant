from .core import SystemCog

async def setup(bot):
    await bot.add_cog(SystemCog(bot))