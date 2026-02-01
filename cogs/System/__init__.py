from .dashboard import SystemCog
from .settings import SettingsCog

async def setup(bot):
    await bot.add_cog(SystemCog(bot))
    print("System Package loaded.")

async def setup(bot):
    await bot.add_cog(SettingsCog(bot))
    print("Settings Package loaded.")