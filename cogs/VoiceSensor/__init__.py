from .VoiceSensorCog import VoiceSensorCog
async def setup(bot):
    await bot.add_cog(VoiceSensorCog(bot))
    print("VoiceSensorCog Package Loaded.")