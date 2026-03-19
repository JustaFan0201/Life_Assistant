import discord
from discord.ext import commands
from discord import app_commands
from .ui.View import LifeDashboardView

class LifeTracker_Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
