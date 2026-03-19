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

        # 如果 parent_view 已經有存過時間，就用存好的；否則抓當下的台灣時間
        default_time = getattr(parent_view, 'record_time', None)
        if not default_time:
            default_time = datetime.now(TW_TZ).strftime("%Y/%m/%d %H:%M")

        self.time_input = ui.TextInput(
            label="紀錄時間 (可修改)",
            default=default_time,
            placeholder="例如：2026/03/20 14:30",
            required=True,
            max_length=16
        )
        self.add_item(self.time_input)

        self.note_input = ui.TextInput(label="備註 (選填)", required=False, max_length=100)
        if parent_view.note:
            self.note_input.default = parent_view.note
        self.add_item(self.note_input)

    async def on_submit(self, interaction: discord.Interaction):
        # 將填寫的資料存回 parent_view 的狀態中
        for f_name, input_ui in self.field_inputs.items():
            self.parent_view.input_values[f_name] = input_ui.value.strip()
            
        self.parent_view.note = self.note_input.value.strip()
        
        # 將使用者修改後的時間也存回去
        self.parent_view.record_time = self.time_input.value.strip()

        # 刷新 parent_view 的畫面
        embed, view = self.parent_view.build_ui()
        await interaction.response.edit_message(embed=embed, view=view)