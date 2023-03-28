import discord
import os
from discord.commands import SlashCommandGroup
from discord.ext import commands,tasks
from discord import SlashCommandOptionType as type
from discord import default_permissions,option
from youtube_dl import YoutubeDL

class MusicCommands(commands.Cog):  #加載機器人指令
    def __init__(self, bot:discord.Bot):
        self.bot = bot
    
    music = SlashCommandGroup("music", "音樂相關指令")
    @music.command(description="從Youtube撥放音樂!")
    @option("url", type=type.string, description="youtube網址", required=True)
    async def play(self,message: discord.ApplicationContext,url):
        url = str(url)
        channel = message.author.voice.channel
        voice = discord.utils.get(self.bot.voice_clients, guild=message.guild)
        if voice == None:
            await channel.connect()
            voice = discord.utils.get(self.bot.voice_clients, guild=message.guild)
            print(message.voice_client)
        YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
        FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        with YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
        URL = info['url']
        await message.respond('開始撥放')
        voice.play(discord.FFmpegPCMAudio(URL, **FFMPEG_OPTIONS))
        voice.is_playing()

    @music.command(description="繼續撥放音樂")
    async def resume(self,message: discord.ApplicationContext):
        voice = discord.utils.get(self.bot.voice_clients, guild=message.guild)
        if not voice == None:
            voice.resume()
            await message.respond('正在繼續撥放...')

    @music.command(description="暫停音樂")
    async def pause(self,message: discord.ApplicationContext):
        voice = discord.utils.get(self.bot.voice_clients, guild=message.guild)
        if not voice == None:
            voice.resume()
            await message.respond('音樂已暫停')

    @music.command(description="停止撥放音樂")
    async def stop(self,message: discord.ApplicationContext):
        voice = discord.utils.get(self.bot.voice_clients, guild=message.guild)
        if not voice == None:
            voice.stop()
            await message.respond('音樂已停止')


def setup(bot:discord.Bot):
    bot.add_cog(MusicCommands(bot))