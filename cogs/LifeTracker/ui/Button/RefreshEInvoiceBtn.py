import discord
from datetime import datetime
from config import TW_TZ
from cogs.BasicDiscordObject import SafeButton
from cogs.LifeTracker.src.invoice_pipeline import InvoicePipeline
from cogs.LifeTracker.utils.EInvoice_Manager import EInvoice_Manager

class RefreshEInvoiceBtn(SafeButton):
    def __init__(self, bot):
        super().__init__(style=discord.ButtonStyle.secondary, label="🔄 刷新發票資訊")
        self.bot = bot

    async def do_action(self, interaction: discord.Interaction):
        # 局部引入，避免 Circular Import
        from cogs.LifeTracker.ui.View.EInvoicePlatformView import EInvoicePlatformView

        config = EInvoice_Manager.get_config(interaction.user.id)
        if config and config.get('last_fetch_date') == datetime.now(TW_TZ).date():
            # 生成一份乾淨的 Embed (避免欄位無限疊加)
            new_embed, _ = EInvoicePlatformView.create_ui(
                self.bot, 
                interaction.user.id, 
                self.view.category_id
            )
            
            # 將提示訊息加在 Embed 底部
            new_embed.add_field(
                name="✅ 執行狀態", 
                value="系統今天已經為您更新過發票囉！財政部資料同步需要時間，請明天再來試試吧！", 
                inline=False
            )
            
            # 解鎖按鈕並更新畫面
            await self.view.unlock_all()
            await interaction.edit_original_response(embed=new_embed, view=self.view)
            return

        # 1. 抓取當前的 Embed (準備加上執行中的提示)
        embed = interaction.message.embeds[0]
        
        # 2. 加上「執行中」的狀態提示
        embed.add_field(name="🔄 執行狀態", value="⏳ 正在抓取，這大約需要 30~60 秒，請稍候...", inline=False)

        # 3. 使用 edit_original_response 更新畫面
        await interaction.edit_original_response(embed=embed, view=self.view)
        
        # 4. 呼叫 Pipeline，將爬蟲丟入背景執行
        success, msg = await InvoicePipeline.execute(interaction.user.id)
        
        # 5. 爬蟲執行完畢後，重新讀取資料庫並產生最新介面
        new_embed, _ = EInvoicePlatformView.create_ui(
            self.bot, 
            interaction.user.id, 
            self.view.category_id
        )
        
        # 6. 根據結果，將執行狀態加進這份「全新」的 Embed 中
        if success:
            new_embed.add_field(name="✅ 執行完成", value=msg, inline=False)
        else:
            new_embed.add_field(name="❌ 執行失敗", value=msg, inline=False)
            new_embed.color = discord.Color.red() 
        
        # 7. 爬蟲結束，解鎖目前的 UI 按鈕
        await self.view.unlock_all()
        
        # 8. 最後將含有最新日期的 embed 與解鎖的 view 推送回 Discord 畫面
        await interaction.edit_original_response(embed=new_embed, view=self.view)