import discord
from discord.ext import commands
from discord import default_permissions,option,OptionChoice
from discord import SlashCommandOptionType as type
import asyncio
from datetime import datetime
from utils.EmbedMessage import SakuraEmbedMsg
from utils.conversation import XPCounter
import os
from utils.personal_commands import PsCommands

class EventsListener(commands.Cog):
    def __init__(self, bot:discord.Bot):
        self.bot = bot
        self.conv = XPCounter()
        self.ps_commands = PsCommands(bot=self.bot)
        loop = asyncio.get_event_loop()
        loop.create_task(self.user_vioce_channel_task())

    @commands.slash_command(description="查看個人伺服器總字數排名")
    @option("user", type=type.user, description="標記以查詢指定帳號", required=False)
    @option("category", type=type.string, description="選擇欲查看的經驗類別", required=False,choices=['文字等級','語音等級'])
    async def rank(self,message: discord.ApplicationContext,user:discord.User=None,category="文字等級"):
        await message.defer()
        if user == None:
            user = message.author
        embed = SakuraEmbedMsg()
        embed.set_author(name=user.display_name + "#" + user.discriminator,icon_url=user.display_avatar.url)
        try:
            if category == "文字等級":
                (level,xp_current_level,xp_next_level) = self.conv.getRank(user,message.guild.id)
            else:
                (level,xp_current_level,xp_next_level) = self.conv.getVoiceRank(user,message.guild.id)
            embed.add_field(name=f"{category}為",value=str(level),inline=False)
            embed.add_field(name=f"經驗值:({xp_current_level}/{xp_next_level})",value=self.conv.drawProgressBar(xp_current_level,xp_next_level),inline=False)
        except:
            embed.add_field(name="尋找失敗",value="該使用者為機器人或沒有說過任何一句話")
        await message.respond(embed=embed)

    @commands.slash_command(description="查看本伺服器總字數排名")
    @option("category", type=type.string, description="選擇欲查看的經驗類別", required=False,choices=['文字等級','語音等級'])
    async def leaderboard(self,message: discord.ApplicationContext,category="文字等級"):
        await message.defer()
        if category == "文字等級":
            type = "TextChannelXP"
        else:
            type = "VoiceChannelXP"
        if self.conv.drawGuildRankQuery(message=message,type=type):
            embed = SakuraEmbedMsg(title=f"{str(message.guild.name)}的伺服器{category}排名")
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
        if message.content.startswith('!'):  # 個人指令判斷
            if message.author.id == 540134212217602050:
                await self.ps_commands.select_commands(message=message)
            else:
                mention = f'<@540134212217602050>'
                author = message.author.mention
                await message.reply(f"{mention}，{author}在亂玩指令")

    async def user_vioce_channel_task(self):
        while True:
            await asyncio.sleep(60 - datetime.now().second)
            self.conv.XPCounter_DB_cursor.execute("BEGIN TRANSACTION")
            for guild in self.bot.guilds:
                for channel in guild.voice_channels:
                    for user in channel.members:
                        self.conv.addVoiceXP(user=user,guild=guild)
            if self.conv.XPCounter_DB.in_transaction:
                self.conv.XPCounter_DB.commit()



def setup(bot:discord.Bot):
    bot.add_cog(EventsListener(bot))