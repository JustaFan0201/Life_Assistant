import discord
from discord import ui
from cogs.Gmail.ui.Button import BackToGmailDashboardBtn

class HelpView(ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id
        
        self.add_item(BackToGmailDashboardBtn(self.user_id))


    @staticmethod
    def generate_embed():
        embed = discord.Embed(title="📖 Gmail 設置與 AI 分類教學", color=0x4285F4)
        
        # 帳號綁定教學
        embed.add_field(name="1. 開啟兩步驗證", value="前往 [Google 安全設定](https://myaccount.google.com/security) 開啟兩步驗證。", inline=False)
        embed.add_field(name="2. 產生應用程式密碼", value="前往 [應用程式密碼](https://myaccount.google.com/apppasswords) 產生一組 16 位密碼並複製。", inline=False)
        embed.add_field(name="3. 進行綁定", value="返回主控台點擊「🔐 設置個人信箱」，輸入 Gmail 帳號與 16 位密碼即可。", inline=False)
        
        embed.add_field(name="✨ AI 分類怎麼用？", value="點擊「🏷️ 新增分類」，輸入想要的名稱與判斷規則。未來收到新信時，AI 就會自動幫您整理與摘要，並呈現在主控台的下拉選單中！", inline=False)
        
        return embed