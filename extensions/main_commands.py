import discord
from discord import default_permissions,option,is_nsfw
from discord import SlashCommandOptionType as type
from discord.ext import commands,tasks
from discord.commands import SlashCommandGroup
from discord.ui import InputText,Select,view
from random import choice
import time
from datetime import datetime
import os
import utils.help as help
from googletrans import Translator
import requests
import pixivpy3
import random
from bs4 import BeautifulSoup
from utils.EmbedMessage import SakuraEmbedMsg
from utils.conversation import XPCounter
import sqlite3


PATH = os.path.join(os.path.dirname(__file__))
translator = Translator()
api_key = '576bfa89b78416c5bb19d6bc92f97a1e'
base_url = "http://api.openweathermap.org/data/2.5/weather?"
_REFRESH_TOKEN = 'eiDaafkFze2rPaw-X2yaOXdiGpwpNpwvrIr_1jVTQww'
pinnedMsgDB = sqlite3.connect(f"./databases/PinnedMsg.db")
pinnedMsgDB_cursor = pinnedMsgDB.cursor()

class MainCommands(commands.Cog):
    def __init__(self, bot:discord.Bot):
        self.bot = bot

    @commands.slash_command(description="ping")
    async def ping(self, message: discord.ApplicationContext):
        await message.respond(f"延遲:{round(self.bot.latency*1000)}ms")

    @commands.slash_command(description="翻譯任何語言至繁體中文(吧?")
    @option("text", type=type.string, description="欲翻譯的文字", required=False)
    @option("url", type=type.string, description="欲翻譯的discord文字連結", required=False)
    async def trans(self,message: discord.ApplicationContext, text=None, url: str=None):
        if text != None:
            output = translator.translate(text, dest='zh-tw').text
            embed = SakuraEmbedMsg()
            embed.add_field(name="原文",value=text,inline=False)
            embed.add_field(name="翻譯",value=output,inline=False)
            await message.respond(embed=embed)
            return
        elif url != None and "https://discord.com/channels/" in url:
            raw_url = url.split("/")
            channel = int(raw_url[len(raw_url) - 2])
            msg_id = int(raw_url[len(raw_url) - 1])
            channel = self.bot.get_channel(channel)
            msg = await channel.fetch_message(msg_id)
            output = translator.translate(msg.content, dest='zh-tw').text
            embed = SakuraEmbedMsg()
            name = msg.author.display_name + "#" + msg.author.discriminator
            embed.add_field(name="原文",value=msg.content,inline=False)
            embed.add_field(name="翻譯",value=output,inline=False)
            embed.set_author(name=name, icon_url=msg.author.display_avatar.url,url=url)
            await message.respond(embed=embed, ephemeral=True)
            return
        else:
            await message.respond(embed = SakuraEmbedMsg(title="錯誤",description="請至少輸入一個翻譯來源"), ephemeral=True)

    @commands.message_command(name="翻譯至繁體中文(Google翻譯)")
    async def msg_trans(self,ctx:discord.ApplicationContext,message: discord.Message):
        output = translator.translate(message.content, dest='zh-tw').text
        embed = SakuraEmbedMsg()
        name = message.author
        embed.add_field(name="原文",value=message.content,inline=False)
        embed.add_field(name="翻譯",value=output,inline=False)
        embed.set_author(name=name, icon_url=message.author.display_avatar.url,url=message.jump_url)
        await ctx.respond(embed=embed, ephemeral=True)

    @commands.message_command(name="儲存並訂選此訊息")
    async def pin_msg(self,ctx:discord.ApplicationContext,message: discord.Message):
        GuildID = message.guild.id
        PinnedBy = ctx.author.id
        msg_id = message.id
        MsgLink = message.jump_url
        msg_content = message.content
        msg_by = message.author.id
        embed = SakuraEmbedMsg()
        embed.set_author(name=message.author, icon_url=message.author.display_avatar.url)
        embed.add_field(name=msg_content[:256],value=f"已儲存該訊息\n[訊息連結]({MsgLink})")
        await ctx.respond(embed=embed)
        x = (GuildID,PinnedBy,msg_id,msg_by,MsgLink,msg_content)
        pinnedMsgDB_cursor.execute("INSERT OR IGNORE INTO PinnedMsg VALUES(?,?,?,?,?,?)",x)
        pinnedMsgDB.commit()

    @commands.slash_command(description="查詢已儲存的消息")
    async def pinnedmsg(self,message: discord.ApplicationContext):
        view = PinnedMsgView(guildID=message.guild.id)
        if view.stat != False:
            embed = SakuraEmbedMsg(title="請選則欲察看的訊息")
            await message.respond(view=view,embed=embed)
        else:
            embed = SakuraEmbedMsg(title="錯誤",description="請先使用應用程式訊息選單釘選訊息後\n再使用此功能")
            await message.respond(embed=embed, ephemeral=True)
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
        
    @commands.slash_command(description="有問題就問問我吧！我可以幫你解答的😆")
    @option("question", type=type.string, description="請輸入您想問的問題", required=True)
    async def pool(self,message: discord.ApplicationContext,question):
        name = message.author.name
        conv = ['一定的', '沒有異議', '你會依靠他的', '好喔',
                '你不會想知道的', '基於我的看法:不要！', '不要。', '你要確定誒',
                '不好說', '等等再問我吧', '好問題，我需要思考一下', '我現在沒辦法決定🤔']
        await message.respond(f'對於{name[0]}的問題:\n{question}\n我的回答是:{random.choice(conv)}')

    @commands.slash_command(description="開車囉!")
    @option("number", type=type.integer, description="以此數字搜索指定漫畫(0為隨機)", required=False)
    @is_nsfw()
    async def n(self,message: discord.ApplicationContext,number=0):
        try:
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
                embed = SakuraEmbedMsg(title=title)
                embed.set_image(url=image)
                embed.add_field(name="漫畫連結", value=url, inline=False)
                await sended_message.edit_original_response(embed=embed,content="")
                return
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

    @commands.slash_command(description="查看可用指令")
    async def help(self,message: discord.ApplicationContext):
        embed = SakuraEmbedMsg(title="指令使用說明", description="讓您了解如何活用我的力量!")
        view = help.HelpView()
        view.set_message(await message.respond(embed=embed, view=view, ephemeral=True))
    
    @commands.slash_command(description="啟動或關閉伺服器等級身分組功能")
    @default_permissions(administrator=True)
    @option("options", type=type.string, description="問題", required=True, choices=['開啟','關閉'])
    async def rankrole(self,message: discord.ApplicationContext,options):
        start_time = time.time()
        xp_counter = XPCounter(bot=self.bot)
        if options == "開啟":
            if xp_counter.XPCounter_DB_cursor.execute(f"SELECT * FROM RankRoleEnabledGuild WHERE Guild_id = {message.guild_id}").fetchone() == None:
                await xp_counter.create_rank_role(message=message)
                await message.respond(embed=SakuraEmbedMsg(title="成功",description="伺服器等級身分組功能已開啟"))
            else:
                await message.respond(embed=SakuraEmbedMsg(title="錯誤",description="伺服器等級身分組功能已開啟\n請手動調整身分組至想放的位置"))
        elif options == "關閉":
            if await xp_counter.delete_rank_role(message=message):
                await message.respond(embed=SakuraEmbedMsg(title="成功",description="伺服器等級身分組功能已關閉"))
            else:
                await message.respond(embed=SakuraEmbedMsg(title="錯誤",description="伺服器等級身分組功能未開啟"))
        else:
            await message.respond(embed=SakuraEmbedMsg(title="錯誤",description="錯誤的選項\n請再試一次"))
        end_time = time.time()
        print(end_time-start_time)

