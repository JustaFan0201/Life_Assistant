import discord
from discord import ui
from cogs.LifeTracker.utils import LifeTrackerDatabaseManager

class SubmitRecordBtn(ui.Button):
    def __init__(self, parent_view, label="", emoji="✅", row=1):
        super().__init__(label=label, style=discord.ButtonStyle.success, emoji=emoji, row=row)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        try:
            # 寫入資料庫
            LifeTrackerDatabaseManager.add_life_record(
                user_id=interaction.user.id,
                category_id=self.parent_view.category_id,
                subcat_id=self.parent_view.selected_subcat_id,
                values_dict=self.parent_view.input_values,
                note=self.parent_view.note,
                record_time_str=self.parent_view.record_time
            )
            
            from cogs.LifeTracker.ui.View import CategoryDetailView
            embed, view = CategoryDetailView.create_ui(self.parent_view.bot, self.parent_view.category_id, page=0)
            await interaction.response.edit_message(embed=embed, view=view)
            
        except Exception as e:
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ 寫入失敗: {e}", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ 寫入失敗: {e}", ephemeral=True)