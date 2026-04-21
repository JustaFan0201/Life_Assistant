import discord
from discord import ui
import traceback
from ...utils.fugle_api import get_stock_quote

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
        # 顯示處理中 (查詢 API 需要時間)
        await interaction.response.defer(ephemeral=True)
        
        try:
            stock_cog = self.bot.get_cog("Stock")
            sym = self.symbol.value.strip().upper()

            # 呼叫 API (使用 Lock 確保不會撞到 60/min 限流)
            async with stock_cog.api_lock:
                info = get_stock_quote(sym, stock_cog.api_token)

            if not info or "lastPrice" not in info:
                return await interaction.followup.send(f"❌ 找不到股票 `{sym}`，請確認代號是否正確。", ephemeral=True)

            # 3. 建立結果 Embed
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

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            print(f"❌ 快速查詢失敗: {e}")
            traceback.print_exc()
            await interaction.followup.send("❌ 查詢過程中發生系統錯誤。", ephemeral=True)