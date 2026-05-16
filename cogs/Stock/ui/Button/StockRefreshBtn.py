import discord
from cogs.BasicDiscordObject import SafeButton
from cogs.Stock.ui.View import StockListView

class StockRefreshBtn(SafeButton):
    def __init__(self, bot, row=0):
        super().__init__(
            label="刷新現價損益", 
            style=discord.ButtonStyle.success, 
            emoji="🔄", 
            row=row
        )
        self.bot = bot

    async def do_action(self, interaction: discord.Interaction):
        loading_embed = discord.Embed(
            title=f"📊 {interaction.user.name} 的投資清單", 
            description="⏳ 正在向 Fugle API 獲取最新行情，請稍候...\n(受限於免費版 API，每檔股票需等待 1.1 秒)",
            color=discord.Color.blue()
        )
        
        if not interaction.response.is_done():
            await interaction.response.edit_message(embed=loading_embed, view=None)
        else:
            await interaction.edit_original_response(embed=loading_embed, view=None)

        try:
            from cogs.Stock.ui.View.StockListView import StockListView
            
            embed, view = await StockListView.create_ui(
                bot=self.bot, 
                user_id=interaction.user.id, 
                user_name=interaction.user.name
            )

            if embed and view:
                await interaction.edit_original_response(content=None, embed=embed, view=view)
            else:
                err_embed = discord.Embed(title="❌ 獲取資料失敗", description="請稍後再試。", color=discord.Color.red())
                await interaction.edit_original_response(embed=err_embed, view=None)
                
        except Exception as e:
            print(f"❌ 按鈕執行崩潰: {e}")
            import traceback
            traceback.print_exc()
            err_embed = discord.Embed(title="❌ 系統異常", description=f"發生錯誤：{e}", color=discord.Color.red())
            await interaction.edit_original_response(embed=err_embed, view=None)