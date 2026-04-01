# cogs/LifeTracker/ui/Button/SubmitRecordBtn.py
import discord
from discord import ui
from cogs.LifeTracker.utils import LifeTrackerDatabaseManager
from cogs.Base import SafeButton

class SubmitRecordBtn(SafeButton): 
    def __init__(self, parent_view, label="", emoji="✅", row=1):
        super().__init__(label=label, style=discord.ButtonStyle.success, emoji=emoji, row=row)
        self.parent_view = parent_view

    async def do_action(self, interaction: discord.Interaction):
        try:
            LifeTrackerDatabaseManager.add_life_record(
                user_id=interaction.user.id,
                category_id=self.parent_view.category_id,
                subcat_id=self.parent_view.selected_subcat_id,
                values_dict=self.parent_view.input_values,
                note=self.parent_view.note,
                record_time_str=self.parent_view.record_time
            )
            
            from cogs.LifeTracker.ui.View.CategoryDetailView import CategoryDetailView
            
            embed, view, chart_file = await CategoryDetailView.create_ui(
                self.parent_view.bot, 
                self.parent_view.category_id, 
                page=0
            )

            if chart_file:
                await interaction.edit_original_response(embed=embed, view=view, attachments=[chart_file])
            else:
                await interaction.edit_original_response(embed=embed, view=view, attachments=[])
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            
            if self.view:
                await self.view.unlock_all(interaction)
                
            await interaction.followup.send(f"❌ 錯誤: {e}", ephemeral=True)