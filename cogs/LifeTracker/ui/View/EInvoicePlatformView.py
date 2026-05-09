import discord
from cogs.BasicDiscordObject import LockableView
from cogs.LifeTracker.ui.Button import SetupEInvoiceBtn,RefreshEInvoiceBtn,BackToDetailBtn
from cogs.LifeTracker.utils import EInvoice_Manager

class EInvoicePlatformView(LockableView):
    def __init__(self, bot, category_id: int):
        super().__init__(timeout=None)
        self.bot = bot
        self.category_id = category_id
        
        self.add_item(SetupEInvoiceBtn(bot, category_id))
        self.add_item(RefreshEInvoiceBtn(bot))
        self.add_item(BackToDetailBtn(bot, category_id,row=0))

    @staticmethod
    def create_ui(bot, user_id: int, category_id: int):
        config_data = EInvoice_Manager.get_config(user_id)

        embed = discord.Embed(
            title="🧾 財政部電子發票整合平台",
            description="在這裡管理你的手機條碼載具登入資訊。系統將會在每日清晨自動為你抓取昨日消費，並透過 AI 進行自動分類。\n您的資料會加密並儲存進資料庫，請斟酌使用。\n" ,
            color=discord.Color.green()
        )

        if config_data:
            pwd = config_data['password']
            if len(pwd) > 4:
                masked_pwd = f"{pwd[:2]}{'*' * (len(pwd) - 4)}{pwd[-2:]}"
            else:
                masked_pwd = "*" * len(pwd)

            # 處理最後抓取日期的顯示邏輯
            last_fetch = config_data.get('last_fetch_date')
            if last_fetch:
                # 如果有日期，格式化成 YYYY-MM-DD
                last_fetch_str = last_fetch.strftime("%Y-%m-%d")
            else:
                # 如果是剛綁定還沒抓過，給個友善的提示
                last_fetch_str = "尚未抓取 (請點擊下方更新按鈕或等待系統排程)"

            embed.add_field(name="📱 手機號碼", value=f"`{config_data['phone_number']}`", inline=False)
            embed.add_field(name="🔑 驗證碼 (密碼)", value=f"`{masked_pwd}`", inline=False)
            embed.add_field(name="📅 發票最新抓取至", value=f"`{last_fetch_str}`", inline=False)
            
        else:
            embed.add_field(name="⚠️ 尚未設定", value="請點擊下方「設定」按鈕綁定你的發票載具帳號。", inline=False)

        view = EInvoicePlatformView(bot, category_id)
        return embed, view