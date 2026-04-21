import discord
from discord import ui

class StockDeleteSelect(ui.Select):
    def __init__(self, bot, stocks, dashboard_interaction: discord.Interaction):
        options = [
            discord.SelectOption(label=f"{s.stock_name} ({s.stock_symbol})", value=s.stock_symbol, emoji="📈")
            for s in stocks
        ]
        # 取消選項
        options.append(discord.SelectOption(label="取消操作", value="cancel", emoji="❌", description="返回不刪除"))
        
        super().__init__(placeholder="請選擇要移除的股票...", options=options)
        self.bot = bot
        self.dashboard_interaction = dashboard_interaction 

    async def callback(self, interaction: discord.Interaction):
        # Defer 避免 3 秒交互失敗
        await interaction.response.defer(ephemeral=True)
        
        # 延遲匯入避免循環引用
        from ..View.StockDashboardView import StockDashboardView
        from ...utils.Stock_Manager import Stock_Manager

        # 處理「取消刪除」
        if self.values[0] == "cancel":
            # 重新產生主畫面的 Embed 與 View（確保按鈕狀態與資料最新）
            embed_new, view_new = StockDashboardView.create_dashboard(self.bot, interaction.user.id)
            
            # 更新「後方」的主介面
            await self.dashboard_interaction.edit_original_response(embed=embed_new, view=view_new)
            
            # 關閉「前方」的取消選單
            return await interaction.edit_original_response(content="已取消刪除操作，已為您刷新主畫面。", view=None)

        # 3. 處理「確認刪除」的情境
        try:
            stock_cog = self.bot.get_cog("Stock")
            symbol = self.values[0]
            
            # 執行刪除邏輯
            success, res_name = Stock_Manager.delete_stock(stock_cog.db_manager, interaction.user.id, symbol)
            
            if success:
                # 刪除成功後，刷新主畫面
                embed_new, view_new = StockDashboardView.create_dashboard(self.bot, interaction.user.id)
                await self.dashboard_interaction.edit_original_response(embed=embed_new, view=view_new)
                
                await interaction.edit_original_response(content=f"✅ 已成功移除 **{res_name}**，主畫面已同步更新。", view=None)
            else:
                await interaction.edit_original_response(content=f"❌ 刪除失敗：{res_name}")
                
        except Exception as e:
            print(f"❌ StockDeleteSelect 錯誤: {e}")
            await interaction.edit_original_response(content=f"❌ 執行錯誤: {e}")