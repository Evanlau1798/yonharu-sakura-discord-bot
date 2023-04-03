import discord

class PsCommands(object):
    def __init__(self,bot) -> None:
        self.bot = bot
        self.prefix = "! "

    async def select_commands(self,message: discord.Message):
        command = message.content.split(" ")[1]
        if 'send' == command:
            await self.send(message=message)

    async def send(self, message: discord.Message):
        if message.author.id == 540134212217602050 and message.content.startswith(f"{self.prefix}send "):
            content = message.content.removeprefix(f"{self.prefix}send ")
            if message.channel.type != discord.ChannelType.private:
                await message.delete()

            if message.reference and message.reference.cached_message:
                await message.reference.cached_message.reply(content)
            else:
                await message.channel.send(content)
        else:
            mention = f'<@!540134212217602050>'
            author = f'<@{message.author.id}>'
            await message.reply(f"{mention}，{author}在亂玩指令")