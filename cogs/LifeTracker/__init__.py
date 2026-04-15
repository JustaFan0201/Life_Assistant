from .LifeTrackerTasks import LifeTrackerTasks
async def setup(bot):
    await bot.add_cog(LifeTrackerTasks(bot))
    print("LifeTrackerTasks Package Loaded.")