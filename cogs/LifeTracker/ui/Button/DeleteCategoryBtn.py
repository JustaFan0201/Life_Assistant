import discord
from discord import ui
from cogs.LifeTracker.utils import LifeTracker_Manager


class DeleteCategoryBtn(ui.Button): 
    def __init__(self, bot, categories, label="刪除主分類", emoji="➖", row=1):
        super().__init__(label=label, style=discord.ButtonStyle.danger, emoji=emoji, row=row)
        self.bot = bot
        self.categories = categories

    
    async def callback(self, interaction: discord.Interaction):
        embed, view = self.create_dashboard()
        await interaction.response.edit_message(embed=embed, view=view)
    

    def create_dashboard(self):
        if not self.categories:
            embed = discord.Embed(
                title = "📔 生活日記 - ⚠️ 無法刪除",
                description = "**❌ 目前沒有其他自訂分類可以刪除喔！(預設的「消費」分類受到系統保護)**\n\n",
                color = discord.Color.red()
            )

            print("test_view: ")
            print(self.view)

            return embed, self.view
        
        from cogs.LifeTracker.ui.View.DeleteCategorySelectView import DeleteCategorySelectView
        view = DeleteCategorySelectView(self.bot, self.categories)
        embed = discord.Embed(
            title="⚠️ 刪除主分類",
            description="請從下方選單選擇要刪除的分類。\n**注意：這會連同該分類下的所有紀錄與標籤一併刪除！**",
            color=discord.Color.red()
        )
        return embed, view
    

    @staticmethod
    def get_Btn_with_user_id(bot, user_id):
        deletable_categories = LifeTracker_Manager.get_deletable_categories(user_id=user_id)
        return DeleteCategoryBtn(bot, deletable_categories)