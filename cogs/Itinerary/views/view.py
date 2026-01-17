import discord

class MyFirstView(discord.ui.View):
    @discord.ui.button(label="按鈕文字", style=discord.ButtonStyle.green)
    async def button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("你點了我！")