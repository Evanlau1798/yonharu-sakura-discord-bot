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
from cachetools import cached, TTLCache

cache = TTLCache(maxsize=100, ttl=3600)

class XPCounter(object):
    def __init__(self,bot=None):
        self.XPCounter_DB = sqlite3.connect(f"./databases/XPCount.db")
        self.XPCounter_DB_cursor = self.XPCounter_DB.cursor()
        self.bot = bot

    @cached(cache)
    def get_guild_config(self, guild_id: int):
        return self.XPCounter_DB_cursor.execute("SELECT * FROM RankRoleEnabledGuild WHERE Guild_id = ?", (guild_id,)).fetchone()

    async def analyzeText(self,message: discord.Message):
        self.print_ctx(message=message)
        if self.checkLastMsg(message=message):
            self.addXP(message=message)
            guild_config = self.get_guild_config(message.guild.id)
            if guild_config is not None:
                await self.check_role(message=message, guild_config=guild_config)
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
        name = message.author.display_name
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
        name = message.author.display_name
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
        name = user.display_name
        id = user.id
        guild = guild.id
        xp = 1
        x = (name,id,guild,xp)
        self.XPCounter_DB_cursor.execute("INSERT OR IGNORE INTO VoiceChannelXP VALUES(?,?,?,?)",x)
        self.XPCounter_DB.commit()
        return
    
    def addVoiceXP(self,user:discord.User,guild:discord.Guild):
        name = user.display_name
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
        Guild_inf = self.XPCounter_DB_cursor.execute("SELECT * FROM RankRoleEnabledGuild WHERE Guild_id = ?", (guild_id,)).fetchone()
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
    
    async def check_role(self,message:discord.Message, guild_config):
        start = time.time()
        level, cur_xp, rank_xp = self.getRank(user=message.author, guild=message.guild.id)
        guild_id, lv20, lv40, lv60, lv80, lv100 = guild_config
        role_ids = {20: lv20, 40: lv40, 60: lv60, 80: lv80, 100: lv100}
        guild_roles = {role.id: role for role in message.guild.roles}

        # Get only the roles that exist in the guild
        role_ids = {level: guild_roles[role_id] for level, role_id in role_ids.items() if role_id in guild_roles}

        # Check only necessary levels and remove roles below the user's level
        necessary_levels = sorted([threshold for threshold in [20, 40, 60, 80, 100] if level >= threshold])

        for i, level_threshold in enumerate(necessary_levels):
            if i > 0 and necessary_levels[i-1] < level_threshold:
                # Remove the role below the current level
                await message.author.remove_roles(role_ids[necessary_levels[i-1]], reason="機器人等級功能之等級調整")

            # Check if the user already has the role
            if role_ids[level_threshold] not in message.author.roles:
                # Assign the role corresponding to the current level
                await message.author.add_roles(role_ids[level_threshold], reason="機器人等級功能之等級調整")
        print(f"{message.author.display_name}的身分組檢查執行時間:",time.time()-start)

class HandsByeSpecialFeedback():
    def __init__(self):
        self.mod_crossdressing_emoji_used_member_list = []
        self.times = 0
        self.tz = pytz.timezone('Asia/Taipei')
        self.day = datetime.now().astimezone(self.tz).day
        self.notifi_list = ["米花先生，今日份的女裝穿上了嗎？還沒穿？你這樣不行吧？明明大家都這麼期待了。", # 1 ~ 5
                            "群主～看到了嗎？又有人要你穿女裝了喔，櫻我也很期待喔，所以是不是該穿了啊～", # 6 ~ 10
                            "今天的女裝提醒已發送，請米花先生盡早完成女裝任務，啊對了！個人推薦白色絲襪配連身裙喔！", # 11 ~ 15
                            "新的一天又到來，米花的女裝還是沒有出現，我們的群主大大呀，女裝呢？", # 16 ~ 20
                            "群主！！穿上吧！！！！女裝。", # 21 ~ 25
                            "<@432188735531122700>，您真的不考慮女裝嗎？明明所有人都那麼期待的說......難道......米花先生是沒辦法兌現承諾的壞人嗎......"] # 26 ~ up
        
    async def event(self,message:discord.Message):
        ctx = message.content
        if '<:mod_crossdressing:1085171453739139122>' in message.content:
            await self.mod_crossdressing_check(message=message)
        elif '早安' == ctx or '午安' == ctx or '晚安' == ctx and message.reference == None:
            dt1 = datetime.utcnow().replace(tzinfo=timezone.utc)
            dt2 = dt1.astimezone(timezone(timedelta(hours=8))) # 轉換台灣時區
            ticks = int(dt2.strftime("%H"))
            await message.reply(self.greeting(ticks=ticks))
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
    
    def greeting(self,ticks):
        if ticks >= 5 and ticks <= 11:
            ctx=['早上了嗎……？不要……！我不想起床！不要叫我起床！啊……但是……早安……',
                 '早上好……你是不是也有種想要再睡一下的想法啊……？沒事喔……我也這麼想的……',
                 '早安，櫻今天精神很好喔！大概啦……你呢？有睡飽嗎？沒精神可是不好的喔！']
        elif ticks >= 12 and ticks <= 18:
            ctx=['午安！午餐吃甚麼？要喝下午茶嗎？嘛……我的話……陪你也不是不行喔。',
                 '中午了呢，嗯……太陽很大的時候總是會很懶散呢～但是！陰天的話也會讓人很想睡覺呢……不……人們好像不分時間都很懶散呢……',
                 '櫻總是在想啊……如果在這樣悠閒的午後能夠安靜地躺在草地上，甚麼事都不做，就這樣呆呆地看著天空，這會是多麼愜意的感覺呢？']
        elif ticks >= 19 and ticks <= 23:
            ctx=['晚安～希望今天能有個好夢，如果睡不著的話，我也是可以說說床邊故事的喔～從前從前，有一個………………喂！讓我說完！',
                 '晚上好，身為夜貓子的你，或者是健康乖寶寶的你，要睡了嗎？不睡的話要幹嘛呢？要一起玩嗎？',
                 '對於櫻來說啊……晚上的時候是很重要的喔，寂靜的深夜之中，只有自己與外頭點點的燈光，平靜，而且美妙。']
        elif ticks >= 0 and ticks <= 4:
            ctx=['喂喂喂……你還沒睡嗎？再怎麼說也太晚了喔，不睡覺明天怎麼會有精神呢！快去睡覺了！']
        '''紀念美好舊時光的程式碼
        elif ticks == 4 :
            ctx=['王子大人，啊……啊，不要這樣♥']'''
        return random.choice(ctx)
    
    def special_greeting(self,ticks:int): #待新增回應
        if ticks >= 5 and ticks <= 11:
            ctx=['早上好！怎麼樣？今天有精神嗎？我今天很有精神喔！要說為什麼的話……因為今天是和你在一起啊！']
        elif ticks >= 12 and ticks <= 18:
            ctx=['']
        elif ticks >= 19 and ticks <= 23:
            ctx=['']
        elif ticks >= 0 and ticks <= 4:
            ctx=['']
        return random.choice(ctx)