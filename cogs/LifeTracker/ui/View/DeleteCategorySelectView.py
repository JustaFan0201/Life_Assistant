import discord
from discord import ui
from cogs.LifeTracker.ui.Select import DeleteCategorySelect
from cogs.LifeTracker.ui.Button import BackToLifeDashboardBtn

class DeleteCategorySelectView(ui.View):
    def __init__(self, bot, categories):
        super().__init__(timeout=60)
        self.add_item(DeleteCategorySelect(bot, categories))
        
        self.add_item(BackToLifeDashboardBtn(bot))