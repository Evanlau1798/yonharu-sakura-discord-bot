import discord
from discord.ext import commands
from discord import default_permissions,option
from discord import SlashCommandOptionType as type
from utils.EmbedMessage import SakuraEmbedMsg
from utils.conversation import WordCounter
import os

class EventsListener(commands.Cog):
    def __init__(self, bot:discord.Bot):
        self.bot = bot
        self.conv = WordCounter()

    @commands.slash_command(description="查看個人伺服器總字數排名")
    @option("user", type=type.user, description="標記以查詢指定帳號", required=False)
    async def rank(self,message: discord.ApplicationContext,user:discord.User=None):
        await message.defer()
        if user == None:
            user = message.author
        embed = SakuraEmbedMsg()
        embed.set_author(name=user.display_name + "#" + user.discriminator,icon_url=user.display_avatar.url)
        try:
            (level,xp_current_level,xp_next_level) = self.conv.getRank(user,message.guild.id)
            embed.add_field(name="等級為",value=str(level),inline=False)
            embed.add_field(name=f"經驗值:({xp_current_level}/{xp_next_level})",value=self.conv.drawProgressBar(xp_current_level,xp_next_level),inline=False)
        except:
            embed.add_field(name="尋找失敗",value="該使用者為機器人或沒有說過任何一句話")
        await message.respond(embed=embed)

    @commands.slash_command(description="查看本伺服器總字數排名")
    async def leaderboard(self,message: discord.ApplicationContext):
        await message.defer()
        if self.conv.drawGuildRankQuery(message=message):
            embed = SakuraEmbedMsg(title=f"{str(message.guild.name)}的伺服器等級排名")
            file = discord.File(f"./rank_tmp/{str(message.guild.id)}.png", filename="rank.png")
            embed.set_image(url=f"attachment://rank.png")
            await message.respond(embed=embed, file=file)
            file.close()
            os.remove(f"./rank_tmp/{str(message.guild.id)}.png")
        else:
            embed = SakuraEmbedMsg()
            embed.add_field(name="錯誤",value="這裡居然沒有人講過話...")
            await message.respond(embed=embed)
        return

    @commands.Cog.listener()
    async def on_message(self, message:discord.Message):
        if message.author.bot == True:  # 排除自己的訊息
            return
        await self.conv.analyzeText(message=message)

def setup(bot:discord.Bot):
    bot.add_cog(EventsListener(bot))