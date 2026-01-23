from .gmail import Gmail

async def setup(bot):
    await bot.add_cog(Gmail(bot))
    print("Gmail Package loaded.")