import discord
from discord import ui
from datetime import datetime, timezone, timedelta
from cogs.LifeTracker.utils import LifeTrackerDatabaseManager
from cogs.LifeTracker.ui.Modal import InputValueModal
TW_TZ = timezone(timedelta(hours=8))
class SubcatSelect(ui.Select):
    def __init__(self, parent_view, subcats):
        self.parent_view = parent_view
        options = [discord.SelectOption(label="無標籤", value="none")]
        for s in subcats:
            options.append(discord.SelectOption(label=s['name'], value=str(s['id'])))
            
        super().__init__(placeholder="點此選擇子分類 (標籤)", min_values=1, max_values=1, options=options[:25])

    async def callback(self, interaction: discord.Interaction):
        # 儲存選擇的標籤 ID
        val = self.values[0]
        self.parent_view.selected_subcat_id = None if val == "none" else int(val)
        
        # 刷新畫面
        embed, view = self.parent_view.build_ui()
        await interaction.response.edit_message(embed=embed, view=view)


class LogRecordView(ui.View):
    def __init__(self, bot, category_id: int, cat_info: dict, subcats_info: list):
        super().__init__(timeout=None)
        self.bot = bot
        self.category_id = category_id
        self.cat_info = cat_info
        self.subcats_info = subcats_info

        # 狀態儲存 (草稿)
        self.selected_subcat_id = None
        self.input_values = {}
        self.note = ""
        # 預設時間為當下台灣時間
        self.record_time = datetime.now(TW_TZ).strftime("%Y/%m/%d %H:%M")

        # 加入 UI 元件
        if subcats_info:
            self.add_item(SubcatSelect(self, subcats_info))
        
        self.btn_fill = ui.Button(label="填寫數值與備註", style=discord.ButtonStyle.primary, emoji="✏️", row=1)
        self.btn_fill.callback = self.open_modal
        self.add_item(self.btn_fill)

        self.btn_submit = ui.Button(label="確認送出", style=discord.ButtonStyle.success, emoji="✅", row=1)
        self.btn_submit.callback = self.submit_record
        self.add_item(self.btn_submit)

        self.btn_cancel = ui.Button(label="取消", style=discord.ButtonStyle.danger, row=1)
        self.btn_cancel.callback = self.cancel_action
        self.add_item(self.btn_cancel)

    def build_ui(self):
        """根據目前的草稿狀態產生 Embed"""
        embed = discord.Embed(
            title=f"📝 新增紀錄：{self.cat_info['name']}",
            color=discord.Color.blue()
        )
        
        # 找出選擇的標籤名稱
        sub_name = "尚未選擇 (無標籤)"
        if self.selected_subcat_id:
            sub_name = next((s['name'] for s in self.subcats_info if s['id'] == self.selected_subcat_id), "未知標籤")
        
        # 整理數值文字
        val_text = "尚未填寫"
        if self.input_values:
            val_text = "\n".join([f"• **{k}**: {v}" for k, v in self.input_values.items()])

        # 把時間顯示在畫面上
        embed.add_field(name="🕒 紀錄時間", value=f"`{self.record_time}`", inline=False)
        embed.add_field(name="🏷️ 目前選擇標籤", value=f"`{sub_name}`", inline=False)
        embed.add_field(name="🔢 輸入數值", value=val_text, inline=False)
        embed.add_field(name="📝 備註", value=self.note if self.note else "尚未填寫", inline=False)

        # 檢查是否可以送出
        can_submit = all(f in self.input_values and self.input_values[f] for f in self.cat_info['fields'][:3])
        self.btn_submit.disabled = not can_submit

        return embed, self

    async def open_modal(self, interaction: discord.Interaction):
        await interaction.response.send_modal(InputValueModal(self, self.cat_info['fields']))

    async def submit_record(self, interaction: discord.Interaction):
        try:
            # 寫入資料庫時，把 record_time 一併傳過去
            LifeTrackerDatabaseManager.add_life_record(
                user_id=interaction.user.id,
                category_id=self.category_id,
                subcat_id=self.selected_subcat_id,
                values_dict=self.input_values,
                note=self.note,
                record_time_str=self.record_time
            )
            
            from cogs.LifeTracker.ui.View import CategoryDetailView
            embed, view = CategoryDetailView.create_ui(self.bot, self.category_id, page=0)
            await interaction.response.edit_message(embed=embed, view=view)
        except Exception as e:
            await interaction.response.send_message(f"❌ 寫入失敗: {e}", ephemeral=True)

    async def cancel_action(self, interaction: discord.Interaction):
        from cogs.LifeTracker.ui.View import CategoryDetailView
        embed, view = CategoryDetailView.create_ui(self.bot, self.category_id, page=0)
        await interaction.response.edit_message(embed=embed, view=view)