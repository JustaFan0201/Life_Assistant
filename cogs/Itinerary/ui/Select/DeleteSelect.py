# cogs\Itinerary\ui\Select\DeleteSelect.py
import discord

class DeleteSelect(discord.ui.Select):
    def __init__(self, parent_view, options):
        self.parent_view = parent_view
        super().__init__(placeholder="請先選擇要刪除的行程...", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.selected_event_id = int(self.values[0])
        
        for opt in self.options:
            opt.default = (opt.value == self.values[0])

        for child in self.parent_view.children:
            if getattr(child, 'label', '') == "確定刪除":
                child.disabled = False

        await interaction.response.edit_message(view=self.parent_view)