# cogs\LifeTracker\ui\Button\BackToDetailBtn.py
import discord
from cogs.BasicDiscordObject import SafeButton

class BackToDetailBtn(SafeButton):
    def __init__(self, bot, category_id, label="", style=discord.ButtonStyle.danger, emoji="🔙", row=1):
        super().__init__(label=label, style=style, emoji=emoji, row=row)
        self.bot = bot
        self.category_id = category_id

    async def do_action(self, interaction: discord.Interaction):
        from cogs.LifeTracker.ui.View.CategoryDetailView import CategoryDetailView
        
        try:
            embed, view, chart_file = await CategoryDetailView.create_ui(
                self.bot, 
                self.category_id
            )
            
            attachments = [chart_file] if chart_file else []
            await interaction.edit_original_response(
                embed=embed, 
                view=view, 
                attachments=attachments
            )
        except Exception as e:
            if self.view:
                await self.view.unlock_all()
            await interaction.followup.send(f"❌ 返回看板失敗: {e}", ephemeral=True)