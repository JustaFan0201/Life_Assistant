import discord
from discord import ui
from datetime import datetime
from config import TW_TZ
from cogs.BasicDiscordObject import ValidatedModal # 💡 引入你的父類

MAX_VALUE = 1000000
class InputValueModal(ValidatedModal):
    def __init__(self, parent_view, fields: list):
        super().__init__(title="⌨️ 填寫數值與備註")
        self.parent_view = parent_view 
        self.field_inputs = {}
        # 動態生成數值輸入欄位
        for f in fields[:3]: 
            text_input = ui.TextInput(
                label=f + f"(最大值: {MAX_VALUE:,})", 
                required=True, 
                max_length=10
            )
            if f in parent_view.input_values:
                text_input.default = parent_view.input_values[f]
            self.field_inputs[f] = text_input
            self.add_item(text_input)

        # 日期輸入欄位
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

        # 備註欄位
        self.note_input = ui.TextInput(
            label="備註 (選填)", 
            required=False, 
            max_length=50
        )
        if parent_view.note:
            self.note_input.default = parent_view.note
        self.add_item(self.note_input)

    async def validate_logic(self, interaction: discord.Interaction) -> str:
        """💡 專門負責檢查數據，回傳字串會自動觸發 10秒消失訊息"""
        
        # A. 檢查各項數值
        for f_name, input_ui in self.field_inputs.items():
            val_str = input_ui.value.strip()
            # 利用父類的 check_range 工具
            error = self.check_range(val_str, min_val=0, max_val=MAX_VALUE, field_name=f_name)
            if error:
                return error

        # B. 檢查日期格式
        time_val = self.time_input.value.strip()
        try:
            datetime.strptime(time_val, "%Y/%m/%d")
        except ValueError:
            return "日期格式錯誤 (應為 YYYY/MM/DD)。"

        return None # 通過校驗

    async def do_action(self, interaction: discord.Interaction):
        """💡 校驗通過後，更新 parent_view 並刷新介面"""
        
        # 1. 更新數值 (此時已經確定資料格式正確)
        for f_name, input_ui in self.field_inputs.items():
            num = float(input_ui.value.strip())
            # 格式化數字：整數去掉 .0，浮點數保留
            final_val = str(int(num) if num.is_integer() else num)
            self.parent_view.input_values[f_name] = final_val

        # 2. 更新備註與日期
        self.parent_view.note = self.note_input.value.strip()
        self.parent_view.record_time = self.time_input.value.strip()
        
        # 3. 清除之前的錯誤訊息 (如果有)
        self.parent_view.error_msg = None

        # 4. 刷新原本的 View 介面
        embed, view = self.parent_view.build_ui()
        await interaction.response.edit_message(embed=embed, view=view)