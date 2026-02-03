from .dashboard import SystemCog
from .settings import SettingsCog

async def setup(bot):
    await bot.add_cog(SystemCog(bot))
    await bot.add_cog(SettingsCog(bot))
    print("System Package loaded.")
    print("Settings Package loaded.")