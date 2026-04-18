from .stock_cog import Stock

async def setup(bot):
    db_session = getattr(bot, "db_session", None)
    await bot.add_cog(Stock(bot, db_session))
    print("Stock Package loaded.")
