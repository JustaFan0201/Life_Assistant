import discord
import traceback
from cogs.BasicDiscordObject import SafeButton

class EInvoicePlatformBtn(SafeButton):
    def __init__(self, bot, category_id: int, row: int = 2):
        super().__init__(style=discord.ButtonStyle.success, label="🧾 發票整合", row=row)
        self.bot = bot
        self.category_id = category_id

    async def do_action(self, interaction: discord.Interaction):
        try:
            from cogs.LifeTracker.ui.View.EInvoicePlatformView import EInvoicePlatformView
            embed, view = EInvoicePlatformView.create_ui(self.bot, interaction.user.id, self.category_id)
            
            await interaction.edit_original_response(embed=embed, view=view, attachments=[])
            
        except Exception as e:
            print("❌ 發票按鈕崩潰：")
            traceback.print_exc()
            await interaction.followup.send(f"發生系統錯誤：`{e}`\n請查看終端機日誌。", ephemeral=True)