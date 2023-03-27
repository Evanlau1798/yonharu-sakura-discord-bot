import random
from threading import Thread
from datetime import datetime,timezone,timedelta
import os
PATH = os.path.join(os.path.dirname(__file__))

def tag(name,ctx): #標記
  conv=[
    '王子先生，王子先生\n要品茗嗎?\n茗就是茶阿!',
    '在古今中外的繪本裡阿，\n保護公主，\n就是王子先生的使命呦。',
    '早上，一睜開眼，\n首先要跟小鳥先生們，\n說聲早安呀~',
    '女孩子就是活在夢之國裡，\n做著夢的呀。\n命運的王子先生與夢之國~♪',
    f'{name}王子先生，有什麼事嗎？'
  ]
  if "讓我看看" in ctx:
    return "不要!"
  else:
    return random.choice(conv)

def new_tag():
  return

def conv_input(conv):
  print(conv)
  f = open(f'{PATH}/conv_log.txt','a')
  f.writelines(f"{str(conv)}\n")
  f.close()

def write_del_log(conv):
  write = Thread(target=conv_del_input(conv))
  write.start()

def conv_del_input(conv):
  print(conv)
  f = open(f'{PATH}/del_log.txt','a')
  f.writelines(f"{str(conv)}\n")
  f.close()

def write_log(conv):
  write = Thread(target=conv_input(conv))
  write.start()

def feedback(conv):
  dt1 = datetime.utcnow().replace(tzinfo=timezone.utc)
  dt2 = dt1.astimezone(timezone(timedelta(hours=8))) # 轉換台灣時區
  ticks = int(dt2.strftime("%H"))
  if ticks >= 5 and ticks <= 11:
    ctx=['早安~請問要來點甜蜜的早餐嗎？']
    return random.choice(ctx)
  if ticks >= 12 and ticks <= 18:
    ctx=['午安~要和我共進下午茶嗎？']
    return random.choice(ctx)
  if ticks >= 19 and ticks <= 23:
    ctx=['晚安~祝你有個美夢～']
    return random.choice(ctx)
  if ticks >= 0 and ticks <= 3:
    ctx=['今晚不讓你睡喔~♥王子大人']
    return random.choice(ctx)
  if ticks == 4 :
    ctx=['王子大人，啊……啊，不要這樣♥']
    return random.choice(ctx)

def gif(message):
  if '🎤' in str(message):
    return 'https://media.discordapp.net/attachments/903285693655162932/904025706286178334/1.gif'

  if 'mumei' in str(message):
    return 'https://i.imgur.com/xojG0xB.gif'

  if 'ina1' == str(message):
    return 'https://i.imgur.com/GfDvVdg.gif'

  if 'ina2' == str(message):
    return 'https://i.imgur.com/mNBAdoA.gif'

  if 'yagoo' in str(message):
    return 'https://i.imgur.com/DUM40wt.gif'
  return False

def print_ctx(message):
  dt1 = datetime.utcnow().replace(tzinfo=timezone.utc)
  dt2 = dt1.astimezone(timezone(timedelta(hours=8))) # 轉換台灣時區
  ticks = dt2.strftime("%H:%M:%S")
  try:
    conv=str(message.author)+'於'+str(ticks)+'在'+str(message.guild.name)+'的'+str(message.channel)+'說:'+str(message.content)
  except:
    conv=str(message.author)+'於'+str(ticks)+'在'+str(message.channel)+'說:'+str(message.content)
  write_log(conv)

def print_cmd(message,cmd):
  dt1 = datetime.utcnow().replace(tzinfo=timezone.utc)
  dt2 = dt1.astimezone(timezone(timedelta(hours=8))) # 轉換台灣時區
  ticks = dt2.strftime("%H:%M:%S")
  try:
    conv=str(message.author)+'於'+str(ticks)+'在'+str(message.guild.name)+'的'+str(message.channel)+'用:'+str(cmd)
  except:
    conv=str(message.author)+'於'+str(ticks)+'在'+str(message.channel)+'用:'+str(cmd)
  write_log(conv)

def del_output(message):
  dt1 = datetime.utcnow().replace(tzinfo=timezone.utc)
  dt2 = dt1.astimezone(timezone(timedelta(hours=8))) # 轉換台灣時區
  ticks = dt2.strftime("%H:%M:%S")
  try:
    conv=str(message.author)+'於'+str(ticks)+'在'+str(message.guild.name)+'的'+str(message.channel)+'刪除了:'+str(message.content)
  except:
    conv=str(message.author)+'於'+str(ticks)+'在'+str(message.channel)+'刪除了:'+str(message.content)
  write_del_log(conv)
  return

def save_guild_message(message):
  write = Thread(target=write_guild_message,args=[message])
  write.start()
  return

def write_guild_message(message):
  dt1 = datetime.utcnow().replace(tzinfo=timezone.utc)
  dt2 = dt1.astimezone(timezone(timedelta(hours=8))) # 轉換台灣時區
  ticks = dt2.strftime("%H:%M:%S")
  if str(message.channel.type) == "private":
    guild = "DM channel"
    channel = str(message.channel)
    author = str(message.author)
    ctx = str(message.content)
  else:
    if "/" in str(message.guild.name):
      guild = ""
      for i in str(message.guild.name):
        if i != "/":
          guild += i
    else:
      guild = str(message.guild.name)
    channel = str(message.channel)
    author = str(message.author)
    ctx = str(message.content)
  path = f"{PATH}/history_message/{guild}"
  if os.path.exists(path):
    path += f"/{channel}.txt"
  else:
    dir = os.path.join(f"{PATH}/history_message/", guild)
    os.mkdir(dir)
  fp = open(f"{PATH}/history_message/{guild}/{channel}.txt","a",encoding="UTF-8")
  fp.writelines(f"{author}於{ticks}說: {ctx}\n")
  fp.close()
  return

def get_cur_time():
  dt1 = datetime.utcnow().replace(tzinfo=timezone.utc)
  dt2 = dt1.astimezone(timezone(timedelta(hours=8))) # 轉換台灣時區
  ticks = str(dt2.strftime("%Y/%m/%d %H:%M"))
  return ticks

class HelpReply:
  def __init__(self):
    self.HelpReplyId = []