import discord
from discord import ui
from datetime import datetime, timezone, timedelta

from config import TW_TZ
MAX_VALUE = 1000000
class InputValueModal(ui.Modal):
    def __init__(self, parent_view, fields: list):
        super().__init__(title="⌨️ 填寫數值與備註")
        self.parent_view = parent_view 
        
        self.field_inputs = {}
        
        for f in fields[:3]: 
            text_input = ui.TextInput(label=f+"(最大值: {:,})".format(MAX_VALUE), required=True, max_length=50)
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
        
        invalid_fields = []
        overflow_fields = []
        temp_values = {}
        
        self.parent_view.error_msg = None

        for f_name, input_ui in self.field_inputs.items():
            val = input_ui.value.strip()
            try:
                num = float(val)
                if num < 0:
                    invalid_fields.append(f_name)
                elif num > MAX_VALUE:
                    overflow_fields.append(f_name)
                else:
                    temp_values[f_name] = str(int(num) if num.is_integer() else num)
            except ValueError:
                invalid_fields.append(f_name)

        # --- 錯誤訊息優先順序處理 ---
        if invalid_fields:
            self.parent_view.error_msg = f"❌ 欄位 {', '.join(invalid_fields)} 格式錯誤，請輸入正數。"
        elif overflow_fields:
            self.parent_view.error_msg = f"⚠️ 數值過大！{', '.join(overflow_fields)} 不能超過 {MAX_VALUE:,}。"
        else:
            # 日期檢查邏輯維持不變...
            time_val = self.time_input.value.strip()
            try:
                datetime.strptime(time_val, "%Y/%m/%d")
                for f_name, final_val in temp_values.items():
                    self.parent_view.input_values[f_name] = final_val
                self.parent_view.note = self.note_input.value.strip()
                self.parent_view.record_time = time_val
            except ValueError:
                self.parent_view.error_msg = "❌ 日期格式錯誤 (應為 YYYY/MM/DD)。"

        embed, view = self.parent_view.build_ui()
        await interaction.response.edit_message(embed=embed, view=view)