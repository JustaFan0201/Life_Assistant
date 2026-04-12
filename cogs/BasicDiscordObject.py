import discord
from discord import ui
import asyncio
class LockableView(ui.View):
    async def lock_all(self, interaction: discord.Interaction):
        """立即鎖定所有按鈕並推送到 Discord"""
        for item in self.children:
            if isinstance(item, (ui.Button, ui.Select)):
                item.disabled = True
        
        if not interaction.response.is_done():
            await interaction.response.edit_message(view=self)
        else:
            await interaction.edit_original_response(view=self)
    async def unlock_all(self):
        """解鎖所有按鈕（僅修改狀態，不主動推送，通常配合後續的 edit 使用）"""
        for item in self.children:
            if isinstance(item, (ui.Button, ui.Select)):
                item.disabled = False

class SafeButton(ui.Button):
    async def callback(self, interaction: discord.Interaction):
        if isinstance(self.view, LockableView):
            await self.view.lock_all(interaction)
        
        await self.do_action(interaction)

    async def do_action(self, interaction: discord.Interaction):
        pass

class ValidatedModal(ui.Modal):
    """具備自動校驗邏輯的基礎 Modal 父類"""

    async def on_submit(self, interaction: discord.Interaction):
        error_msg = await self.execute_logic(interaction)
        
        if error_msg:
            await interaction.response.send_message(f"⚠️ {error_msg}", ephemeral=True)
            await asyncio.sleep(3)
            try:
                await interaction.delete_original_response()
            except discord.NotFound:
                pass  
            return
        await self.on_success(interaction)

    async def execute_logic(self, interaction: discord.Interaction) -> str:
        """
        子類別需實作：呼叫 Manager 方法。
        成功請回傳 None，失敗請回傳 錯誤訊息字串。
        """
        return None

    async def on_success(self, interaction: discord.Interaction):
        """
        子類別需實作：邏輯執行成功後的 UI 處理。
        """
        pass