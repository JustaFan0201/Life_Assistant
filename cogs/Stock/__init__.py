from .stock_cog import Stock

async def setup(bot):
    await bot.add_cog(Stock(bot))
    print("Stock Package loaded.")
