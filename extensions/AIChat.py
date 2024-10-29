import discord,asyncio,os,sqlite3,random,time,requests,pickle,io, filetype
from discord.ext import commands
from discord import default_permissions,option,OptionChoice
from discord import SlashCommandOptionType as type
from utils.EmbedMessage import SakuraEmbedMsg
from datetime import datetime
import textwrap
import google.generativeai as genai
import google.ai.generativelanguage as glm
from IPython.display import Markdown
from dotenv import load_dotenv

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

#==================基於Google Gemini之AI對話======================
class AiChat(commands.Cog):
    def __init__(self, bot):
        self.bot:discord.Bot = bot
        genai.configure(api_key=os.environ["GEMINIAPIKEY"])
        self.model = genai.GenerativeModel(GEMINI_MODEL)
        self.vModel = genai.GenerativeModel(GEMINI_VISION_MODEL)
        self.userHistory = self.load_user_history()
        self.user_ai_choices = AiChat.UserAIChoice()

    def getUserHistory(self, user:discord.User, persona):
        self.userHistory = self.load_user_history()
        id = user.id
        history = self.userHistory[user.id] if self.userHistory.get(id) else AiChat.getStartupPrompt() if persona is True else None
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
    
    class UserAIChoice:
        SAKURA = True
        ORIGINAL = False

        def __init__(self):
            self.choices:dict = self.load_user_AI_choice()
            self.last_modified_time = self.get_file_last_modified_time()

        def get(self, user:discord.User=None, user_id:int=None) -> bool:
            if user is None and user_id is None:
                raise Exception("必須至少指定一個Discord user或user id")
            user_id = user_id if user is None else user.id

            current_modified_time = self.get_file_last_modified_time()
            if current_modified_time != self.last_modified_time:
                self.choices = self.load_user_AI_choice()
                self.last_modified_time = current_modified_time

            return self.choices.get(user_id, None)
        
        def modify(self, choice:bool , user:discord.User=None, user_id:int=None):
            user_id = user_id if user is None else user.id
            self.choices[user_id] = choice
            with open('./databases/AI_user_choice.pickle', 'wb') as f:
                pickle.dump(self.choices, f)
        
        def load_user_AI_choice(self) -> dict:
            try:
                with open('./databases/AI_user_choice.pickle', 'rb') as f:
                    return pickle.load(f)
            except (FileNotFoundError, EOFError):
                return {}
            
        def get_file_last_modified_time(self) -> float:
            return os.path.getmtime('./databases/AI_user_choice.pickle')
            
        @staticmethod #無快取，可用於其他區域
        def static_get(user:discord.User) -> bool:
            try:
                with open('./databases/AI_user_choice.pickle', 'rb') as f:
                    choices = pickle.load(f)
            except (FileNotFoundError, EOFError):
                choices = {}
            return choices.get(user.id, None)
        
        @staticmethod #無快取，可用於其他區域
        def static_modify(user:discord.User, choice):
            user_id = user_id if user is None else user.id
            try:
                with open('./databases/AI_user_choice.pickle', 'rb') as f:
                    choices = pickle.load(f)
            except (FileNotFoundError, EOFError):
                choices = {}
            choices[user_id] = choice
            with open('./databases/AI_user_choice.pickle', 'wb') as f:
                pickle.dump(choices, f)
    
    async def chat(self, message: discord.Message, content:str = None, tmp_msg: discord.Interaction = None):
        persona = self.user_ai_choices.get(message.author)
        chat:genai.ChatSession = self.getUserHistory(user=message.author, persona=persona)
        chat_len = len(chat.history) / 2
        if chat_len > 101:
            raise Exception("您目前已達到對話上限(100次)，請使用/forgotjuice指令來餵四春櫻遺忘汁(重置對話)\n也可以在刪除對話以前使用/chat_history將對話導出保存。")
        if tmp_msg:
            await tmp_msg.edit_original_response(embed = SakuraEmbedMsg("四春櫻正在輸入回應...", loading=True))
        user_content = self.generate_user_content(message, additional_content=content)
        response = await chat.send_message_async(user_content, safety_settings=safety_settings)
        self.userHistory.update({message.author.id: chat.history})
        self.save_user_history()
        if chat_len > 80:
            reply_text = response.text + "\n\n" + "提醒:您目前已對話了(" + chat_len + "/100)回，請確保您在達到對話上限前結束對話。"
            return reply_text
        else:
            '''if not persona:
                return "```此對話由原版Google Gemini生成，請使用四春櫻人設模式以獲得使用機器人之最佳體驗```" + response.text'''
            return response.text
        
    def generate_user_content(self, message:discord.Message, additional_content:str = None) -> str:
        nowTime = datetime.now().strftime("目前的時間(24小時制): %Y/%m/%d %H:%M:%S \n")
        AI_choice = os.getenv('PersonaStartPrompt') if self.user_ai_choices.get(message.author) else "\n每段對話前會附上目前的實際時間和使用者的名字，您可以按照時間來了解目前實際上經過了多久和對話的人是誰，譬如目前的時間(早上、中午、晚上)，請不要在回答中寫出或重複與每段對話前的前置文相同的文字內容\n"
        content = nowTime + AI_choice + "與您對話的人是" + message.author.name + "\n\n"
        content += message.content if additional_content is None else additional_content
        content = AiChat.get_message_attachment(message=message, content=[content])
        return content
    
    @commands.slash_command(description="修改使用的AI之人設")
    @option("persona", type=type.string, description="選擇欲使用的人設", choices=['四春櫻 (預設)','標準Google Gemini'])
    async def persona(self, message: discord.ApplicationContext, persona):
        if persona == '標準Google Gemini':
            self.user_ai_choices.modify(user=message.author, choice = False)
        else:
            self.user_ai_choices.modify(user=message.author, choice = True)
        await message.respond(embed = SakuraEmbedMsg(title="修改成功", description=f"您使用的AI人設已修改成基於{persona}之回覆。"))

    
    @commands.slash_command(name="chat", description="與我聊天吧!(基於Google Gemini)")
    @option("text", type=type.string, description="想跟我聊甚麼?", required=True)
    async def commandChat(self,message: discord.ApplicationContext,text:str):
        tmp = await message.respond(embed = SakuraEmbedMsg("正在等待四春櫻回應...", loading=True))
        try:
            reply = await self.chat(message=message, content=text, tmp_msg=tmp)
            await tmp.edit_original_response(embed=SakuraEmbedMsg(title="四春櫻的回應", description=reply))
        except Exception as e:
            await tmp.edit_original_response(embed=SakuraEmbedMsg(title="訊息無法傳送",description=str(e.args[0])))

    @commands.slash_command(name="forgotjuice", description="讓我喝下遺忘汁(重置AI對話)")
    async def forgotjuice(self, message:discord.ApplicationContext):
        userID = message.author.id
        try:
            chat = self.model.start_chat(history=AiChat.getStartupPrompt() if self.user_ai_choices.get(user=message.author) is True else None)
            self.userHistory.update({userID: chat.history})
            self.save_user_history()
            await message.respond(content=f"{message.author.mention} 已成功讓四春櫻喝下遺忘汁")
        except Exception as e:
            await message.respond(embed=SakuraEmbedMsg(title="訊息無法傳送",description=str(e.args[0])))

    @commands.slash_command(name="chat_history", description="將目前的AI對話紀錄私訊給您")
    async def chat_history(self, ctx: discord.ApplicationContext):
        user_id = ctx.author.id
        user_history = self.userHistory.get(user_id)
        if not user_history:
            await ctx.respond(embed=SakuraEmbedMsg("錯誤", "該使用者的對話紀錄不存在"))
            return
        chat_history_str = ""
        for entry in user_history[8:]:
            role = entry.role
            for part in entry.parts:
                chat_history_str += f"{role}: {part.text}\n"
        chat_history_bytes = chat_history_str.encode('utf-8')
        chat_history_io = io.BytesIO(chat_history_bytes)
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
        persona = AiChat.UserAIChoice.static_get(message.author)
        chat = model.start_chat(history=AiChat.getStartupPrompt() if persona else None)
        reference_msg = bot.get_message(message.reference.message_id) if message.reference is not None else None
        user_AI_choice = os.getenv('PersonaStartPrompt') if AiChat.UserAIChoice.static_get(user=message.author) else "\n每段對話前會附上目前的實際時間和使用者的名字，您可以按照時間來了解目前實際上經過了多久和對話的人是誰，譬如目前的時間(早上、中午、晚上)，請不要在回答中寫出或重複與每段對話前的前置文相同的文字內容，如:'2024/09/05 01:35:11'\n"
        if reference_msg:
            chat = AiChat.get_chat_history(message=reference_msg, chat=chat, bot=bot)
            content_prefix = nowTime + user_AI_choice + "目前與您對話的人是" + name + "，請接續上一段對話\n\n"
        else:
            content_prefix = nowTime + user_AI_choice + "與您對話的人是" + name + "\n\n"
        content[0] = content_prefix + content[0]

        response = await chat.send_message_async(content=content, safety_settings=safety_settings)
        await message.reply(response.text)
        '''if not persona:
            await message.reply("```此對話由原版Google Gemini生成，請使用四春櫻人設模式以獲得使用機器人之最佳體驗```" + response.text)
        else:
            await message.reply(response.text)'''

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
    bot.add_cog(AiChat(bot))