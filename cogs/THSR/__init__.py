from .dashboard import THSR_Cog

async def setup(bot):
    await bot.add_cog(THSR_Cog(bot))
    print("THSR Package loaded.")