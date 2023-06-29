import random
from datetime import datetime,timezone,timedelta
import discord
import sqlite3
import time
import cv2
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from utils.EmbedMessage import SakuraEmbedMsg
import pytz

class XPCounter(object):
    def __init__(self,bot=None):
        self.XPCounter_DB = sqlite3.connect(f"./databases/XPCount.db")
        self.XPCounter_DB_cursor = self.XPCounter_DB.cursor()
        self.bot = bot

    async def analyzeText(self,message: discord.Message):
        self.print_ctx(message=message)
        if self.checkLastMsg(message=message):
            self.addXP(message=message)
            start = time.time()
            if self.XPCounter_DB_cursor.execute(f"SELECT * FROM RankRoleEnabledGuild WHERE Guild_id = {message.guild.id}").fetchone() != None:
                await self.check_role(message=message)
                end = time.time()
                print(end-start)
        return

    def checkLastMsg(self,message: discord.Message) -> bool:
        id = message.author.id
        guild = message.guild.id
        output = self.XPCounter_DB_cursor.execute(f"SELECT LastMsg from TextChannelXP where ID = {id} and Guild = {guild}").fetchone()
        if output == None:
            self.newUser(message=message)
        elif int(time.time()) - int(output[0]) < 60:
            return False
        return True

    def addXP(self,message: discord.Message):
        id = message.author.id
        guild = message.guild.id
        name = message.author.display_name + "#" + message.author.discriminator
        xp = self.XPCounter_DB_cursor.execute(f"SELECT XP from TextChannelXP where ID = {id} and Guild = {guild}").fetchone()[0]
        xp = xp + random.randint(15,35)
        self.XPCounter_DB_cursor.execute(f'UPDATE TextChannelXP SET XP = {xp}, Name = "{name}", LastMsg = "{int(time.time())}" WHERE ID = {id} AND Guild = {guild}')
        self.XPCounter_DB.commit()
    
    def getLevel(self,xp) -> int:
        level = 1
        rank_xp = 100
        while xp >= rank_xp:
            level += 1
            xp -= rank_xp
            rank_xp = 4 * level ** 2 + 50 * level + 200
        return level, int(xp), int(rank_xp)
    
    def getRank(self,user:discord.User,guild:int):
        xp = int(self.XPCounter_DB_cursor.execute(f"SELECT XP from TextChannelXP where ID = {user.id} and Guild = {guild}").fetchone()[0])
        if xp == None:
            raise ValueError("該使用者為機器人或沒有說過任何一句話")
        level,cur_xp,rank_xp = self.getLevel(xp)
        return level,cur_xp,rank_xp

    def newUser(self,message: discord.Message):
        print("New User")
        name = message.author.display_name + "#" + message.author.discriminator
        id = message.author.id
        guild = message.guild.id
        xp = random.randint(15,35)
        last_msg = int(time.time())
        x = (name,id,guild,xp,last_msg)
        self.XPCounter_DB_cursor.execute("INSERT OR IGNORE INTO TextChannelXP VALUES(?,?,?,?,?)",x)
        self.XPCounter_DB.commit()
        return
    
    def getVoiceRank(self,user:discord.User,guild:int):
        xp = int(self.XPCounter_DB_cursor.execute(f"SELECT XP from VoiceChannelXP where ID = {user.id} and Guild = {guild}").fetchone()[0])
        if xp == None:
            raise ValueError("該使用者為機器人或沒有進過任何一個語音頻道")
        level,cur_xp,rank_xp = self.getLevel(xp)
        return level,cur_xp,rank_xp

    def newVoiceUser(self,user:discord.User,guild:discord.Guild):
        print("New Voice User")
        name = user.display_name + "#" + user.discriminator
        id = user.id
        guild = guild.id
        xp = 1
        x = (name,id,guild,xp)
        self.XPCounter_DB_cursor.execute("INSERT OR IGNORE INTO VoiceChannelXP VALUES(?,?,?,?)",x)
        self.XPCounter_DB.commit()
        return
    
    def addVoiceXP(self,user:discord.User,guild:discord.Guild):
        name = user.display_name + "#" + user.discriminator
        id = user.id
        guild_id = guild.id
        if self.XPCounter_DB_cursor.execute(f"SELECT * from VoiceChannelXP where ID = {id} and Guild = {guild_id}").fetchone() == None:
            self.newVoiceUser(user=user,guild=guild)
        xp = self.XPCounter_DB_cursor.execute(f"SELECT XP from VoiceChannelXP where ID = {id} and Guild = {guild_id}").fetchone()[0]
        xp = xp + random.randint(15,25)
        self.XPCounter_DB_cursor.execute(f'UPDATE VoiceChannelXP SET XP = {xp}, Name = "{name}" WHERE ID = {id} AND Guild = {guild_id}')

    def drawProgressBar(self,min,max) -> str:
        progress = round(min / max, 2)
        filled = round(progress * 40)
        bar = "[" + "".join(["/" for _ in range(filled)]) + "".join(["-" for _ in range(40 - filled)]) + "]"
        return bar
    
    def drawGuildRankQuery(self,message: discord.Message,type:str):
        img = cv2.imread(f'./media/rank.png', cv2.IMREAD_UNCHANGED)
        rank_list = self.XPCounter_DB_cursor.execute(f"SELECT Name,XP from {type} where Guild = {message.guild.id} ORDER BY XP DESC LIMIT 10;").fetchall()
        rank_list = [list(x) for x in rank_list]       
        for i in range(len(rank_list)):
            rank_list[i][1] = f"Lv.{str(self.getLevel(rank_list[i][1])[0])}"
        if len(rank_list) != 0:
            for i,x in zip(rank_list,range(19,919,90)):
                img = self.cv2ImgAddText(img,str(i[0]),110,x,"black")
                img = self.cv2ImgAddText(img,str(i[1]),580,x,"black")
            cv2.imwrite(f'./rank_tmp/{message.guild.id}.png', img)
            return True
        else:
            return False
    
    def cv2ImgAddText(self,img, text, left, top,color):
        if (isinstance(img, np.ndarray)):
            img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2BGRA))
        draw = ImageDraw.Draw(img)
        fontStyle = ImageFont.truetype(f"./font/Iansui094-Regular.ttf", 35, encoding="utf-8")
        if fontStyle.getsize(text)[0] > 410:
            for i in range(len(list(text))+1,0,-1):
                if fontStyle.getsize(text[:i])[0] < 420:
                    text=str(text[:i]) + "..."
                    break
        draw.text((left, top), text, color, font=fontStyle)
        return cv2.cvtColor(np.asarray(img), cv2.COLOR_BGR2BGRA)

    def print_ctx(self,message: discord.Message):
        dt1 = datetime.utcnow().replace(tzinfo=timezone.utc)
        dt2 = dt1.astimezone(timezone(timedelta(hours=8))) # 轉換台灣時區
        ticks = dt2.strftime("%H:%M:%S")
        try:
            conv=str(message.author)+'於'+str(ticks)+'在'+str(message.guild.name)+'的'+str(message.channel)+'說:'+str(message.content)
        except:
            conv=str(message.author)+'於'+str(ticks)+'在'+str(message.channel)+'說:'+str(message.content)
        print(conv)

    async def create_rank_role(self,message:discord.ApplicationContext):
        await message.defer()
        guild = message.guild
        lv20 = await guild.create_role(name="Lv.20",reason="機器人等級功能創建之身分組",colour=discord.Color.from_rgb(2, 192, 192))
        lv40 = await guild.create_role(name="Lv.40",reason="機器人等級功能創建之身分組",colour=discord.Color.from_rgb(51, 102, 255))
        lv60 = await guild.create_role(name="Lv.60",reason="機器人等級功能創建之身分組",colour=discord.Color.from_rgb(153, 51, 255))
        lv80 = await guild.create_role(name="Lv.80",reason="機器人等級功能創建之身分組",colour=discord.Color.from_rgb(255, 215, 0))
        lv100 = await guild.create_role(name="Lv.100",reason="機器人等級功能創建之身分組",colour=discord.Color.from_rgb(255, 0, 0))
        x = (message.guild_id,lv20.id,lv40.id,lv60.id,lv80.id,lv100.id)
        self.XPCounter_DB_cursor.execute("INSERT OR IGNORE INTO RankRoleEnabledGuild VALUES(?,?,?,?,?,?)",x)
        self.XPCounter_DB.commit()
        return
    
    async def delete_rank_role(self,message:discord.ApplicationContext):
        await message.defer()
        guild = message.guild
        Guild_inf = self.XPCounter_DB_cursor.execute(f"SELECT * FROM RankRoleEnabledGuild WHERE Guild_id = {guild.id}").fetchone()
        if Guild_inf == None:
            return False
        guild_id,lv20,lv40,lv60,lv80,lv100 = Guild_inf
        role_ids = {lv20: None, lv40: None, lv60: None, lv80: None, lv100: None}
        Guild_roles = await guild.fetch_roles()
        for role in Guild_roles:
            if role.id in role_ids:
                await role.delete(reason="關閉機器人等級功能創建之身分組")
        self.XPCounter_DB_cursor.execute(f"DELETE FROM RankRoleEnabledGuild WHERE Guild_id = {guild.id}")
        self.XPCounter_DB.commit()
        return True
    
    async def check_role(self,message:discord.Message):
        level,cur_xp,rank_xp = self.getRank(user=message.author,guild=message.guild.id)
        guild_id, lv20, lv40, lv60, lv80, lv100 = self.XPCounter_DB_cursor.execute("SELECT * FROM RankRoleEnabledGuild WHERE Guild_id = ?", (message.guild.id,)).fetchone()
        role_ids = {20: lv20, 40: lv40, 60: lv60, 80: lv80, 100: lv100}
        guild_roles = await message.guild.fetch_roles()
        for role in guild_roles:
            if role.id in role_ids.values():
                role_ids = {level: role for level, role_id in role_ids.items() if role_id == role.id}
        for level_threshold in [20, 40, 60, 80, 100]:
            if level >= level_threshold:
                await message.author.add_roles(role_ids[level_threshold],reason="機器人等級功能之等級調整")

