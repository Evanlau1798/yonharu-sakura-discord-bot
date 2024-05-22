import discord
import sqlite3
import time
from utils.EmbedMessage import SakuraEmbedMsg
import asyncio,threading,io
import extensions.channel_events as events
from extensions.search import GoogleSearch

class PsCommands(object):
    def __init__(self,bot) -> None:
        self.bot = bot
        self.prefix = "! "
        self.command_dict = {
            "send": self.send,
            "sqladd": self.sqladd,
            "sqldel": self.sqldel
        }
            

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
        
class TagCommands(object):
    def __init__(self,bot) -> None:
        self.bot:discord.Client = bot
        self.command_dict = {
            "幫我釘選": self.ping_msg,
            "runcode": self.run_code
        }
        self.pinnedMsgDB = sqlite3.connect(f"./databases/PinnedMsg.db")
        self.pinnedMsgDB_cursor = self.pinnedMsgDB.cursor()

    async def select_commands(self,message: discord.Message):
        command = message.content.split("<@909796683418832956>")[1]
        if "\n" in command:
            command = command.split("\n")[0].replace(" ","")
        else:
            command = command.replace(" ","")
        func = self.command_dict.get(command)
        if func is not None:
            await func(message=message)
        else:
            try:
                await message.channel.trigger_typing()
                await events.AiChat.singleChat(content=command,message=message, bot=self.bot)
            except Exception as e:
                await message.reply(embed=SakuraEmbedMsg(title="訊息無法傳送",description=str(e.args[0])))

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

    def run_code_thread(self, code_text, message):
        output_io = io.StringIO()
        try:
            locals_dict = {}
            globals_dict = {"print": lambda *args, **kwargs: print(*args, file=output_io, **kwargs)}
            exec(code_text, globals_dict, locals_dict)
            output = output_io.getvalue()
            embed=SakuraEmbedMsg(title="程式執行測試",description=f"```{code_text}```")
            embed.add_field(name="程式執行結果",value=output)
            asyncio.run_coroutine_threadsafe(message.reply(embed=embed), self.bot.loop)
            return output
        except Exception as e:
            error_message = str(e)
            embed=SakuraEmbedMsg(title="程式執行測試",description=f"```{code_text}```")
            embed.add_field(name="程式執行過程發生錯誤",value=error_message)
            asyncio.run_coroutine_threadsafe(message.reply(embed=embed), self.bot.loop)

    async def search(self, message: discord.Message):
        content = message.content.removeprefix(f"<@909796683418832956> search\n")
        search = GoogleSearch()
        await message.channel.send(search.search(content))

    async def run_code(self,message: discord.Message):
        if message.author.id != 540134212217602050:
            await message.reply("您沒有權限使用此功能", ephemeral=True)
            return
        '''code_text = message.content.split("```")[1]
        t = threading.Thread(target=self.run_code_thread, args=(code_text, message))
        t.start()'''