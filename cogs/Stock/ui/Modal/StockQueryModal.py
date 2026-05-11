import discord
from discord import ui
import traceback
from cogs.Stock.utils import get_stock_quote

class StockQueryModal(ui.Modal, title="股票快搜"):
    symbol = ui.TextInput(
        label="股票代號",
        placeholder="例如: 2330",
        min_length=4,
        max_length=6,
        required=True
    )

    # 🌟 1. [修改] 加入 parent_view 參數，用來接收觸發這個 Modal 的原儀表板 View
    def __init__(self, bot, parent_view):
        super().__init__()
        self.bot = bot
        self.parent_view = parent_view 

    async def on_submit(self, interaction: discord.Interaction):
        # 🌟 2. [修改] 移除 ephemeral=True，改為一般 defer()，表明我們將「更新原訊息」
        await interaction.response.defer()
        
        try:
            stock_cog = self.bot.get_cog("Stock")
            sym = self.symbol.value.strip().upper()

            # 呼叫 API
            async with stock_cog.api_lock:
                info = get_stock_quote(sym, stock_cog.api_token)

            if not info or "lastPrice" not in info:
                # 🌟 3. [修改] 查詢失敗時，也直接把錯誤訊息更新在原畫面，不彈出新訊息
                err_embed = discord.Embed(
                    title="❌ 查詢失敗", 
                    description=f"找不到股票 `{sym}`，請確認代號是否正確。", 
                    color=discord.Color.red()
                )
                return await interaction.edit_original_response(embed=err_embed, view=self.parent_view)

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

            # 🌟 4. [修改] 將查詢結果更新回原來的訊息上，並附加上原有的 View (保持按鈕存在)
            await interaction.edit_original_response(embed=embed, view=self.parent_view)

        except Exception as e:
            print(f"❌ 快速查詢失敗: {e}")
            traceback.print_exc()
            
            # 發生系統錯誤時的畫面更新
            err_embed = discord.Embed(
                title="❌ 系統錯誤", 
                description="查詢過程中發生未預期的系統錯誤。", 
                color=discord.Color.red()
            )
            await interaction.edit_original_response(embed=err_embed, view=self.parent_view)