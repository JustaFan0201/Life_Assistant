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
        error_msg = await self.validate_logic(interaction)
        
        if error_msg:
            await interaction.response.send_message(f"⚠️ {error_msg}", ephemeral=True)
            await asyncio.sleep(5)
            try:
                await interaction.delete_original_response()
            except discord.NotFound:
                # 防呆機制：如果使用者在 5 秒內自己把訊息按掉了，機器人找不到訊息會噴錯，這裡直接忽略即可
                pass  
            return
        await self.do_action(interaction)

    def check_range(self, value: str, min_val: float = None, max_val: float = None, field_name: str = "數值") -> str:
        """輔助函式：判斷數值是否在範圍內"""
        try:
            num = float(value)
        except ValueError:
            return f"{field_name}必須是有效的數字！"

        if min_val is not None and num < min_val:
            return f"{field_name}不能小於 {min_val}。"
        if max_val is not None and num > max_val:
            return f"{field_name}不能超過 {max_val:,}。"
        return None

    def check_length(self, text: str, min_len: int = 0, max_len: int = 100, field_name: str = "內容") -> str:
        """輔助函式：判斷文字長度是否超標"""
        length = len(text)
        if length < min_len:
            return f"{field_name}長度不足（至少 {min_len} 字）。"
        if length > max_len:
            return f"{field_name}長度太長（最多 {max_len} 字）。"
        return None

    async def validate_logic(self, interaction: discord.Interaction) -> str:
        """子類別需實作此函式，回傳錯誤訊息字串；若成功則回傳 None"""
        return None

    async def do_action(self, interaction: discord.Interaction):
        """校驗成功後要執行的邏輯，子類別需實作"""
        pass