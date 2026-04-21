import discord
from cogs.BasicDiscordObject import SafeButton

class DeleteContactBtn(SafeButton): # 保留 SafeButton 防止連點刪除
    def __init__(self, cog, user_id, nickname):
        super().__init__(label="刪除聯絡人", style=discord.ButtonStyle.danger, emoji="🗑️")
        self.cog = cog
        self.user_id = user_id
        self.nickname = nickname

    async def do_action(self, interaction: discord.Interaction):
        result = self.cog.db_manager.delete_contact(self.user_id, self.nickname)
        # ✅ 使用 edit_original_response，因為 response 已經被 SafeButton 的鎖定消耗了
        await interaction.edit_original_response(content=result, view=None)