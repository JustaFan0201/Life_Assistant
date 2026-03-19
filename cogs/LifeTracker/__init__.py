from .dashboard import LifeTracker_Cog
async def setup(bot):
    await bot.add_cog(LifeTracker_Cog(bot))