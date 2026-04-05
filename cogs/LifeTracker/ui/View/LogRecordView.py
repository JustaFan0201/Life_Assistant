# cogs\LifeTracker\ui\View\LogRecordView.py
import discord
from discord import ui
from datetime import datetime
from cogs.LifeTracker.ui.Button import FillRecordBtn, SubmitRecordBtn, BackToDetailBtn
from cogs.LifeTracker.ui.Select import SubcatSelect
from cogs.Base import LockableView

from config import TW_TZ
        
class LogRecordView(LockableView):
    def __init__(self, bot, category_id: int, cat_info: dict, subcats_info: list):
        super().__init__(timeout=None)
        self.bot = bot
        self.category_id = category_id
        self.cat_info = cat_info
        self.subcats_info = subcats_info
        self.error_msg = None

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
        """根據目前的狀態 (是否有錯誤、是否已填寫) 渲染 Embed"""
        color = discord.Color.red() if self.error_msg else discord.Color.blue()
        
        embed = discord.Embed(
            title=f"📝 新增紀錄：{self.cat_info['name']}",
            color=color
        )

        if self.error_msg:
            embed.add_field(name="⚠️ 輸入錯誤", value=f"```diff\n- {self.error_msg}\n```", inline=False)

        # 標籤顯示邏輯
        if self.selected_subcat_id:
            sub_name = next((s['name'] for s in self.subcats_info if s['id'] == self.selected_subcat_id), "未知標籤")
        else:
            sub_name = "其他" 
        
        val_text = "\n".join([f"• **{k}**: {v}" for k, v in self.input_values.items()]) if self.input_values else "尚未填寫"

        embed.add_field(name="📅 紀錄日期", value=f"`{self.record_time}`", inline=False)
        embed.add_field(name="🏷️ 選取標籤", value=f"`{sub_name}`", inline=False)
        embed.add_field(name="🔢 數值內容(正數)", value=val_text, inline=False)
        embed.add_field(name="📝 備註", value=self.note if self.note else "無", inline=False)

        required_fields = self.cat_info['fields'][:3]
        can_submit = all(f in self.input_values and self.input_values[f] for f in required_fields)
        
        self.btn_fill.disabled = False
        self.btn_back.disabled = False
        
        self.btn_submit.disabled = not can_submit or self.error_msg is not None

        for item in self.children:
            if isinstance(item, ui.Select):
                item.disabled = False

        return embed, self