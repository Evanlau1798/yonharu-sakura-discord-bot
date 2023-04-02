import random
from datetime import datetime,timezone,timedelta
import discord
import sqlite3
import time
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import numpy as np

class WordCounter(object):
    def __init__(self):
        self.word_countDB = sqlite3.connect(f"./databases/word_count.db")
        self.word_countDB_cursor = self.word_countDB.cursor()

    async def analyzeText(self,message: discord.Message):
        self.print_ctx(message=message)
        if self.checkLastMsg(message=message):
            self.addXP(message=message)
        return

    def checkLastMsg(self,message: discord.Message) -> bool:
        id = message.author.id
        guild = message.guild.id
        output = self.word_countDB_cursor.execute(f"SELECT Last_Msg from Count where ID = {id} and Guild = {guild}").fetchone()
        if output == None:
            self.newUser(message=message)
        elif int(time.time()) - int(output[0]) < 60:
            return False
        return True

    def addXP(self,message: discord.Message):
        id = message.author.id
        guild = message.guild.id
        name = message.author.display_name + "#" + message.author.discriminator
        xp = self.word_countDB_cursor.execute(f"SELECT XP from Count where ID = {id} and Guild = {guild}").fetchone()[0]
        xp = xp + random.randint(15,35)
        self.word_countDB_cursor.execute(f'UPDATE Count SET XP = {xp}, Name = "{name}", Last_Msg = "{int(time.time())}" WHERE ID = {id} AND Guild = {guild}')
        self.word_countDB.commit()
    
    def getLevel(self,user:discord.User,guild:int) -> int:
        xp = self.word_countDB_cursor.execute(f"SELECT XP from Count where ID = {user.id} and Guild = {guild}").fetchone()[0]
        if xp == None:
            raise ValueError("該使用者為機器人或沒有說過任何一句話")
        level = 1
        rank_xp = 100
        while xp >= rank_xp:
            level += 1
            xp -= rank_xp
            rank_xp *= 1.1
        return level,int(xp),int(rank_xp)

    def newUser(self,message: discord.Message):
        print("New User")
        name = message.author.display_name + "#" + message.author.discriminator
        id = message.author.id
        guild = message.guild.id
        xp = random.randint(15,35)
        last_msg = int(time.time())
        x = (name,id,guild,xp,last_msg)
        self.word_countDB_cursor.execute("INSERT OR IGNORE INTO Count VALUES(?,?,?,?,?)",x)
        self.word_countDB.commit()
        return

    def drawProgressBar(self,min,max) -> str:
        progress = round(min / max, 2)
        filled = round(progress * 40)
        bar = "[" + "".join(["/" for _ in range(filled)]) + "".join(["-" for _ in range(40 - filled)]) + "]"
        return bar
    
    def drawGuildRankQuery(self,message: discord.Message):
        img = cv2.imread(f'./media/rank.png', cv2.IMREAD_UNCHANGED)
        rank_list = self.word_countDB_cursor.execute(f"SELECT Name,XP from Count where Guild = {message.guild.id} ORDER BY XP DESC LIMIT 10;").fetchall()
        if len(rank_list) != 0:
            for i,x in zip(rank_list,range(19,919,90)):
                img = self.cv2ImgAddText(img,str(i[0]),110,x,"black")
                img = self.cv2ImgAddText(img,str(i[1]),540,x,"black")
            cv2.imwrite(f'./rank_tmp/{message.guild.id}.png', img)
            print(rank_list)
            return True
        else:
            return False
    
    def cv2ImgAddText(self,img, text, left, top,color):
        if (isinstance(img, np.ndarray)):
            img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2BGRA))
        draw = ImageDraw.Draw(img)
        fontStyle = ImageFont.truetype(f"./font/Iansui094-Regular.ttf", 35, encoding="utf-8")
        if fontStyle.getsize(text)[0] > 390:
            for i in range(len(list(text))+1,0,-1):
                if fontStyle.getsize(text[:i])[0] < 400:
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