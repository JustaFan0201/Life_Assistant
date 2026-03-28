import discord
from discord import ui
from datetime import datetime, timezone, timedelta
from cogs.LifeTracker.ui.Button import FillRecordBtn, SubmitRecordBtn, BackToDetailBtn
from cogs.LifeTracker.ui.Select import SubcatSelect

TW_TZ = timezone(timedelta(hours=8))
        
class LogRecordView(ui.View):
    def __init__(self, bot, category_id: int, cat_info: dict, subcats_info: list):
        super().__init__(timeout=None)
        self.bot = bot
        self.category_id = category_id
        self.cat_info = cat_info
        self.subcats_info = subcats_info

        self.selected_subcat_id = None
        self.input_values = {}
        self.note = ""
        self.record_time = datetime.now(TW_TZ).strftime("%Y/%m/%d")

        self.btn_fill = FillRecordBtn(self, row=1)
        self.btn_submit = SubmitRecordBtn(self, row=1)
        self.btn_back = BackToDetailBtn(self.bot, self.category_id, row=1)

        if subcats_info:
            self.add_item(SubcatSelect(self, subcats_info))
        
        self.add_item(self.btn_fill)
        self.add_item(self.btn_submit)
        self.add_item(self.btn_back)

    def build_ui(self):
        """根據狀態刷新 Embed"""
        embed = discord.Embed(
            title=f"📝 新增紀錄：{self.cat_info['name']}",
            color=discord.Color.blue()
        )
        
        # 如果有 ID，去找出對應的名稱
        if self.selected_subcat_id:
            sub_name = next((s['name'] for s in self.subcats_info if s['id'] == self.selected_subcat_id), "未知標籤")
        # 如果 ID 為 None，但 input_values 已經有資料或已經點過下拉選單
        # 為了更精準，我們檢查是否真的點了「其他」
        else:
            # 這裡簡單處理：只要有 subcats_info，且 ID 為 None，我們就視為「其他」
            sub_name = "其他" 
        
        val_text = "\n".join([f"• **{k}**: {v}" for k, v in self.input_values.items()]) if self.input_values else "尚未填寫"

        embed.add_field(name="📅 紀錄日期", value=f"`{self.record_time}`", inline=False)
        embed.add_field(name="🏷️ 選取標籤", value=f"`{sub_name}`", inline=False)
        embed.add_field(name="🔢 數值內容", value=val_text, inline=False)
        embed.add_field(name="📝 備註", value=self.note if self.note else "無", inline=False)

        required_fields = self.cat_info['fields'][:3]
        can_submit = all(f in self.input_values and self.input_values[f] for f in required_fields)
        self.btn_submit.disabled = not can_submit

        return embed, self