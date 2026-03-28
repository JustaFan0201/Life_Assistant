import discord
from discord import ui

class SubcatSelect(ui.Select):
    def __init__(self, parent_view, subcats):
        self.parent_view = parent_view
        options = [discord.SelectOption(label="其他", value="none")] 
        for s in subcats:
            options.append(discord.SelectOption(label=s['name'], value=str(s['id'])))
        super().__init__(placeholder="點此選擇標籤", min_values=1, max_values=1, options=options[:25])

    async def callback(self, interaction: discord.Interaction):
        val = self.values[0]
        self.parent_view.selected_subcat_id = None if val == "none" else int(val)
        embed, view = self.parent_view.build_ui()
        await interaction.response.edit_message(embed=embed, view=view)