import discord,asyncio,os,sqlite3,random,time,requests
from discord.ext import commands
from discord import default_permissions,option,OptionChoice
from discord import SlashCommandOptionType as type
from datetime import datetime
from utils.EmbedMessage import SakuraEmbedMsg
from utils.conversation import XPCounter,HandsByeSpecialFeedback
from utils.personal_commands import PsCommands,TagCommands
from discord.ui import InputText,Select,view
from utils.game import game
from dotenv import load_dotenv
import textwrap
from PIL import Image
from io import BytesIO
import google.generativeai as genai
import google.ai.generativelanguage as glm
from IPython.display import Markdown

load_dotenv()

OpenAiAPIKey = os.getenv("OPENAPIKEY")

class EventsListener(commands.Cog):
    def __init__(self, bot:discord.Bot):
        self.bot = bot
        self.conv = XPCounter()
        self.handsByeSpFB = HandsByeSpecialFeedback()
        self.ps_commands = PsCommands(bot=self.bot)
        self.tag_commands = TagCommands(bot=self.bot)
        self.channels_DB = sqlite3.connect(f"./databases/channels.db")
        self.channels_DB_cursor = self.channels_DB.cursor()
        self.quetion = None
        loop = asyncio.get_event_loop()
        loop.create_task(self.user_vioce_channel_XP_task())

    @commands.slash_command(description="查看個人伺服器總字數排名")
    @option("user", type=type.user, description="標記以查詢指定帳號", required=False)
    @option("category", type=type.string, description="選擇欲查看的經驗類別", required=False,choices=['文字等級','語音等級'])
    async def rank(self,message: discord.ApplicationContext,user:discord.User=None,category="文字等級"):
        await message.defer()
        if user == None:
            user = message.author
        embed = SakuraEmbedMsg()
        embed.set_author(name=user.display_name + "#" + user.discriminator,icon_url=user.display_avatar.url)
        try:
            if category == "文字等級":
                (level,xp_current_level,xp_next_level) = self.conv.getRank(user,message.guild.id)
            else:
                (level,xp_current_level,xp_next_level) = self.conv.getVoiceRank(user,message.guild.id)
            embed.add_field(name=f"{category}為",value=str(level),inline=False)
            embed.add_field(name=f"經驗值:({xp_current_level}/{xp_next_level})",value=self.conv.drawProgressBar(xp_current_level,xp_next_level),inline=False)
        except:
            embed.add_field(name="尋找失敗",value="該使用者為機器人或沒有說過任何一句話")
        await message.respond(embed=embed)

    @commands.slash_command(description="查看本伺服器總字數排名")
    @option("category", type=type.string, description="選擇欲查看的經驗類別", required=False,choices=['文字等級','語音等級'])
    async def leaderboard(self,message: discord.ApplicationContext,category="文字等級"):
        await message.defer()
        if category == "文字等級":
            type = "TextChannelXP"
        else:
            type = "VoiceChannelXP"
        if self.conv.drawGuildRankQuery(message=message,type=type):
            embed = SakuraEmbedMsg(title=f"{str(message.guild.name)}的伺服器{category}排名")
            file = discord.File(f"./rank_tmp/{str(message.guild.id)}.png", filename="rank.png")
            embed.set_image(url=f"attachment://rank.png")
            await message.respond(embed=embed, file=file)
            file.close()
            os.remove(f"./rank_tmp/{str(message.guild.id)}.png")
        else:
            embed = SakuraEmbedMsg()
            embed.add_field(name="錯誤",value="這裡居然沒有人講過話...")
            await message.respond(embed=embed)
        return
    
    @commands.slash_command(description="創建語音頻道")
    async def create(self,message: discord.ApplicationContext):
        if self.channels_DB_cursor.execute(f"SELECT * FROM TextChannel WHERE ChannelID = {message.channel.id}").fetchone():
            await message.response.send_modal(modal=CreateChannelModal())
        else:
            await message.respond(embed=SakuraEmbedMsg("錯誤","此頻道無法使用此功能"), ephemeral=True)
        return
        
    @commands.slash_command(description="設定目前的頻道為動態語音創建用文字頻道")
    @default_permissions(administrator=True)
    async def vcset(self,message: discord.ApplicationContext):
        if not self.channels_DB_cursor.execute(f"SELECT * FROM TextChannel WHERE ChannelID = {message.channel.id}").fetchone():
            channel_id = message.channel.id
            create_by = message.author.id
            guild_id = message.guild.id
            x = (channel_id,create_by,guild_id)
            self.channels_DB_cursor.execute("INSERT OR IGNORE INTO TextChannel VALUES(?,?,?)",x)
            self.channels_DB.commit()
            await message.respond(embed=SakuraEmbedMsg("成功",f"已登記<#{channel_id}>為動態語音創建用文字頻道"), ephemeral=True)
        else:
            await message.respond(embed=SakuraEmbedMsg("錯誤","此頻道已登記"), ephemeral=True)
        return
    
    @commands.slash_command(description="設定使用者目前的語音頻道為動態語音創建用語音頻道")
    @default_permissions(administrator=True)
    async def dvcset(self,message: discord.ApplicationContext):
        if not self.channels_DB_cursor.execute(f"SELECT * FROM DynamicVoiceChannel WHERE ChannelID = {message.channel.id}").fetchone():
            channel_id = message.author.voice.channel.id
            create_by = message.author.id
            guild_id = message.guild.id
            x = (channel_id,create_by,guild_id)
            self.channels_DB_cursor.execute("INSERT OR IGNORE INTO DynamicVoiceChannel VALUES(?,?,?)",x)
            self.channels_DB.commit()
            await message.respond(embed=SakuraEmbedMsg("成功",f"已登記<#{channel_id}>為動態語音創建用語音頻道"), ephemeral=True)
        else:
            await message.respond(embed=SakuraEmbedMsg("錯誤","此頻道已登記"), ephemeral=True)
        return
    
    @commands.slash_command(description="取消設定動態語音頻道")
    @option("channel", type=type.channel, description="選擇欲取消的頻道", required=True)
    @default_permissions(administrator=True)
    async def vcdel(self,message: discord.ApplicationContext,channel):
        if channel.type == discord.ChannelType.voice and self.channels_DB_cursor.execute(f"SELECT * FROM DynamicVoiceChannel WHERE ChannelID = {message.channel.id}").fetchone():
            self.channels_DB_cursor.execute("DELETE FROM DynamicVoiceChannel WHERE ChannelID = ?",(channel.id,))
            self.channels_DB.commit()
            await message.respond(embed=SakuraEmbedMsg("成功",f"已取消登記該頻道\n頻道為:{channel.mention}"), ephemeral=True)
        elif channel.type == discord.ChannelType.text and self.channels_DB_cursor.execute(f"SELECT * FROM TextChannel WHERE ChannelID = {message.channel.id}").fetchone():
            self.channels_DB_cursor.execute("DELETE FROM TextChannel WHERE ChannelID = ?",(channel.id,))
            self.channels_DB.commit()
            await message.respond(embed=SakuraEmbedMsg("成功",f"已取消登記該頻道\n頻道為:{channel.mention}"), ephemeral=True)
        else:
            await message.respond(embed=SakuraEmbedMsg("錯誤","此頻道不存在於資料庫內"), ephemeral=True)
        return
    
    @commands.slash_command(description="遊玩小遊戲!")
    @option("difficulty", type=type.integer, description="自訂難度(預設為100)", required=False)
    async def game(self,message: discord.ApplicationContext,difficulty=100):
        await message.response.defer()
        if difficulty >= 1:
            quetion_message = await message.respond(f"猜猜看究竟是0~{difficulty}中哪一個數吧!\n(回覆此訊息以猜測，限時45秒)")
            self.quetion = game(quetion_message.id,difficulty)
        else:
            await message.respond(f"無效的難度，難度需大於1({difficulty})")

    @commands.Cog.listener()
    async def on_message(self, message:discord.Message):
        if message.author.bot == True:  # 排除自己的訊息
            return
        if message.author.id == 540134212217602050:
            if message.content.startswith('!'):  # 個人指令判斷
                await self.ps_commands.select_commands(message=message)
        if message.guild.id == 887172437903560784: #斷手群discord伺服器特殊回應
            await self.handsByeSpFB.event(message=message)
        if "<@909796683418832956>" in message.content:
            await self.tag_commands.select_commands(message=message)
        if self.quetion != None and message.reference != None:
            if message.reference.message_id in self.quetion.msg_id:
                await self.game_process(message)
        if isinstance(message.channel, discord.DMChannel):
            return
        await self.conv.analyzeText(message=message)

    async def user_vioce_channel_XP_task(self):
        while True:
            await asyncio.sleep(60 - datetime.now().second)
            self.conv.XPCounter_DB_cursor.execute("BEGIN TRANSACTION")
            for guild in self.bot.guilds:
                for channel in guild.voice_channels:
                    for user in channel.members:
                        if user.bot == False:
                            self.conv.addVoiceXP(user=user,guild=guild)
            if self.conv.XPCounter_DB.in_transaction:
                self.conv.XPCounter_DB.commit()

    async def game_process(self,message: discord.Message):
        try:
            user = str(message.author).split("#")[0]
            embed = SakuraEmbedMsg(description=self.quetion.Guess(int(message.content)))
            embed.set_author(name=f"{user}猜了{str(message.content)}",icon_url=message.author.display_avatar.url)
            if int(message.content) != self.quetion.number:
                embed.set_footer(text="回覆我以繼續猜數字")
                new_msg = await message.channel.send(embed=embed)
                await message.delete()
                self.quetion.msg_id.append(new_msg.id)
            else:
                embed.set_footer(text="遊戲結束!")
                await message.channel.send(embed=embed)
                await message.delete()
                self.quetion = None
        except Exception as e:
            embed = SakuraEmbedMsg(description=f"答案包含除數字以外的字元\n剩餘{int(45 - self.quetion.time/10)}秒")
            embed.set_author(name=f"{user}猜了{str(message.content)}",icon_url=message.author.display_avatar.url)
            embed.set_footer(text="回覆我以繼續猜數字")
            new_msg = await message.channel.send(embed=embed)
            await message.delete()
            self.quetion.msg_id.append(new_msg.id)
            await message.reply(embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self,member:discord.Member, before:discord.VoiceState, after:discord.VoiceState):
        start = time.time()
        if before.channel != None and after.channel != None and before.channel.id == after.channel.id: #使用者更改自身狀態，不需偵測
            return
        if before.channel != None: #偵測是否有使用者離開自訂義頻道
            if self.channels_DB_cursor.execute(f"SELECT * from CreatedChannel WHERE ChannelID = ? and GuildID = ?",(before.channel.id,before.channel.guild.id)).fetchone() and len(before.channel.members) == 0:
                await before.channel.delete(reason=None)
                self.channels_DB_cursor.execute(f"DELETE FROM CreatedChannel WHERE ChannelID = ? and GuildID = ?",(before.channel.id,before.channel.guild.id))
                self.channels_DB.commit()
            if after.channel != None and self.channels_DB_cursor.execute(f"SELECT * from DynamicVoiceChannel WHERE ChannelID = ? and GuildID = ?",(after.channel.id,after.channel.guild.id)).fetchone():
                await self.createDynamicVoiceChannel(member=member,after=after)
        elif self.channels_DB_cursor.execute(f"SELECT * from DynamicVoiceChannel WHERE ChannelID = ? and GuildID = ?",(after.channel.id,after.channel.guild.id)).fetchone(): 
            await self.createDynamicVoiceChannel(member=member,after=after)
        end = time.time()
        try:print("舊頻道:",before.channel.name if before.channel else None,"新頻道:",after.channel.name if after.channel else None)
        except:pass
        print("頻道更替檢測執行時間:",end - start,"\n")
        return
    
    async def createDynamicVoiceChannel(self,member:discord.Member,after:discord.VoiceState):
        channelName = ['白喵一番屋桃喵店', '白喵一番屋竹喵店', '白喵一番屋中喵店', 'X50 Music Game Station',
                       'chunithm玩家專業模仿中心','maimai玩家專業模仿中心','廣三SOGO紅帽象','sdvx玩家專業模仿中心',
                       '普羅洗腳玩家專業模仿中心','在此敲碗群主女裝',
                       f'{member.name}的秀肌肉專區',f'{member.name}的自閉小黑屋',f'{member.name}的語音頻道',f'{member.name}大佬在此🛐',f'{member.name}的線上賭場開張囉']
        new_ch:discord.VoiceChannel = await after.channel.guild.create_voice_channel(name=random.choice(channelName),category=after.channel.category,reason=None)
        await member.move_to(channel=new_ch)
        channel_id = new_ch.id
        create_by = member.id
        guild_id = after.channel.guild.id
        self.channels_DB_cursor.execute("INSERT OR IGNORE INTO CreatedChannel VALUES(?,?,?)",(channel_id,create_by,guild_id))
        self.channels_DB.commit()

class CreateChannelModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="創建自定義頻道名稱",timeout=180)
        self.add_item(InputText(label="頻道名稱",placeholder="請輸入頻道名稱",custom_id="ch_name"))
        self.add_item(InputText(label="頻道限制人數",placeholder="請輸入頻道最多允許的人數(最大99,預設為不限)",custom_id="people",required=False))
        
    async def callback(self, interaction: discord.Interaction):
        channel_name = str(self.children[0].value)
        try:
            people = int(self.children[1].value) if self.children[1].value != "" else 0
            if people < 0 or people > 99:
                raise Exception("錯誤的人數")
        except:
            await interaction.response.send_message(
                embed=SakuraEmbedMsg(title="錯誤",
                                     description=f"錯誤的頻道人數數量\n合法範圍為0~99人\n您輸入的文字為:{self.children[1].value}"),ephemeral=True)
        new_ch:discord.VoiceChannel = await interaction.guild.create_voice_channel(name=channel_name,category=interaction.channel.category,reason=None,user_limit=people)
        await interaction.response.send_message(embed=SakuraEmbedMsg("成功",f"語音頻道<#{new_ch.id}>已成功創建"),ephemeral=True)
        channel_id = new_ch.id
        create_by = interaction.user.id
        guild_id = interaction.guild.id
        x = (channel_id,create_by,guild_id)
        with sqlite3.connect(f"./databases/channels.db") as db:
            db_cursor = db.cursor()
            db_cursor.execute("INSERT OR IGNORE INTO CreatedChannel VALUES(?,?,?)",x)
            db.commit()

