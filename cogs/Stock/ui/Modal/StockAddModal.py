import discord
from discord import ui
from cogs.Stock.utils import get_stock_quote,StockManager,fugle_api_lock
from cogs.Stock.stock_config import FUGLE_TOKEN

class StockAddModal(ui.Modal, title="新增監控股票"):
    symbol = ui.TextInput(label="股票代號", placeholder="例如: 2330", min_length=4, max_length=10)
    shares = ui.TextInput(label="持股數量", placeholder="例如: 1000", default="0", required=False)
    total_cost = ui.TextInput(label="總投入成本 (含手續費)", placeholder="例如: 650000", default="0", required=False)
    up_percent = ui.TextInput(label="漲幅預警 (%)", placeholder="例如: 5 (代表 5%)", required=False)
    down_percent = ui.TextInput(label="跌幅預警 (%)", placeholder="例如: -3 (代表 -3%)", required=False)

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        error_msg = await self.execute_logic(interaction)
        
        if error_msg:
            await interaction.followup.send(error_msg, ephemeral=True)
        else:
            from cogs.Stock.ui.View import StockDashboardView
            embed, view = StockDashboardView.create_dashboard(self.bot, interaction.user.id)
            embed.title = "✅ 新增成功！"
            await interaction.edit_original_response(embed=embed, view=view)

    async def execute_logic(self, interaction: discord.Interaction) -> str | None:
        """執行校驗與存檔"""
        sym = self.symbol.value.strip().upper()
        num_shares = int(self.shares.value) if self.shares.value.isdigit() else 0
        cost_val = float(self.total_cost.value) if self.total_cost.value else 0.0
        
        up = int(self.up_percent.value) if self.up_percent.value else None
        down = int(self.down_percent.value) if self.down_percent.value else None

        return await StockAddModal.check(sym, num_shares, cost_val, up, down, interaction.user.id, interaction.user.name)
         
        
    @staticmethod
    async def check(symbol: str, shares: int, total_cost: float, up_percent: int|None, down_percent: int|None, user_id, user_name):
        sym = symbol.strip().upper()
        try:
            num_shares = shares
            cost_val = total_cost
            avg_price = cost_val / num_shares if num_shares > 0 else None
            
            up = float(up_percent) / 100 if up_percent else None
            down = float(down_percent) / 100 if down_percent else None

            # 串接 API 確認股票是否存在
            # 直接透過 bot 獲取 cog 的 lock，不額外宣告變數
            async with fugle_api_lock:
                info = get_stock_quote(sym, FUGLE_TOKEN)
            
            if not info or "lastPrice" not in info:
                return f"❌ 找不到股票 `{sym}`，請確認代號是否正確。"

            data = {
                'symbol': sym, 'name': info['name'], 'shares': num_shares,
                'total_cost': cost_val, 'buy_price': avg_price, 'up': up, 'down': down
            }
            
            StockManager.add_stock(user_id, user_name, data)
            
            return None 
            
        except ValueError:
            return "❌ 格式錯誤！請填入正確數字。"
        except Exception as e:
            print(f"❌ 新增出錯: {e}")
            return f"❌ 系統錯誤: {e}"
