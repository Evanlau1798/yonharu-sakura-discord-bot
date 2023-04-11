import random
from datetime import datetime,timezone,timedelta
import discord
import sqlite3
import time
import cv2
from PIL import Image, ImageDraw, ImageFont
import numpy as np

class XPCounter(object):
    def __init__(self):
        self.XPCounter_DB = sqlite3.connect(f"./databases/XPCount.db")
        self.XPCounter_DB_cursor = self.XPCounter_DB.cursor()

    async def analyzeText(self,message: discord.Message):
        self.print_ctx(message=message)
        if self.checkLastMsg(message=message):
            self.addXP(message=message)
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
            rank_xp *= 1.1
        return level,int(xp),int(rank_xp)
    
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