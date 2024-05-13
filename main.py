import discord
import logger
import json
import os
import time
from discord.ext import tasks
from uptime import StatusServer

#==================載入機器人本體==================
class mainBot(discord.Bot):
    def __init__(self, intents):
        super().__init__(intents=intents)
        self.status_server = StatusServer()
        #self.debug_guilds = [912688935363305484]

    async def on_ready(self):
        self.loadButton()
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(bot.guilds)} 個伺服器"))
        self.guild_count_update.start()  # 啟動背景任務更新伺服器數
        await self.status_server.run()
        print("done")
        print(f"目前使用者:{bot.user}")

    @tasks.loop(minutes=30)  # 每30分鐘更新一次
    async def guild_count_update(self):
        print(str(time.time()) + "updated")
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(bot.guilds)} 個伺服器"))

    def loadButton(self): #views新增區
        from utils.help import HelpView
        from extensions.main_commands import PinnedMsgView
        bot.add_view(HelpView())
        bot.add_view(PinnedMsgView())
        return

#Phone online status : discord.gateway.DiscordWebSocket.identify()

if __name__ == "__main__":
    intents = discord.Intents.default()
    intents.message_content = True
    intents.messages = True
    intents.typing = True
    intents.voice_states = True
    intents.members = True
    bot = mainBot(intents=intents)

    if not os.path.exists("rank_tmp"):
        os.makedirs("rank_tmp")

    with open("./extensions.json", mode="r", encoding='utf-8') as extensions:
        extensions = json.load(extensions)

    for extension in extensions:
        bot.load_extension(extension)
    
    with open("./discord_key") as f:
        bot.run(str(f.read()))
        f.close()