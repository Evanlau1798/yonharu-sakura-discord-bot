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
import random
from bs4 import BeautifulSoup
from utils.EmbedMessage import SakuraEmbedMsg
from utils.word_count import count
from utils.game import game

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
            embed = SakuraEmbedMsg(title=f"這是在 {city_name} 的天氣")
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
                await message.respond('最多只能查詢30張圖片喔', ephemeral=True)
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
            await message.respond('pixiv上沒有關於這個關鍵字的圖片喔', ephemeral=True)
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
    @default_permissions(administrator=True)
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
    @default_permissions(administrator=True)
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
        
    @commands.slash_command(description="設定指定的語音頻道為動態語音創建用語音頻道")
    @option("channel", type=type.channel, description="頻道名稱", required=True)
    @default_permissions(administrator=True)
    async def dvcset(self,message: discord.ApplicationContext,channel:discord.VoiceChannel):
        if message.author.guild_permissions.manage_channels or str(message.author.id) == '540134212217602050':
            c = open(f'{PATH}/channelID/DV_ChannelID.txt', 'r')
            temp = eval(c.read())
            c.close()
            if str(channel.id) in str(temp):
                await message.respond('此頻道已登記', ephemeral=True)
                return
            channel = self.bot.get_channel(int(channel.id))
            if channel != None:
                f = open(f'{PATH}/channelID/DV_ChannelID.txt', 'w')
                temp.append(str(channel.id))
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
        
    @commands.slash_command(description="有問題就問問我吧！我可以幫你解答的😆")
    @option("question", type=type.string, description="請輸入您想問的問題", required=True)
    async def pool(self,message: discord.ApplicationContext,question):
        name = str(message.author).split('#')
        conv = ['一定的', '沒有異議', '你會依靠他的', '好喔',
                '你不會想知道的', '基於我的看法:不要！', '不要。', '你要確定誒',
                '不好說', '等等再問我吧', '好問題，我需要思考一下', '我現在沒辦法決定🤔']
        await message.respond(f'對於{name[0]}的問題:\n{question}\n我的回答是:{random.choice(conv)}')

    @commands.slash_command(description="開車囉!")
    @option("number", type=type.integer, description="以此數字搜索指定漫畫(0為隨機)", required=False)
    async def n(self,message: discord.ApplicationContext,number=0):
        try:
            if message.channel.is_nsfw() == True or str(message.author.id) == '540134212217602050':
                sended_message = await message.respond('查詢中...')
                black_list=[228922]
                while True:
                    if int(number) in black_list:
                        await sended_message.edit_original_response(content="不受理此號碼")
                        return
                    if int(number) == 0:
                        number = str(random.randint(1, 400000))
                    else:
                        number = str(number)
                    url = "https://nhentai.net/g/" + number
                    search_obj = requests.get(f"https://translate.google.com/translate?sl=vi&tl=en&hl=vi&u={url}&client=webapp")
                    if search_obj.status_code == 404:
                        if int(number) == 0:
                            continue
                        else:
                            await sended_message.edit_original_response(content="查詢錯誤，此漫畫不存在。")
                        return
                    Soup = BeautifulSoup(search_obj.text,'html.parser')
                    title = Soup.title.string.replace(" » nhentai: hentai doujinshi and manga","")
                    image = Soup.find("meta", itemprop="image").get('content')  
                    embed = SakuraEmbedMsg(title=title, color=0xd98d91)
                    embed.set_image(url=image)
                    embed.add_field(name="漫畫連結", value=url, inline=False)
                    await sended_message.edit_original_response(embed=embed,content="")
                    return
            else:
                await message.respond("不可以色色!", ephemeral=True)
        except Exception as e:
            await message.respond(str(e), ephemeral=True)

    @commands.slash_command(description="擲骰子")
    @option("max_number", type=type.integer, description="指定最大的數(空白預設為6)", required=False)
    @option("min_number", type=type.integer, description="指定最小的數(空白預設為1)", required=False)
    async def roll(self,message: discord.ApplicationContext,max_number=6,min_number=0):
        if max_number < min_number:
            embed = SakuraEmbedMsg(title="錯誤",description=f"最小的數大於最大的數")
            await message.respond(embed=embed, ephemeral=True)
            return
        embed = SakuraEmbedMsg(title="擲骰子",description=f"您擲到了{random.choice(range(min_number,max_number))}")
        await message.respond(embed=embed)

    @commands.slash_command(description="查看本伺服器總字數排名")
    async def leaderboard(self,message: discord.ApplicationContext):
        name=str(message.author)
        guild=int(message.guild.id)
        tmp = count.rank_query(name, guild)
        file = discord.File(f"./rank_tmp/{str(guild)}.png", filename="rank.png")
        if len(tmp) != 0:
            embed = SakuraEmbedMsg(title=f"{str(message.guild)}的伺服器總字數排名")
            embed.set_image(url=f"attachment://rank.png")
            await message.respond(embed=embed, file=file)
            os.remove(f"./rank_tmp/{str(guild)}.png")
            return
        else:
            await message.respond("這裡居然沒有人講過話...", ephemeral=True)
            return
        
    @commands.slash_command(description="查看個人伺服器總字數排名")
    @option("name", type=type.user, description="標記以查詢指定帳號", required=False)
    async def rank(self,message: discord.ApplicationContext,name=None):
        embed = SakuraEmbedMsg()
        await message.respond(embed=count.user_rank_query(name=name, guild=int(message.guild.id),message=message, embed=embed))

    @commands.slash_command(description="把人ban不見")
    @option("member", type=type.user, description="標記以指定帳號", required=False)
    @option("reason", type=type.string, description="原因", required=False)
    @default_permissions(administrator=True)
    async def ban(self,message: discord.ApplicationContext,member:discord.User,reason=None):
        if message.author.guild_permissions.administrator == True:
            await message.guild.ban(user=member, delete_message_days=0, reason = reason)
            embed = SakuraEmbedMsg(title=member.name,description=f"{member.mention}已經被ban啦")
            await message.respond(embed=embed)
        else:
            await message.respond(f"您沒有權限使用此指令", ephemeral=True)
    
    @commands.slash_command(description="把人踢不見")
    @option("member", type=type.user, description="標記以指定帳號", required=False)
    @option("reason", type=type.string, description="原因", required=False)
    @default_permissions(administrator=True)
    async def kick(self,message: discord.ApplicationContext,member:discord.User,reason=None):
        if message.author.guild_permissions.administrator == True:
            await message.guild.kick(user=member, reason = reason)
            embed = SakuraEmbedMsg(title=member.name,description=f"{member.mention}已經被踢啦")
            await message.respond(embed=embed)
        else:
            await message.respond(f"您沒有權限使用此指令", ephemeral=True)

    @commands.slash_command(description="創建問題並進行投票吧!")
    @option("quetion", type=type.string, description="問題", required=True)
    @option("choice1", type=type.string, description="選項一", required=True)
    @option("choice2", type=type.string, description="選項二", required=False)
    @option("choice3", type=type.string, description="選項三", required=False)
    @option("choice4", type=type.string, description="選項四", required=False)
    @option("choice5", type=type.string, description="選項五", required=False)
    @option("choice6", type=type.string, description="選項六", required=False)
    @option("choice7", type=type.string, description="選項七", required=False)
    @option("choice8", type=type.string, description="選項八", required=False)
    @option("choice9", type=type.string, description="選項九", required=False)
    @option("choice10", type=type.string, description="選項十", required=False)
    async def poll(self,message: discord.ApplicationContext,quetion,choice1,
                   choice2=None,choice3=None,choice4=None,choice5=None,choice6=None,
                   choice7=None,choice8=None,choice9=None,choice10=None):
        choices = ""
        choices_amount = 0
        choices_emoji = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
        if choice1 != None:
            choices = choices + f"1️⃣:{choice1}\n"
            choices_amount+=1
        if choice2 != None:
            choices = choices + f"2️⃣:{choice2}\n"
            choices_amount+=1
        if choice3 != None:
            choices = choices + f"3️⃣:{choice3}\n"
            choices_amount+=1
        if choice4 != None:
            choices = choices + f"4️⃣:{choice4}\n"
            choices_amount+=1
        if choice5 != None:
            choices = choices + f"5️⃣:{choice5}\n"
            choices_amount+=1
        if choice6 != None:
            choices = choices + f"6️⃣:{choice6}\n"
            choices_amount+=1
        if choice7 != None:
            choices = choices + f"7️⃣:{choice7}\n"
            choices_amount+=1
        if choice8 != None:
            choices = choices + f"8️⃣:{choice8}\n"
            choices_amount+=1
        if choice9 != None:
            choices = choices + f"9️⃣:{choice9}\n"
            choices_amount+=1
        if choice10 != None:
            choices = choices + f"🔟:{choice10}\n"
            choices_amount+=1
        embed = SakuraEmbedMsg(description=choices)
        embed.set_author(name=quetion,icon_url=message.author.avatar.url)
        embed.add_field(name="投票建立者", value=message.author.mention, inline=False)
        msg:discord.Message = await message.channel.send(embed=embed)
        await message.respond("已建立投票", ephemeral=True)
        for i in range(choices_amount):
            await msg.add_reaction(choices_emoji[i])
        return
    
    @commands.slash_command(description="遊玩小遊戲!")
    @option("difficulty", type=type.integer, description="自訂難度(預設為100)", required=False)
    async def game(self,message: discord.ApplicationContext,difficulty=100):
        await message.response.defer()
        global quetion
        if difficulty >= 1:
            quetion_message = await message.respond(f"猜猜看究竟是0~{difficulty}中哪一個數吧!\n(回覆此訊息以猜測，限時45秒)")
            quetion = game(quetion_message.id,difficulty)
        else:
            await message.respond(f"無效的難度，難度需大於1({difficulty})")

    
    

def setup(bot:discord.Bot):
    bot.add_cog(MainCommands(bot))