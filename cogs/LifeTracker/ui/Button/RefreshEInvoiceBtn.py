import discord
from cogs.BasicDiscordObject import SafeButton
from cogs.LifeTracker.src.invoice_pipeline import InvoicePipeline

class RefreshEInvoiceBtn(SafeButton):
    def __init__(self, bot):
        super().__init__(style=discord.ButtonStyle.secondary, label="🔄 刷新發票資訊")
        self.bot = bot

    async def do_action(self, interaction: discord.Interaction):
        # 1. 抓取當前的 Embed
        embed = interaction.message.embeds[0]
        
        # 2. 加上「執行中」的狀態提示 (加在最後一個欄位)
        embed.add_field(name="🔄 執行狀態", value="⏳ 正在抓取，這大約需要 30~60 秒，請稍候...", inline=False)
        status_field_index = len(embed.fields) - 1 

        # 3. 由於 SafeButton 已經回應過 interaction，這裡使用 edit_original_response 更新畫面
        await interaction.edit_original_response(embed=embed, view=self.view)
        
        # 4. 呼叫 Pipeline，將爬蟲丟入背景執行
        success, msg = await InvoicePipeline.execute(interaction.user.id)
        
        # 5. 根據結果更新剛剛新增的狀態欄位
        if success:
            embed.set_field_at(status_field_index, name="✅ 執行完成", value=msg, inline=False)
        else:
            embed.set_field_at(status_field_index, name="❌ 執行失敗", value=msg, inline=False)
            embed.color = discord.Color.red() # 如果失敗，把整個面板變紅增加警示感
        
        # 6. 爬蟲結束，解鎖 UI 按鈕
        await self.view.unlock_all()
        
        # 7. 最後再把更新結果的 embed 與解鎖的 view 推送回 Discord 畫面
        await interaction.edit_original_response(embed=embed, view=self.view)