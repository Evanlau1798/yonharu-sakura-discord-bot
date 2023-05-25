import discord
from discord.ext import commands
from discord import default_permissions,option,OptionChoice
from discord import SlashCommandOptionType as type
from utils.EmbedMessage import SakuraEmbedMsg
from collections import deque

snipes = {} # 建立一個字典，用來儲存每個伺服器最近刪除或編輯的訊息
MAX_MESSAGES = 100 # 定義一個常數，表示每個伺服器能儲存的訊息數量上限

class SnipeEventsListener(commands.Cog):
    def __init__(self, bot:discord.Bot):
        self.bot = bot
    
    @commands.slash_command(description="查看最近被刪除的訊息")
    @option("index", type=type.integer, description="頁數索引", required=False)
    @default_permissions(administrator=True)
    async def deletesnipe(self,message: discord.ApplicationContext, index: int = 0):
        if message.guild.id in snipes:
            queue = snipes[message.guild.id]
            if 0 <= index < len(queue): # 檢查索引是否有效（介於 0 到佇列長度 - 1 之間）
                snipe_message:discord.Message = queue[index]
                embed = SakuraEmbedMsg(description=snipe_message.content)
                embed.set_author(name=snipe_message.author.display_name, icon_url=snipe_message.author.avatar.url)
                await message.respond(embed=embed)
            else:
                await message.respond(f"索引超出範圍（0-{len(queue)-1}）", ephemeral=True)
        else:
            await message.respond("沒有找到任何被刪除或編輯的訊息", ephemeral=True)

    @commands.slash_command(description="查看最近被刪除的訊息")
    @option("index", type=type.integer, description="頁數索引", required=False)
    @default_permissions(administrator=True)
    async def editsnipe(self,message: discord.ApplicationContext, index: int = 0):
        if message.guild.id in snipes:
            queue = snipes[message.guild.id]
            if 0 <= index < len(queue): # 檢查索引是否有效（介於 0 到佇列長度 - 1 之間）
                snipe_message:discord.Message = queue[index]
                embed = SakuraEmbedMsg(description=snipe_message.content)
                embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
                await message.respond(embed=embed)
            else:
                await message.respond(f"索引超出範圍（0-{len(queue)-1}）", ephemeral=True)
        else:
            await message.respond("沒有找到任何被編輯或刪除的訊息", ephemeral=True)

    @commands.Cog.listener()
    async def on_message_delete(self,message:discord.Message):
        print(message.content)
        if message.author.bot:return
        guild_id = message.guild.id
        if guild_id in snipes:
            queue = snipes[guild_id]
            queue.appendleft(message)
            if len(queue) > MAX_MESSAGES:
                queue.pop()
        else:
            queue = deque([message]) # 如果該伺服器沒有儲存的訊息，則建立一個新的雙端佇列，並將被刪除的訊息加入其中
            snipes[guild_id] = queue

    @commands.Cog.listener()
    async def on_message_edit(self,before:discord.Message, after:discord.Message):
        print("舊:",before.content,"新:",after.content)
        if before.author.bot:return
        guild_id = before.guild.id
        if guild_id in snipes:
            queue = snipes[guild_id]
            queue.appendleft(before)
            if len(queue) > MAX_MESSAGES: # 如果佇列的長度超過上限，則移除佇列的右側元素
                queue.pop()
        else:
            queue = deque([before]) # 如果該伺服器沒有儲存的訊息，則建立一個新的雙端佇列，並將被編輯的訊息加入其中
            snipes[guild_id] = queue


def setup(bot:discord.Bot):
    bot.add_cog(SnipeEventsListener(bot))