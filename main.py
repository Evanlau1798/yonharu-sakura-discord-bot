import discord
import logger
import json
import os

#==================載入機器人本體==================
class mainBot(discord.Bot):
    def __init__(self, intents):
        super().__init__(intents=intents)
        #self.debug_guilds = [912688935363305484]

    async def on_ready(self):
        self.loadButton()
        print("done")
        print(f"目前使用者:{bot.user}")

    def loadButton(self): #views新增區
        from utils.help import HelpView
        from extensions.main_commands import PinnedMsgView
        bot.add_view(HelpView())
        bot.add_view(PinnedMsgView())
        return

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