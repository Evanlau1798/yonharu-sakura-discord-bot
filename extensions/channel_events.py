import discord,asyncio,os,sqlite3,random,time,requests,pickle,io, filetype
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
from extensions.search import GoogleSearch

load_dotenv()
#GEMINI_MODEL = "gemini-1.0-pro-latest"
GEMINI_MODEL = "gemini-1.5-flash-latest"
#GEMINI_VISION_MODEL = "gemini-1.0-pro-vision-latest"
GEMINI_VISION_MODEL = "gemini-1.5-flash-latest"
#OpenAiAPIKey = os.getenv("OPENAPIKEY")
safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_NONE",
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_NONE",
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_NONE",
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_NONE",
  },
]


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
        self.dmAichat = AiChat(bot=self.bot)
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
        try:
            if message.guild.id == 887172437903560784: #斷手群discord伺服器特殊回應
                await self.handsByeSpFB.event(message=message)
        except:
            pass
        if "<@909796683418832956>" in message.content:
            print(message.reference)
            await self.tag_commands.select_commands(message=message)
        if self.quetion != None and message.reference != None:
            if message.reference.message_id in self.quetion.msg_id:
                await self.game_process(message)
        #print(message.reference.resolved.content)
        if message.reference is not None and message.reference.resolved is not None and 909796683418832956 == message.reference.resolved.author.id:
            try:
                await AiChat.singleChat(content=message.content, message=message, bot=self.bot)
            except Exception as e:
                await message.reply(embed=SakuraEmbedMsg(title="訊息無法傳送",description=str(e.args[0])))
        if isinstance(message.channel, discord.DMChannel):
            try:
                await message.channel.trigger_typing()
                reply = await self.dmAichat.chat(message=message)
                await message.channel.send(content = reply)
            except Exception as e:
                await message.reply(embed=SakuraEmbedMsg(title="訊息無法傳送",description=str(e.args[0])))
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
        self.model = genai.GenerativeModel(GEMINI_MODEL)
        self.vModel = genai.GenerativeModel(GEMINI_VISION_MODEL)
        self.userHistory = self.load_user_history()

    def getUserHistory(self, user:discord.User):
        self.userHistory = self.load_user_history()
        id = user.id
        history = self.userHistory[user.id] if self.userHistory.get(id) else AiChat.getStartupPrompt()
        chat = self.model.start_chat(history=history)
        return chat
    
    def load_user_history(self) -> dict:
        try:
            with open('./AIHistory/user_history.pickle', 'rb') as f:
                return pickle.load(f)
        except (FileNotFoundError, EOFError):
            return {}

    def save_user_history(self):
        with open('./AIHistory/user_history.pickle', 'wb') as f:
            pickle.dump(self.userHistory, f)
    
    async def chat(self, message: discord.Message, tmp_msg: discord.Interaction = None):
        chat:genai.ChatSession = self.getUserHistory(user=message.author)
        chat_len = len(chat.history) / 2
        if chat_len > 101:
            raise Exception("您目前已達到對話上限(100次)，請使用/forgotjuice指令來餵四春櫻遺忘汁(重置對話)\n也可以在刪除對話以前使用/chat_history將對話導出保存。")
        if tmp_msg:
            await tmp_msg.edit_original_response(embed = SakuraEmbedMsg("四春櫻正在輸入回應...", loading=True))
        nowTime = datetime.now().strftime("目前的時間(24小時制): %Y/%m/%d %H:%M:%S \n")
        content = nowTime + os.getenv('PersonaStartPrompt') + "與您對話的人是" + message.author.name + "\n\n" + message.content
        content = AiChat.get_message_attachment(message=message, content=[content])
        response = await chat.send_message_async(content, safety_settings=safety_settings)
        self.userHistory.update({message.author.id: chat.history})
        self.save_user_history()
        #return self.to_markdown(response.text)
        if chat_len > 80:
            reply_text = response.text + "\n\n" + "提醒:您目前已對話了(" + chat_len + "/100)回，請確保您在達到對話上限前結束對話。"
            return reply_text
        else:
            return response.text
    
    @commands.slash_command(name="chat", description="與我聊天吧!(基於Google Gemini)")
    @option("text", type=type.string, description="想跟我聊甚麼?", required=True)
    async def commandChat(self,message: discord.ApplicationContext,text:str):
        tmp = await message.respond(embed = SakuraEmbedMsg("正在等待四春櫻回應...", loading=True))
        try:
            reply = await self.chat(user=message.author,content=text,tmp_msg=tmp)
            await tmp.edit_original_response(embed=SakuraEmbedMsg(title="四春櫻的回應", description=reply))
        except Exception as e:
            await tmp.edit_original_response(embed=SakuraEmbedMsg(title="訊息無法傳送",description=str(e.args[0])))

    @commands.slash_command(name="forgotjuice", description="讓我喝下遺忘汁(重置AI對話)")
    async def forgotjuice(self, message:discord.ApplicationContext):
        userID = message.author.id
        try:
            chat = self.model.start_chat(history=AiChat.getStartupPrompt())
            self.userHistory.update({userID: chat.history})
            self.save_user_history()
            await message.respond(content=f"{message.author.mention} 已成功讓四春櫻喝下遺忘汁")
        except Exception as e:
            await message.respond(embed=SakuraEmbedMsg(title="訊息無法傳送",description=str(e.args[0])))

    @commands.slash_command(name="chat_history", description="將目前的AI對話紀錄私訊給您")
    async def chat_history(self, ctx: discord.ApplicationContext):
        user_id = ctx.author.id
        # 從 userHistory 中找到指定使用者的對話紀錄
        user_history = self.userHistory.get(user_id)
        if not user_history:
            await ctx.respond(embed=SakuraEmbedMsg("錯誤", "該使用者的對話紀錄不存在"))
            return

        # 將對話紀錄整理成一個字符串
        chat_history_str = ""
        for entry in user_history[8:]:
            role = entry.role
            for part in entry.parts:
                chat_history_str += f"{role}: {part.text}\n"

        #  使用 io.BytesIO 暫存 txt 檔案的內容
        chat_history_bytes = chat_history_str.encode('utf-8')
        chat_history_io = io.BytesIO(chat_history_bytes)

        # 將 txt 檔案私訊給使用者
        await ctx.author.send(file=discord.File(chat_history_io, f"{user_id}_chat_history.txt"))

        await ctx.respond(embed=SakuraEmbedMsg("成功", "對話紀錄已私訊給您"))

    @staticmethod
    async def singleChat(content, message:discord.Message = None, bot:discord.Client = None):
        await message.channel.trigger_typing()
        content = AiChat.get_message_attachment(message=message, content=[content])
        user = message.guild.get_member(message.author.id)
        name = message.author.name if user is None else user.display_name
        nowTime = datetime.now().strftime("目前的時間: %Y/%m/%d %H:%M:%S \n")
        model = genai.GenerativeModel(GEMINI_MODEL)
        chat = model.start_chat(history=AiChat.getStartupPrompt())
        reference_msg = bot.get_message(message.reference.message_id) if message.reference is not None else None
        if reference_msg:
            chat = AiChat.get_chat_history(message=reference_msg, chat=chat, bot=bot)
            content_prefix = nowTime + os.getenv('PersonaStartPrompt') + "目前與您對話的人是" + name + "，請接續上一段對話\n\n"
        else:
            content_prefix = nowTime + os.getenv('PersonaStartPrompt') + "與您對話的人是" + name + "\n\n"
        content[0] = content_prefix + content[0]

        response = await chat.send_message_async(content=content, safety_settings=safety_settings)
        await message.reply(response.text)

    @staticmethod
    def get_chat_history(message:discord.Message, chat:genai.ChatSession, bot:discord.Client = None) -> genai.ChatSession:
        if message is not None and message.reference is not None and message.reference.resolved is not None:
            if message.reference.resolved.reference is not None:
                ref_message = bot.get_message(message.reference.resolved.reference.message_id)
                chat = AiChat.get_chat_history(message=ref_message, chat=chat, bot=bot)
            if message.reference.resolved.content is not None:
                chat.history.extend([
                    glm.Content(parts=[glm.Part(text=message.reference.resolved.content)], role="user"),
                    glm.Content(parts=[glm.Part(text=message.content)], role="model")
                ])
        else:
            user_chat_history = AiChat.get_user_chat_history(message=message, bot=bot)
            chat.history.extend([
                glm.Content(parts=[glm.Part(text=f"以下是一段目前的使用者與其他使用者對話的紀錄: {user_chat_history}")], role="user"),
                glm.Content(parts=[glm.Part(text="我知道了。")], role="model")
            ])
        return chat
    
    @staticmethod
    def get_user_chat_history(message: discord.Message, bot: discord.Client, user_chat_history: str = "") -> str:
        user_chat_history = f"使用者{message.author.display_name}說了: {message.content}\n" + user_chat_history
        if message.reference is not None and message.reference.resolved is not None and not message.reference.resolved.author.bot:
            ref_message = bot.get_message(message.reference.resolved.reference.message_id)
            user_chat_history = AiChat.get_user_chat_history(message=ref_message, bot=bot, user_chat_history=user_chat_history)
        return user_chat_history
    
    @staticmethod
    def get_message_attachment(message: discord.Message, content: list) -> list:
        if message.attachments:
            for file in message.attachments:
                response = requests.get(file.url)
                file_type = filetype.guess(response.content).mime
                if file_type is None:
                    raise Exception("不支援該檔案類型")
                content.append({
                    'mime_type': file_type,
                    'data': response.content
                })
        return content

    '''@staticmethod
    async def singleChat(content, pic = None, message:discord.Message = None):
        search = GoogleSearch()
        if pic:
            first_pic_url = pic[0]
            response = requests.get(first_pic_url.url)
            img = Image.open(BytesIO(response.content))
            model = genai.GenerativeModel('gemini-pro-vision')
            response = model.generate_content(contents=[content,img])
        else:
            content = "請以\"四春櫻\"的身份並以繁體中文進行回答。\n\n請注意，如果詢問的問題有必要搜尋網路，請說出「請幫我搜尋:{您想要的搜尋文字}」，對話會回傳從Google的搜尋結果。如果要開啟搜尋到的網頁，請說出「請幫我打開:{您想要打開的網頁url}」以獲得網頁的html程式碼。如果詢問的是特定的資訊(如:時間)，請打開html網頁以確定，而不是單純查看網頁預覽文字。\n\n" + content
            model = genai.GenerativeModel('gemini-pro')
            chat = model.start_chat(history=AiChat.getStartupPrompt())
            res asponse = chat.send_message(content=content)
        if "請幫我搜尋:" in response.text or "請幫我搜尋：" in response.text:
            search_text = response.text.split("請幫我搜尋:")[1] if "請幫我搜尋:" in response.text else response.text.split("請幫我搜尋：")[1]
            msg_tmp = await message.reply(content=f'<a:loading:1050076012853080214> 四春櫻正在上網尋找"{search_text}"......')
            try:
                content = str(search.search(search_text))
                response = chat.send_message(content=content)
                if "請幫我打開" in response.text:
                    search_text = response.text.split("請幫我打開:")[1] if "請幫我打開:" in response.text else response.text.split("請幫我打開：")[1]
                    await msg_tmp.edit(content=f'<a:loading:1050076012853080214> 四春櫻正在瀏覽 "{search_text}"......')
                    content = str(search.get_html(search_text))
                    response = chat.send_message(content=content)
                    await msg_tmp.edit(content=AiChat.to_markdown(response.text).data)
            except Exception as e:
                await msg_tmp.edit(embed=SakuraEmbedMsg(title="訊息無法傳送",description=str(e.args[0])))
        else:
            await message.reply(AiChat.to_markdown(response.text).data)'''
    
    @staticmethod
    def getStartupPrompt():
        startupPrompt = [glm.Content(parts = [glm.Part(text=os.environ["PersonaInfo1"])])]
        startupPrompt[0].role = "user"
        startupPrompt.append(glm.Content(parts = [glm.Part(text="我知道了。")]))
        startupPrompt[1].role = "model"
        startupPrompt.append(glm.Content(parts = [glm.Part(text=os.environ["PersonaInfo2"])]))
        startupPrompt[2].role = "user"
        startupPrompt.append(glm.Content(parts = [glm.Part(text='我知道了。')]))
        startupPrompt[3].role = "model"
        startupPrompt.append(glm.Content(parts = [glm.Part(text=os.environ["PersonaInfo3"])]))
        startupPrompt[4].role = "user"
        startupPrompt.append(glm.Content(parts = [glm.Part(text='我知道了。')]))
        startupPrompt[5].role = "model"
        startupPrompt.append(glm.Content(parts = [glm.Part(text=os.environ["PersonaInfo4"])]))
        startupPrompt[6].role = "user"
        startupPrompt.append(glm.Content(parts = [glm.Part(text='我知道了，我會完全融入"四春櫻"的人設中，並且會遵守時間相關要求。')]))
        startupPrompt[7].role = "model"
        return startupPrompt
    
    @staticmethod
    def to_markdown(text:str):
        text = text.replace('•', '  *')
        return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

def setup(bot:discord.Bot):
    bot.add_cog(EventsListener(bot))
    bot.add_cog(AiChat(bot))