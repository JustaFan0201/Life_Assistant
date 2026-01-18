from .src import THSR_CheckTimeStampCog


async def setup(bot):
    await bot.add_cog(THSR_CheckTimeStampCog(bot))
    print("THSR Package loaded.")