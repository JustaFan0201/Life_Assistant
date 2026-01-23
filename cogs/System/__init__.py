from .dashboard import SystemCog

async def setup(bot):
    await bot.add_cog(SystemCog(bot))
    print("System Package loaded.")