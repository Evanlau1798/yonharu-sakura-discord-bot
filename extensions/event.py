import discord
from discord.ext import commands
from utils.EmbedMessage import SakuraEmbedMsg
import utils.conversation as conv

class EventsListener(commands.Cog):
    def __init__(self, bot:discord.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message:discord.Message):
        if message.author.bot == True:  # 排除自己的訊息
            return
        conv.print_ctx(message=message)

    


def setup(bot:discord.Bot):
    bot.add_cog(EventsListener(bot))