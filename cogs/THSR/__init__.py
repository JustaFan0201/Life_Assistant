from .dashboard import THSR_Cog
from .task import THSRTask

async def setup(bot):
    await bot.add_cog(THSR_Cog(bot))
    await bot.add_cog(THSRTask(bot))
    print("THSR Package loaded.")