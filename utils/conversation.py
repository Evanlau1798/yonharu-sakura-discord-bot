import random
from threading import Thread
from datetime import datetime,timezone,timedelta
import discord
import sqlite3
import time
import math
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
        print("addXp",xp)
    
    def getLevel(self,user:discord.User,guild:int) -> int:
        xp = self.word_countDB_cursor.execute(f"SELECT XP from Count where ID = {user.id} and Guild = {guild}").fetchone()[0]
        if xp == None:
            raise ValueError
        level = (-27 + math.sqrt(729 + 24 * xp / 5)) / 6 # 目前的等級
        xp_current_level = 5 * level * level + 27 * level # 該等級需要的經驗值
        xp_next_level = 5 * (level + 1) * (level + 1) + 27 * (level + 1) # 下一等級需要的經驗值
        level = int(level)
        xp_current_level = int(xp_current_level)
        xp_next_level = int(xp_next_level)
        return level,xp_current_level,xp_next_level

    def newUser(self,message: discord.Message):
        print("New User")
        name = message.author.display_name + "#" + message.author.discriminator
        id = message.author.id
        guild = message.guild.id
        xp = random.randint(15,35)
        last_msg = int(time.time())
        x = (name,id,guild,xp,last_msg)
        self.word_countDB_cursor.execute("INSERT INTO Count VALUES(?,?,?,?,?)",x)
        self.word_countDB.commit()
        return

    def drawProgressBar(self,min,max) -> str:
        progress = int(np.around(min / max,decimals=2) * 40)
        print(progress)
        bar = "("
        for i in range(progress):
            bar += "/"
        for i in range(40 - progress):
            bar += "-"
        bar += ")"
        print(bar)
        return str(bar)

    def print_ctx(self,message: discord.Message):
        dt1 = datetime.utcnow().replace(tzinfo=timezone.utc)
        dt2 = dt1.astimezone(timezone(timedelta(hours=8))) # 轉換台灣時區
        ticks = dt2.strftime("%H:%M:%S")
        try:
            conv=str(message.author)+'於'+str(ticks)+'在'+str(message.guild.name)+'的'+str(message.channel)+'說:'+str(message.content)
        except:
            conv=str(message.author)+'於'+str(ticks)+'在'+str(message.channel)+'說:'+str(message.content)
        print(conv)