import discord
from datetime import datetime, timezone, timedelta
from discord import ui
from cogs.BasicDiscordObject import ValidatedModal

class ItineraryModal(ValidatedModal):
    def __init__(self, time_data, cog):
        super().__init__(title="新增我的行程")
        self.time_data = time_data
        self.cog = cog
        
        today_day = self.time_data.get('day', '1')
        
        # 動態設定 Placeholder，提示使用者今天是幾號
        self.date_input = ui.TextInput(
            label="日期 (1-31)", 
            placeholder=f"例如: {today_day} (今天是 {today_day} 號)", 
            min_length=1, 
            max_length=2
        )
        self.time_input = ui.TextInput(label="時間 (時:分) 24小時至", placeholder="例如: 08:30", min_length=4, max_length=5)
        self.content_input = ui.TextInput(label="行程內容", style=discord.TextStyle.paragraph, placeholder="請輸入行程細節...")
        
        self.add_item(self.date_input)
        self.add_item(self.time_input)
        self.add_item(self.content_input)

    async def execute_logic(self, interaction: discord.Interaction) -> str:
        try:
            year = int(self.time_data.get('year'))
            month = int(self.time_data.get('month'))
            day = int(self.date_input.value)
            time_parts = self.time_input.value.replace('：', ':').split(':')
            
            # 強制標記使用者輸入的時間為台灣時區 (UTC+8)
            tz_tw = timezone(timedelta(hours=8))
            event_time = datetime(year, month, day, int(time_parts[0]), int(time_parts[1]), tzinfo=tz_tw)
            
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
        await interaction.response.send_message(self.report_message, ephemeral=True)