#==================基於Google Gemini之AI對話======================
class AiChat(commands.Cog):
    def __init__(self, bot):
        self.bot:discord.Bot = bot
        genai.configure(api_key=os.environ["GEMINIAPIKEY"])
        self.model = genai.GenerativeModel('gemini-pro')
        self.vModel = genai.GenerativeModel('gemini-pro-vision')
        self.userHistory = {}
        self.userVisionHistory = {}

    def getUserHistory(self, user:discord.User,isVision):
        id = user.id
        if isVision:
            if self.userVisionHistory.get(id):
                return self.userVisionHistory[id]
            chat = self.vModel.start_chat(history=[])
            self.userVisionHistory.update({id: chat})
        else:
            if self.userHistory.get(id):
                return self.userHistory[id]
            chat = self.model.start_chat(history=AiChat.getStartupPrompt())
            self.userHistory.update({id: chat})
            return self.userHistory[id]    

    async def chat(self, user:discord.User = None, content:str = "", tmp_msg:discord.Interaction = None):
        chat:genai.ChatSession = self.getUserHistory(user=user, isVision=False)
        if tmp_msg:
            await tmp_msg.edit_original_response(embed = SakuraEmbedMsg("Gemini正在輸入回應...", loading=True))
        content = "請以\"四春櫻\"的身份並以繁體中文進行回答。\n\n" + content
        response = chat.send_message(content)
        self.userHistory.update({user.id: chat})
        return self.to_markdown(response.text)
    
    @commands.slash_command(name="chat", description="與我聊天吧!(基於Google Gemini)")
    @option("text", type=type.string, description="想跟我聊甚麼?", required=True)
    async def commandChat(self,message: discord.ApplicationContext,text:str):
        tmp = await message.respond(embed = SakuraEmbedMsg("正在等待Gemini回應...", loading=True))
        reply:Markdown = await self.chat(user=message.author,content=text,tmp_msg=tmp)
        await tmp.edit_original_response(embed=SakuraEmbedMsg(title="Gemini的回應", description=reply.data))
    
    @staticmethod
    async def singleChat(content, pic=None):
        if pic:
            first_pic_url = pic[0]
            response = requests.get(first_pic_url.url)
            img = Image.open(BytesIO(response.content))
            model = genai.GenerativeModel('gemini-pro-vision')
            response = model.generate_content(contents=[content,img])
        else:
            content = "請以\"四春櫻\"的身份並以繁體中文進行回答。\n\n" + content
            model = genai.GenerativeModel('gemini-pro')
            chat = model.start_chat(history=AiChat.getStartupPrompt())
            response = chat.send_message(content=content)
        return AiChat.to_markdown(response.text).data
    
    @staticmethod
    def getStartupPrompt():
        startupPrompt = [glm.Content(parts = [glm.Part(text=os.environ["PersonaInfo"])])]
        startupPrompt[0].role = "user"
        startupPrompt.append(glm.Content(parts = [glm.Part(text="我知道了")]))
        startupPrompt[1].role = "model"
        return startupPrompt
    
    @staticmethod
    def to_markdown(text):
        text = text.replace('•', '  *')
        return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

