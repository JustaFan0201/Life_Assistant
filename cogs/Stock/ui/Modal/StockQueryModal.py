import discord
from discord import ui
import traceback

from cogs.Stock.utils import get_stock_quote,fugle_api_lock
from cogs.Stock.stock_config import FUGLE_TOKEN
from cogs.Stock.ui.View.StockDashboardView import StockDashboardView

class StockQueryModal(ui.Modal, title="股票快搜"):
    symbol = ui.TextInput(
        label="股票代號",
        placeholder="例如: 2330",
        min_length=4,
        max_length=6,
        required=True
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed, view = await StockQueryModal.create_dashboard(self.bot, interaction.user.id, self.symbol.value)
        await interaction.edit_original_response(embed=embed, view=view)
    
    @staticmethod
    async def create_dashboard(bot, user_id, symbol: str):    
        try:
            sym = symbol.strip().upper()
            async with fugle_api_lock:
                info = get_stock_quote(sym, FUGLE_TOKEN)

            view = StockDashboardView(bot, user_id)

            if not info or "lastPrice" not in info:
                err_embed = discord.Embed(
                    title="❌ 查詢失敗", 
                    description=f"找不到股票 `{sym}`，請確認代號是否正確。", 
                    color=discord.Color.red()
                )
                return err_embed, view

            # 建立結果 Embed
            price = info['lastPrice']
            pct = info['changePercent']
            emoji = "🔺" if pct > 0 else "🟢" if pct < 0 else "⚪"
            color = discord.Color.red() if pct > 0 else discord.Color.green() if pct < 0 else discord.Color.light_gray()
            
            embed = discord.Embed(
                title=f"🔍 查詢結果：{info['name']} ({info['symbol']})",
                color=color,
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="目前成交價", value=f"### `{price}`", inline=True)
            embed.add_field(name="本日漲跌幅", value=f"### {emoji} `{pct:.2f}%`", inline=True)
            embed.set_footer(text="提示：此數據為即時行情，僅供參考。")

            # 將查詢結果更新回原來的訊息上，並附加上原有的 View (保持按鈕存在)
            return embed, view

        except Exception as e:
            print(f"❌ 快速查詢失敗: {e}")
            traceback.print_exc()
            
            # 發生系統錯誤時的畫面更新
            err_embed = discord.Embed(
                title="❌ 系統錯誤", 
                description="查詢過程中發生未預期的系統錯誤。", 
                color=discord.Color.red()
            )
            return err_embed, view
    