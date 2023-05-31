import discord
import sqlite3
import time
from revChatGPT.V1 import Chatbot
from utils.EmbedMessage import SakuraEmbedMsg

class PsCommands(object):
    def __init__(self,bot) -> None:
        self.bot = bot
        self.prefix = "! "
        self.command_dict = {
            "send": self.send,
            "sqladd": self.sqladd,
            "sqldel": self.sqldel
        }
        with open("chatgpt_key","r") as key:
            self.chatbot = Chatbot(config={"access_token":key.read()})
            

    async def select_commands(self,message: discord.Message):
        command = message.content.split(" ")[1]
        func = self.command_dict.get(command)
        if func is not None:
            await func(message=message)
            return True
        else:
            return False

    async def send(self, message: discord.Message):
        content = message.content.removeprefix(f"{self.prefix}send ")
        if message.channel.type != discord.ChannelType.private:
            await message.delete()
        if message.reference and message.reference.cached_message:
            await message.reference.cached_message.reply(content)
        else:
            await message.channel.send(content)

    async def sqladd(self, message: discord.Message):
        id = message.author.id
        guild = message.guild.id
        name = f"{message.author.display_name}#{message.author.discriminator}"
        content = int(message.content.removeprefix(f"{self.prefix}sqladd "))

        with sqlite3.connect("./databases/XPCount.db") as conn:
            cursor = conn.cursor()
            xp = cursor.execute("SELECT XP FROM TextChannelXP WHERE ID = ? AND Guild = ?", (id, guild)).fetchone()[0]
            xp += content
            cursor.execute(
                "UPDATE TextChannelXP SET XP = ?, Name = ?, LastMsg = ? WHERE ID = ? AND Guild = ?",
                (xp, name, int(time.time()), id, guild)
            )
            if cursor.rowcount == 1:
                await message.delete()

    async def sqldel(self, message: discord.Message):
        id = message.author.id
        guild = message.guild.id
        name = f"{message.author.display_name}#{message.author.discriminator}"
        content = int(message.content.removeprefix(f"{self.prefix}sqldel "))

        with sqlite3.connect("./databases/XPCount.db") as conn:
            cursor = conn.cursor()
            xp = cursor.execute("SELECT XP FROM TextChannelXP WHERE ID = ? AND Guild = ?", (id, guild)).fetchone()[0]
            xp -= content
            cursor.execute(
                "UPDATE TextChannelXP SET XP = ?, Name = ?, LastMsg = ? WHERE ID = ? AND Guild = ?",
                (xp, name, int(time.time()), id, guild)
            )
            if cursor.rowcount == 1:
                await message.delete()

    async def chat(self,message: discord.Message):
        prompt = message.content
        response = ""
        try:
            for data in self.chatbot.ask(prompt):
                response = data["message"]
            return response
        except Exception as e:
            return str(e)
        
class TagCommands(object):
    def __init__(self,bot) -> None:
        self.bot = bot
        self.command_dict = {
            "幫我釘選": self.ping_msg
        }
        self.pinnedMsgDB = sqlite3.connect(f"./databases/PinnedMsg.db")
        self.pinnedMsgDB_cursor = self.pinnedMsgDB.cursor()

    async def select_commands(self,message: discord.Message):
        command = message.content.split("<@909796683418832956>")
        command = command[len(command) - 1].replace(" ","")
        func = self.command_dict.get(command)
        if func is not None:
            await func(message=message)
            return True
        else:
            return False

    async def ping_msg(self,message: discord.Message):
        ctx:discord.Message = message.reference.cached_message
        if message.reference == None:
            await message.reply(embed=SakuraEmbedMsg(title="錯誤",description="請回復欲釘選的訊息"))
            return
        elif message.reference.cached_message is None:
            await message.reply(embed=SakuraEmbedMsg(title="錯誤",description="您回復的訊息無法釘選\n請使用應用程式指令釘選該訊息"))
        GuildID = message.guild.id
        PinnedBy = message.author.id
        msg_id = ctx.id
        MsgLink = ctx.jump_url
        msg_content = ctx.content
        msg_by = ctx.author.id
        embed = SakuraEmbedMsg()
        embed.set_author(name=ctx.author, icon_url=ctx.author.display_avatar.url)
        embed.add_field(name=msg_content[:256],value=f"已儲存該訊息\n[訊息連結]({MsgLink})")
        await message.reply(embed=embed)
        x = (GuildID,PinnedBy,msg_id,msg_by,MsgLink,msg_content)
        self.pinnedMsgDB_cursor.execute("INSERT OR IGNORE INTO PinnedMsg VALUES(?,?,?,?,?,?)",x)
        self.pinnedMsgDB.commit()