'''class AiChat(commands.Cog):
    def __init__(self, bot):
        self.bot:discord.Bot = bot
        self.persona_info = os.getenv("PersonaInfo")
        openai.api_key = OpenAiAPIKey

    async def extract_city_from_input(self, input_text):
        response = openai.Completion.create(
            model="text-davinci-002",
            prompt=f"從這段輸入中提取城市名稱: '{input_text}'\n",
            max_tokens=10
        )
        city_name = response.choices[0].text.strip().split('\n')[0]
        return city_name

    async def execute_command(self, ctx, command, **kwargs):
        if command == "儲存消息":
            await self.bot.get_command('pin_msg')(ctx, **kwargs)
        elif command == "查詢天氣":
            await self.bot.get_command('weather')(ctx, **kwargs)
        # ... 根據您的指令添加更多邏輯

    async def handle_command(self, ctx:discord.Message, message):
        response = openai.Completion.create(
            model="text-davinci-002",  # 使用 GPT-3
            prompt=f"判斷這個用戶的輸入是否涉及指令: '{message.content}'\n\n",
            max_tokens=50
        )

        command_response = response.choices[0].text.strip()
        if "翻譯" in command_response:
            await self.execute_command(ctx, "翻譯", text=message.content)
        elif "天氣" in command_response:
            city = self.extract_city_from_input(message.content)  # 提取城市名稱的邏輯
            await self.execute_command(ctx, "查詢天氣", weather=city)
        # ... 添加更多判斷和執行邏輯
        else:
        # 使用 GPT-4 進行基於人設的回應
        async with ctx.channel.typing():
            persona_response = openai.ChatCompletion.create(
                    model="gpt-4-1106-preview",
                    messages=[
                        {"role": "system", "content": self.persona_info},
                        {"role": "user", "content": f"請以四春櫻的人設回應以下對話\n\n{message.content}"}
                    ],
                    max_tokens=1000
                )
            await ctx.channel.send(persona_response.choices[0].message["content"])


    @commands.slash_command(name="chat", description="與我聊天吧!(基於GPT-4)")
    async def chat(self, ctx, *, message: str):
        await self.handle_command(ctx, message)

    @commands.Cog.listener()
    async def on_message(self, message:discord.Message):
        if message.author == self.bot.user or not isinstance(message.channel, discord.DMChannel):
            return
        ctx = self.bot.get_message(message.id)
        await self.handle_command(ctx, message)'''

def setup(bot:discord.Bot):
    bot.add_cog(EventsListener(bot))
    bot.add_cog(AiChat(bot))