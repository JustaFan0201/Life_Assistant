from .gmail import Gmail

async def setup(bot):
    db_session = getattr(bot, "db_session", None)
    
    if db_session is None:
        print("[Gmail Package] 載入失敗：找不到資料庫 Session。")
        return

    await bot.add_cog(Gmail(bot, db_session))
    print("Gmail Package loaded.")