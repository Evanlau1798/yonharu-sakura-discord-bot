import discord
from discord import default_permissions,option
from discord import SlashCommandOptionType as type
from discord.ext import commands,tasks
from discord.commands import SlashCommandGroup
from discord.ui import InputText,Select,view
from random import choice
import time
from datetime import datetime
import os
import help
from googletrans import Translator
import requests
import pixivpy3

PATH = os.path.join(os.path.dirname(__file__))
translator = Translator()
api_key = '576bfa89b78416c5bb19d6bc92f97a1e'
base_url = "http://api.openweathermap.org/data/2.5/weather?"
_REFRESH_TOKEN = 'eiDaafkFze2rPaw-X2yaOXdiGpwpNpwvrIr_1jVTQww'

class MainCommands(commands.Cog):
    def __init__(self, bot:discord.Bot):
        self.bot = bot

    @commands.slash_command(description="ping")
    async def ping(self, message: discord.ApplicationContext):
        await message.respond(f"延遲:{round(self.bot.latency*1000)}ms")

    @commands.slash_command(description="查看可用指令")
    @option("page", type=type.string, description="輸入要設定的身分組", required=True,choices=['一般指令','音樂相關指令','管理員專用指令','額外指令','額外功能'])
    async def help(self,message: discord.ApplicationContext,page='一般指令'):
        embed = discord.Embed(title="機器人指令使用說明", description="讓您了解如何活用我的力量!", color=0xd98d91)
        #file = discord.File(f"{PATH}/media/introduction.jpg", filename="introduction.jpg")
        embed = help.help(embed, page=page)
        await message.respond(embed=embed, ephemeral=True)#,file=file)

    @commands.slash_command(description="翻譯任何語言至繁體中文(吧?")
    @option("text", type=type.string, description="欲翻譯的文字", required=True)
    async def trans(self,message: discord.ApplicationContext,text):
        output = translator.translate(text, dest='zh-tw').text
        await message.respond(f'翻譯:{output}')
        return
    
    @commands.slash_command(description="查詢指定地區")
    @option("weather", type=type.string, description="請輸入欲查詢的地區", required=True)
    async def weather(self,message: discord.ApplicationContext,city):
        city_name = translator.translate(city, dest='EN').text
        complete_url = base_url + "appid=" + api_key + "&q=" + city_name
        response = requests.get(complete_url)
        x = response.json()
        if x["cod"] != "404":
            y = x["main"]
            current_temperature = y["temp"]
            current_temperature_celsiuis = str(round(current_temperature - 273.15))
            current_pressure = y["pressure"]
            current_humidity = y["humidity"]
            z = x["weather"]
            city_name = translator.translate(city, dest='zh-tw').text
            embed = discord.Embed(title=f"這是在 {city_name} 的天氣", color=0xd98d91)
            weather_description = translator.translate(
                z[0]["description"], dest='zh-tw').text
            embed.add_field(
                name="天氣狀況", value=f"**{weather_description}**", inline=False)
            embed.add_field(
                name="溫度（°C）", value=f"**{current_temperature_celsiuis}°C**", inline=False)
            embed.add_field(
                name="濕度(%)", value=f"**{current_humidity}%**", inline=False)
            embed.add_field(name="大氣壓力(hPa)",
                            value=f"**{current_pressure}hPa**", inline=False)
            embed.set_thumbnail(url="https://i.ibb.co/CMrsxdX/weather.png")
            embed.set_footer(text=f"要求自:{message.author.name}")
            await message.respond(embed=embed, ephemeral=True)
        else:
            await message.respond("我找不到這個城市喔😨", ephemeral=True)

    @commands.slash_command(description="在pixiv上搜尋指定關鍵字的圖片")
    @option("text", type=type.string, description="以此關鍵字在pixiv上搜尋", required=True)
    @option("num", type=type.integer, description="搜尋後的結果順位", required=False)
    async def pixiv(self,message: discord.ApplicationContext,text,num=1):
        aapi = pixivpy3.AppPixivAPI()
        search = text
        try:
            if int(num) > 30:
                await message.send('最多只能查詢30張圖片喔')
                return
            elif int(num) > 1:
                tmp = int(num) - 1
            elif int(num) == 1:
                tmp = 0
        except:
            tmp = 0
        try:
            aapi.auth(refresh_token=_REFRESH_TOKEN)
            json_result = aapi.search_illust(
                search, search_target='partial_match_for_tags')
            illust = json_result.illusts[tmp]
        except:
            await message.respond('pixiv上沒有關於這個關鍵字的圖片喔')
            return
        url = illust.image_urls['large']
        url = url.split('https://i.pximg.net', 2)
        url = 'https://pixiv.runrab.workers.dev' + url[1]
        embed = discord.Embed(color=0xd98d91)
        embed.set_image(url=url)
        embed.set_author(name=illust.title)
        await message.respond(embed=embed)

    @commands.slash_command(description="創建語音頻道")
    @option("name", type=type.string, description="頻道名稱", required=True)
    @option("num", type=type.integer, description="設定頻道人數(預設為不設限)", required=False)
    async def create(self,message: discord.ApplicationContext,name,num=0):
        voice = message.guild.voice_channels
        c = open(f'{PATH}/channelID/T_ChannelID.txt', 'r')
        temp = eval(c.read())
        if str(message.channel.id) in str(temp):
            print('相符')
        else:
            await message.respond('這個頻道無法使用此指令喔', ephemeral=True)
            return
        c.close()
        for i in voice[:len(voice)]:
            if str(i) == str(name):
                await message.respond('此頻道已存在', ephemeral=True)
                return
        await message.guild.create_voice_channel(name=name, category=message.channel.category, reason=None, user_limit=num)
        await message.respond('頻道創建成功!')
        voice = message.guild.voice_channels
        for i in voice:
            if str(name) == str(i):
                f = open(f'{PATH}/channelID/V_ChannelID.txt', 'r')
                temp = eval(f.read())
                temp.append(str(i.id))
                f.close()
                t = open(f'{PATH}/channelID/V_ChannelID.txt', 'w')
                t.write(str(temp))
                t.close()

    @commands.slash_command(description="設定目前的頻道為動態語音創建用文字頻道")
    async def vcset(self,message: discord.ApplicationContext):
        if message.author.guild_permissions.manage_channels or str(message.author.id) == '540134212217602050':
            id=str(message.channel.id)
            c = open(f'{PATH}/channelID/T_ChannelID.txt', 'r')
            temp = eval(c.read())
            c.close()
            if str(id) in str(temp):
                await message.respond('此頻道已登記', ephemeral=True)
                return
            channel = self.bot.get_channel(int(id))
            if channel != None: 
                f = open(f'{PATH}/channelID/T_ChannelID.txt', 'w')
                temp.append(str(id))
                f.write(str(temp))
                f.close()
                await message.respond(f'已設定{channel.name}為動態語音產生頻道', ephemeral=True)
                return
            else:
                await message.respond('未找到此頻道', ephemeral=True)
            return
        else:
            await message.respond('您沒有權限執行此操作', ephemeral=True)
            return
        
    @commands.slash_command(description="取消動態語音創建用文字頻道")
    async def vcdel(self,message: discord.ApplicationContext):
        id = str(message.channel.id)
        if message.author.guild_permissions.manage_channels or str(message.author.id) == '540134212217602050':
            c = open(f'{PATH}/channelID/T_ChannelID.txt', 'r')
            temp = eval(c.read())
            c.close()
            if str(id) in str(id):
                channel = self.bot.get_channel(int(id))
                if channel != None:
                    f = open(f'{PATH}/channelID/T_ChannelID.txt', 'w')
                    temp.remove(id)
                    f.write(str(temp))
                    f.close()
                    await message.respond(f'刪除{channel.name}成功')
                    return
                else:
                    await message.respond('未找到此頻道', ephemeral=True)
                    return
        else:
            await message.respond('您沒有權限執行此操作', ephemeral=True)
            return
    

    

def setup(bot:discord.Bot):
    bot.add_cog(MainCommands(bot))