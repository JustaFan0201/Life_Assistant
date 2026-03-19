import discord
from discord import ui
from cogs.LifeTracker.ui.Button import BackToLifeDashboardBtn

class CategoryDropdown(ui.Select):
    def __init__(self, bot, categories): 
        self.bot = bot
        
        options = []
        for cat in categories:
            fields_str = ", ".join(cat.fields)
            options.append(discord.SelectOption(
                label=cat.name, 
                description=f"紀錄數值: {fields_str}", 
                value=str(cat.id)
            ))
            
        super().__init__(placeholder="請選擇一個分類來查看或紀錄...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_category_id = int(self.values[0])
        
        from cogs.LifeTracker.ui.View import CategoryDetailView
        
        embed, view = CategoryDetailView.create_ui(self.bot, selected_category_id, page=0)
        await interaction.response.edit_message(embed=embed, view=view)

class CategorySelectView(ui.View):
    def __init__(self, bot, categories):
        super().__init__(timeout=None)
        self.bot = bot
        
        self.add_item(CategoryDropdown(bot, categories)) 
        self.add_item(BackToLifeDashboardBtn(bot))

    @staticmethod
    def create_ui(bot, categories):
        embed = discord.Embed(
            title="📂 你的分類紀錄",
            description="請從下方選單選擇一個你要查看或操作的分類：",
            color=discord.Color.green()
        )
        
        cat_list_text = ""
        for cat in categories:
            cat_list_text += f"• **{cat.name}** (包含欄位: `{', '.join(cat.fields)}`)\n"
            
        embed.add_field(name="目前已建立的分類", value=cat_list_text, inline=False)
        
        view = CategorySelectView(bot, categories)
        return embed, view