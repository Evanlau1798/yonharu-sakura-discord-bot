import discord
import sqlite3
import time

class PsCommands(object):
    def __init__(self,bot) -> None:
        self.bot = bot
        self.prefix = "! "

    async def select_commands(self,message: discord.Message):
        command = message.content.split(" ")[1]
        if 'send' == command:
            await self.send(message=message)
        if 'sqladd' == command:
            await self.sqladd(message=message)
        if 'sqldel' == command:
            await self.sqldel(message=message)

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