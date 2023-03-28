import sqlite3
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from datetime import datetime
import asyncio
import discord
import os

PATH = os.path.join(os.path.dirname(__file__))
global db
db = sqlite3.connect(f"./databases/word_count.db")


class opencv:
    def cv2ImgAddText(img, text, left, top,color):
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

class PIL:
    def drawProgressBar(d, x, y, w, h, progress, bg="black", fg="red"):
        # draw background
        d.ellipse((x+w, y, x+h+w, y+h), fill=bg)
        d.ellipse((x, y, x+h, y+h), fill=bg)
        d.rectangle((x+(h/2), y, x+w+(h/2), y+h), fill=bg)

        # draw progress bar
        w *= progress
        d.ellipse((x+w, y, x+h+w, y+h),fill=fg)
        d.ellipse((x, y, x+h, y+h),fill=fg)
        d.rectangle((x+(h/2), y, x+w+(h/2), y+h),fill=fg)

        return d

class count:
    def word_count(name,id,guild,message):
        msg_list = list(enumerate(message))
        tmp = ""
        num = len(message)
        for i in msg_list:
            if str(i[1]) == "<":
                tmp = i
            if str(i[1]) == ">":
                if tmp[1] == "<":
                    num = num - i[0] + int(tmp[0])
        try:
            for i in db.execute(f'''SELECT Msg_count from Count where ID = {id} and Guild = {guild}'''):
                tmp = i
            if len(tmp) < 0:
                raise ValueError("None")
            num = num + int(tmp[0])
            guild=int(guild)
            db.execute(f'''UPDATE Count set Msg_count = {num}, Name = "{name}" WHERE ID = {id} AND Guild = {guild}''')
            db.commit()
        except:
            print("NewUser")
            x=(str(name),int(id),int(guild),int(num))
            db.execute("INSERT INTO Count VALUES(?,?,?,?)",x)
            db.commit()
        return

    def old_rank_query(name,guild):
        db = sqlite3.connect(f"./databases/word_count.db")
        tmp=""
        for i in db.execute(f'''SELECT Name,Msg_count from Count where Guild = {guild} ORDER BY Msg_count DESC LIMIT 10;'''):
            tmp = tmp + str(i[0]) + "，字數為" + str(i[1]) + "\n"
        return tmp
    
    def rank_query(name, guild):
        img = cv2.imread(f'./media/rank.png', cv2.IMREAD_UNCHANGED)
        tmp=[]
        for i in db.execute(f'''SELECT Name,Msg_count from Count where Guild = {guild} ORDER BY Msg_count DESC LIMIT 10;'''):
            tmp.append(i)
        for i,x in zip(tmp,range(19,919,90)):
            img = opencv.cv2ImgAddText(img,str(i[0]),110,x,"black")
            img = opencv.cv2ImgAddText(img,str(i[1]),540,x,"black")
        cv2.imwrite(f'./rank_tmp/{guild}.png', img)
        return tmp
    
    def levels(msg):
        level=0
        xp=100
        while True:
            level+=1
            if msg < xp:
                return level,int(msg),int(xp)
            else:
                msg = msg - xp
                xp = xp * 1.1

    def rank_progress_bar(levels):
        msg = levels[1]
        xp = levels[2]
        progress = int(np.around(msg / xp,decimals=2) * 40)
        print(progress)
        bar = "("
        for i in range(progress):
            bar += "/"
        for i in range(40 - progress):
            bar += "-"
        bar += ")"
        print(bar)
        return str(bar)

    def user_rank_query(name:discord.User, guild, message:discord.Message, embed):
        rk_list = db.execute(f'''SELECT Id,Name,Msg_count from Count where Guild = {guild} ORDER BY Msg_count DESC''')
        cur=0
        if name == None:
            embed.set_author(name=message.author, icon_url=message.author.avatar.url)
            for i in rk_list:
                cur+=1
                if int(message.author.id) == int(i[0]):
                    tmp = i
                    embed.add_field(name=f"您總共說過的字數為:{i[2]}", value=f"排名為:{cur}", inline=True)
                    msg_count=int(i[2])
                    break
        else:
            embed.set_author(name=name,icon_url=name.avatar.url)
            id = int(name.id)
            for i in rk_list:
                cur+=1
                if id == int(i[0]):
                    tmp = i
                    embed.add_field(name=f"總共說過的字數為:{i[2]}", value=f"排名為:{cur}", inline=True)
                    msg_count=int(i[2])
                    break
        try:
            levels=count.levels(msg_count)
        except:
            embed.add_field(name="尋找失敗", value="該使用者為機器人或沒有說過任何一句話", inline=True)
            return embed
        embed.add_field(name=f"等級為", value=f"{levels[0]}", inline=False)
        embed.add_field(name=f"經驗值:({levels[1]}/{levels[2]})", value=count.rank_progress_bar(levels), inline=False)
        return embed
    
class dailyCheck():
    def __init__(self):
        self.dailyCheckDB = sqlite3.connect(f"./databases/daily.db")
        self.dailyCheckDB.row_factory = sqlite3.Row
        self.cursor = self.dailyCheckDB.cursor()
        self.notifi_list = ["群主 該換上女裝了，不要讓大家等太久喔~", # 1 ~ 5
                            "懇請群主趕快換上女裝，外面的賓客都已經迫不及待想見您的美麗風采了呢！", # 6 ~ 10
                            "米花先生，真步在此提醒您，請快點穿上女裝，客人們可是翹首以待了喔~", # 11 ~ 15
                            "米花大人，若您再不快些換衣服，可是要受到小小的懲罰哦！", # 16 ~ 20
                            "米花大人，賓客們為了欣賞您的女裝美態已經等待太久，真的不能再拖延了喔！", # 21 ~ 25
                            "<@432188735531122700>，您真的不考慮女裝嗎？明明所有人都那麼期待的說......難道......米花大人是沒辦法兌現承諾的壞人嗎......"] # 26 ~ up
        
    async def check(self,message:discord.Message):
        day = datetime.now().day
        user_id = str(message.author.id)
        user_output = self.cursor.execute("SELECT day FROM mod_crossdressing WHERE user_id = ?",(user_id,)).fetchall()
        if user_output and user_output[0]["day"] == day:return
        times_output = self.cursor.execute("SELECT * from times").fetchone()
        times = times_output["times"]
        last_call = times_output["last_check_day"]
        times = times + 1 if day == last_call else 1
        list_pos = times // 5 if times < 26 else 6
        embed = discord.Embed(title=f"每日提醒米花女裝", color=0xd98d91)
        embed.add_field(name=f"今天已有{times}人簽到",value=self.notifi_list[list_pos])
        await message.channel.send(embed=embed)
        if user_output:
            self.cursor.execute("UPDATE mod_crossdressing SET day = ? WHERE user_id = ?",(day,user_id))
        else:
            self.cursor.execute("INSERT INTO mod_crossdressing VALUES(?,?)",(user_id,day))
        self.cursor.execute("UPDATE times SET times = ? , last_check_day = ?",(times,day))
        self.dailyCheckDB.commit()
        return