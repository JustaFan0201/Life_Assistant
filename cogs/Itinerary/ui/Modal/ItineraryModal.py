import discord
from datetime import datetime, timezone, timedelta
from discord import ui
from cogs.BasicDiscordObject import ValidatedModal
from cogs.Itinerary import itinerary_config as conf
class ItineraryModal(ValidatedModal):
    def __init__(self, time_data, cog):
        super().__init__(title="新增我的行程")
        self.time_data = time_data
        self.cog = cog
        
        today_day = self.time_data.get('day', '1')
        
        now = datetime.now(conf.TW_TZ)
        current_time_str = now.strftime("%H:%M")
        
        self.date_input = ui.TextInput(
            label="日期 (1-31)", 
            placeholder=f"例如: {today_day} (今天是 {today_day} 號)", 
            default=today_day,
            min_length=1, 
            max_length=2
        )
        
        self.time_input = ui.TextInput(
            label="時間 (時:分) 24小時制",
            placeholder="例如: 08:30", 
            default=current_time_str,
            min_length=4, 
            max_length=5
        )
        
        self.content_input = ui.TextInput(
            label="行程內容", 
            style=discord.TextStyle.paragraph, 
            placeholder="請輸入行程內容...",
            max_length=conf.MAX_TEXT_LENGTH
        )
        
        self.add_item(self.date_input)
        self.add_item(self.time_input)
        self.add_item(self.content_input)
    async def execute_logic(self, interaction: discord.Interaction) -> str:
        try:
            year = int(self.time_data.get('year'))
            month = int(self.time_data.get('month'))
            day = int(self.date_input.value)
            time_parts = self.time_input.value.replace('：', ':').split(':')
            
            event_time = datetime(year, month, day, int(time_parts[0]), int(time_parts[1]), tzinfo=conf.TW_TZ)
            
            clean_time = event_time.replace(tzinfo=None)
            
            success, report = await self.cog.process_data_sql(
                interaction, 
                time_obj=clean_time, 
                description=self.content_input.value,
                is_private=(self.time_data.get('privacy') == "1"),
                priority=self.time_data.get('priority', "2") 
            )
            
            self.report_message = report
            if not success:
                return report 
            return None 
            
        except ValueError:
            return "日期或時間格式輸入錯誤，請確認輸入正確數字。"
        except Exception as e:
            return f"發生未預期的錯誤：{e}"

    async def on_success(self, interaction: discord.Interaction):
        """💡 成功後切換回 Dashboard"""
        try:
            embed, view, file = self.cog.create_itinerary_dashboard_ui(interaction.user.id)
            
            embed.title = "✅ 行程新增成功！"
            embed.color = discord.Color.green()
            
            if hasattr(self, 'report_message'):
                embed.set_footer(text=f"狀態回報：{self.report_message}")

            await interaction.response.edit_message(embed=embed, view=view, attachments=[file])
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"❌ 畫面跳轉失敗：{e}", ephemeral=True)