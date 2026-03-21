import discord
from discord import ui
from datetime import datetime, timezone, timedelta

TW_TZ = timezone(timedelta(hours=8))

class InputValueModal(ui.Modal):
    def __init__(self, parent_view, fields: list):
        super().__init__(title="⌨️ 填寫數值與備註")
        self.parent_view = parent_view 
        
        self.field_inputs = {}
        
        for f in fields[:3]: 
            text_input = ui.TextInput(label=f, required=True, max_length=50)
            if f in parent_view.input_values:
                text_input.default = parent_view.input_values[f]
            self.field_inputs[f] = text_input
            self.add_item(text_input)

        default_time = getattr(parent_view, 'record_time', None)
        if not default_time:
            default_time = datetime.now(TW_TZ).strftime("%Y/%m/%d")

        self.time_input = ui.TextInput(
            label="紀錄日期 (YYYY/MM/DD)",
            default=default_time,
            placeholder="例如：2026/03/22",
            required=True,
            max_length=10
        )
        self.add_item(self.time_input)

        self.note_input = ui.TextInput(label="備註 (選填)", required=False, max_length=100)
        if parent_view.note:
            self.note_input.default = parent_view.note
        self.add_item(self.note_input)

    async def on_submit(self, interaction: discord.Interaction):
        for f_name, input_ui in self.field_inputs.items():
            self.parent_view.input_values[f_name] = input_ui.value.strip()
            
        self.parent_view.note = self.note_input.value.strip()
        
        self.parent_view.record_time = self.time_input.value.strip()

        embed, view = self.parent_view.build_ui()
        await interaction.response.edit_message(embed=embed, view=view)