class PinnedMsgView(discord.ui.View):
    def __init__(self,guildID = None):
        super().__init__(timeout=None)
        self.guildID = guildID
        self.stat = True
        if not guildID:
            return
        output = pinnedMsgDB_cursor.execute("SELECT * from PinnedMsg WHERE GuildID = ? ",(guildID,)).fetchall()
        if len(output) == 0:
            self.stat = False
            return
        options = []
        for GuildID,PinnedBy,msg_id,msg_by,MsgLink,msg_content in output:
            options.append(discord.SelectOption(label=msg_content[:100], description=f"訊息ID:{msg_id}",value=MsgLink))
        self.select = discord.ui.Select(placeholder="請選擇訊息",options=options,custom_id="Pinned_Msg_View")
        self.select.callback = self.select_callback
        self.add_item(item=self.select)

    async def select_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        url = interaction.data["values"][0]
        GuildID,PinnedBy,msg_id,msg_by,MsgLink,msg_content = pinnedMsgDB_cursor.execute("SELECT * from PinnedMsg WHERE MsgLink = ?",(url,)).fetchone()
        embed = SakuraEmbedMsg(title=f"{interaction.guild}的釘選訊息",description=msg_content)
        embed.add_field(name="訊息發送者",value=f"<@{msg_by}>",inline=False)
        embed.add_field(name="釘選訊息者",value=f"<@{PinnedBy}>",inline=False)
        embed.add_field(name="訊息連結",value=f"[點我前往]({MsgLink})",inline=False)
        await interaction.message.edit(embed=embed)

def setup(bot:discord.Bot):
    bot.add_cog(MainCommands(bot))