import discord
from discord import ui

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

class SafeButton(ui.Button):
    async def callback(self, interaction: discord.Interaction):
        if isinstance(self.view, LockableView):
            await self.view.lock_all(interaction)
        
        await self.do_action(interaction)

    async def do_action(self, interaction: discord.Interaction):
        pass