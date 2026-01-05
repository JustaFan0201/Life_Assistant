import discord
from discord import ui

class FortuneButton(ui.Button):
    def __init__(self, bot):
        super().__init__(
            label="今日運勢", 
            style=discord.ButtonStyle.blurple, 
            emoji="🔮",
            custom_id="btn_fortune_persistent"
        )
        self.bot = bot

    # 這是按鈕被點擊時觸發的事件 (相當於原本的 @ui.button 下面的函式)
    async def callback(self, interaction: discord.Interaction):
        # 1. 告訴 Discord 稍等
        await interaction.response.defer()
        # 2. 取得 GPT 模組
        fortune_cog = self.bot.get_cog("FortuneCog")
        if fortune_cog:
            await fortune_cog.process_fortune_logic(interaction)
        else:
            await interaction.followup.send("❌ 找不到運勢模組。", ephemeral=True)

class StatusButton(ui.Button):
    def __init__(self, bot):
        super().__init__(label="系統狀態", style=discord.ButtonStyle.gray, emoji="ℹ️")
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"✅ 系統運作中，延遲：{latency}ms", ephemeral=True)

class GPTChatModal(ui.Modal, title="與 AI 對話"):
    question = ui.TextInput(
        label="請輸入你的問題",
        style=discord.TextStyle.paragraph,
        placeholder="你好，請幫我解釋...",
        required=True,
        max_length=500
    )

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        reply_cog = self.bot.get_cog("ReplyCog")
        if reply_cog:
            await reply_cog.process_direct_chat(interaction, self.question.value)
        else:
            await interaction.response.send_message("❌ 找不到 GPT 模組。", ephemeral=True)

class ChatButton(ui.Button):
    def __init__(self, bot):
        super().__init__(
            label="與 AI 對話", 
            style=discord.ButtonStyle.green, 
            emoji="💬",
            custom_id="btn_chat_modal"
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(GPTChatModal(self.bot))

class ToggleReplyButton(ui.Button):
    def __init__(self, bot):
        super().__init__(
            label="自動回覆開關", 
            style=discord.ButtonStyle.secondary, 
            emoji="⚙️",
            custom_id="btn_toggle_reply"
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        reply_cog = self.bot.get_cog("ReplyCog")
        if reply_cog:
            await reply_cog.toggle_active_status(interaction)
        else:
            await interaction.response.send_message("❌ 找不到 GPT 模組。", ephemeral=True)