# cogs/Gmail/__init__.py
from .gmail_cog import Gmail
async def setup(bot):
    session_factory = getattr(bot, "db_session", None)
    await bot.add_cog(Gmail(bot, session_factory))
    print("✅ Gmail 模組已成功載入並註冊至 Cog 列表")