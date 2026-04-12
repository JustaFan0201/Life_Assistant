# 檔案路徑: cogs/Stock/__init__.py

from .stock_cog import Stock  # 假設你的類別在 stock_cog.py 裡

async def setup(bot):
    # 從 bot 物件取得資料庫 session (對應你 bot.py 的 bot.db_session)
    db_session = getattr(bot, "db_session", None)
    await bot.add_cog(Stock(bot, db_session))
    print("Stock Package loaded.")