class HandsByeSpecialFeedback():
    def __init__(self):
        self.mod_crossdressing_emoji_used_member_list = []
        self.times = 0
        self.tz = pytz.timezone('Asia/Taipei')
        self.day = datetime.now().astimezone(self.tz).day
        self.notifi_list = ["群主 該換上女裝了，不要讓大家等太久喔~", # 1 ~ 5
                            "懇請群主趕快換上女裝，外面的賓客都已經迫不及待想見您的美麗風采了呢！", # 6 ~ 10
                            "米花先生，真步在此提醒您，請快點穿上女裝，客人們可是翹首以待了喔~", # 11 ~ 15
                            "米花大人，若您再不快些換衣服，可是要受到小小的懲罰哦！", # 16 ~ 20
                            "米花大人，賓客們為了欣賞您的女裝美態已經等待太久，真的不能再拖延了喔！", # 21 ~ 25
                            "<@432188735531122700>，您真的不考慮女裝嗎？明明所有人都那麼期待的說......難道......米花大人是沒辦法兌現承諾的壞人嗎......"] # 26 ~ up
        
    async def event(self,message:discord.Message):
        ctx = message.content
        if '<:mod_crossdressing:1085171453739139122>' in message.content:
            await self.mod_crossdressing_check(message=message)
        elif '早安' == ctx or '午安' == ctx or '晚安' == ctx and message.reference == None:
            await message.reply(self.greeting())
        else:
            return False
    
    async def mod_crossdressing_check(self,message:discord.Message):
        today = datetime.now().astimezone(self.tz).day
        if self.day != today:
            self.times = 1
            self.day = today
            self.mod_crossdressing_emoji_used_member_list = [message.author.id]
        elif message.author.id not in self.mod_crossdressing_emoji_used_member_list:
            self.times = self.times + 1
            self.mod_crossdressing_emoji_used_member_list.append(message.author.id)
        else:
            return
        list_pos = self.times // 5 if self.times < 26 else 6
        embed = SakuraEmbedMsg(title=f"每日提醒米花女裝")
        if random.randint(0,100) > 15: 
            embed.add_field(name=f"今天已有{self.times}人簽到",value=self.notifi_list[list_pos])
        else:
            embed.add_field(name=f"今天已有{self.times}人簽到",value="米花先生，你的祭神進度已經嚴重落後了，請好好注意一下自己的行為。哼~")
        await message.channel.send(embed=embed)
        print("cur time:",datetime.now(),"\ntoday=",today,"\n",self.mod_crossdressing_emoji_used_member_list)
        return
    
    def greeting(self):
        dt1 = datetime.utcnow().replace(tzinfo=timezone.utc)
        dt2 = dt1.astimezone(timezone(timedelta(hours=8))) # 轉換台灣時區
        ticks = int(dt2.strftime("%H"))
        if ticks >= 5 and ticks <= 11:
            ctx=['早安~請問要來點甜蜜的早餐嗎？']
        elif ticks >= 12 and ticks <= 18:
            ctx=['午安~要和我共進下午茶嗎？']
        elif ticks >= 19 and ticks <= 23:
            ctx=['晚安~祝你有個美夢～']
        elif ticks >= 0 and ticks <= 3:
            ctx=['今晚不讓你睡喔~♥王子大人']
        elif ticks == 4 :
            ctx=['王子大人，啊……啊，不要這樣♥']
        return random.choice(ctx)