import discord
from discord import ui
from ...utils.fugle_api import get_stock_quote 

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
        # 立即顯示處理中
        await interaction.response.defer(ephemeral=True)
        
        error_msg = await self.execute_logic(interaction)
        
        if error_msg:
            await interaction.followup.send(error_msg, ephemeral=True)
        else:
            # 成功後呼叫主畫面的更新邏輯
            stock_cog = self.bot.get_cog("Stock")
            from ..View.StockDashboardView import StockDashboardView
            embed, view = StockDashboardView.create_dashboard(self.bot, interaction.user.id)
            await interaction.edit_original_response(content="✅ 新增成功！", embed=embed, view=view)

    async def execute_logic(self, interaction: discord.Interaction) -> str:
        """執行校驗與存檔"""
        from ...utils.Stock_Manager import Stock_Manager
        stock_cog = self.bot.get_cog("Stock")
        
        sym = self.symbol.value.strip().upper()
        
        try:
            # 數值校驗
            num_shares = int(self.shares.value) if self.shares.value.isdigit() else 0
            cost_val = float(self.total_cost.value) if self.total_cost.value else 0.0
            avg_price = cost_val / num_shares if num_shares > 0 else None
            
            up = float(self.up_percent.value) / 100 if self.up_percent.value else None
            down = float(self.down_percent.value) / 100 if self.down_percent.value else None

            # 串接 API 確認股票是否存在
            async with stock_cog.api_lock:
                info = get_stock_quote(sym, stock_cog.api_token)
            
            if not info or "lastPrice" not in info:
                return f"❌ 找不到股票 `{sym}`，請確認代號是否正確。"

            # 存檔
            data = {
                'symbol': sym, 'name': info['name'], 'shares': num_shares,
                'total_cost': cost_val, 'buy_price': avg_price, 'up': up, 'down': down
            }
            Stock_Manager.add_stock(stock_cog.db_manager, interaction.user.id, interaction.user.name, data)
            return None 
            
        except ValueError:
            return "❌ 格式錯誤！請填入正確數字。"
        except Exception as e:
            print(f"❌ 新增出錯: {e}")
            return f"❌ 系統錯誤: {e}"