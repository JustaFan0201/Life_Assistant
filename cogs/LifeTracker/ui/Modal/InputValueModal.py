import discord
from discord import ui
from datetime import datetime
from config import TW_TZ
from cogs.BasicDiscordObject import ValidatedModal
from cogs.LifeTracker.utils import LifeTracker_Manager
from cogs.LifeTracker.LifeTracker_config import (
    MAX_INPUT_VALUE,
    MAX_TEXT_LENGTH
)
class InputValueModal(ValidatedModal):
    def __init__(self, parent_view, fields: list):
        super().__init__(title="⌨️ 填寫數值與備註")
        self.parent_view = parent_view 
        self.field_inputs = {}
        # 動態生成數值輸入欄位
        for f in fields[:3]: 
            text_input = ui.TextInput(
                label=f + f"(最大值: {MAX_INPUT_VALUE:,})", 
                required=True, 
                max_length=len(str(MAX_INPUT_VALUE))
            )
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

        self.note_input = ui.TextInput(
            label="備註 (選填)", 
            required=False, 
            max_length=MAX_TEXT_LENGTH
        )
        if parent_view.note:
            self.note_input.default = parent_view.note
        self.add_item(self.note_input)

    async def execute_logic(self, interaction: discord.Interaction) -> str:
        """💡 呼叫 Manager 進行『純數據校驗』"""
        
        temp_values = {}
        for f_name, input_ui in self.field_inputs.items():
            temp_values[f_name] = input_ui.value.strip()
        
        note = self.note_input.value.strip()
        record_time = self.time_input.value.strip()

        is_valid, error_msg = LifeTracker_Manager.validate_record_data(
            self.parent_view.category_id, temp_values, note, record_time
        )
        
        if not is_valid:
            return error_msg

        return None

    async def on_success(self, interaction: discord.Interaction):
        """💡 校驗通過後，將資料同步回 View 的暫存狀態"""
        
        for f_name, input_ui in self.field_inputs.items():
            num = float(input_ui.value.strip())
            self.parent_view.input_values[f_name] = str(int(num) if num.is_integer() else num)

        self.parent_view.note = self.note_input.value.strip()
        self.parent_view.record_time = self.time_input.value.strip()
        self.parent_view.error_msg = None

        embed, view = self.parent_view.build_ui()
        await interaction.response.edit_message(embed=embed, view=view)