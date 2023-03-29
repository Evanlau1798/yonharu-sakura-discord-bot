import random
from threading import Thread
from datetime import datetime,timezone,timedelta
import os
import discord

PATH = os.path.join(os.path.dirname(__file__))


def print_ctx(message: discord.Message):
    dt1 = datetime.utcnow().replace(tzinfo=timezone.utc)
    dt2 = dt1.astimezone(timezone(timedelta(hours=8))) # 轉換台灣時區
    ticks = dt2.strftime("%H:%M:%S")
    try:
        conv=str(message.author)+'於'+str(ticks)+'在'+str(message.guild.name)+'的'+str(message.channel)+'說:'+str(message.content)
    except:
        conv=str(message.author)+'於'+str(ticks)+'在'+str(message.channel)+'說:'+str(message.content)
    print(conv)