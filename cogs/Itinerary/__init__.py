from .itinerary_cog import Itinerary

async def setup(bot):
    db_session = getattr(bot, "db_session", None)
    await bot.add_cog(Itinerary(bot, db_session))
    print("Itinerary Package loaded.")