import discord
import logger
import json
import os
import phone

PATH = os.path.join(os.path.dirname(__file__))

#==================載入機器人本體==================
class mainBot(discord.Bot):
    def __init__(self):
        super().__init__()
        #self.debug_guilds = [912688935363305484,969732954572075008]

    async def on_ready(self):
        self.loadButton()
        print(f"目前使用者:{bot.user}")

    def loadButton(self):
        #views新增區
        return

if __name__ == "__main__":
    bot = mainBot()

    with open(f"{PATH}/extensions.json", mode="r", encoding='utf-8') as extensions:
        extensions = json.load(extensions)

    for extension in extensions:
        bot.load_extension(extension)
    
    with open(f"{PATH}/discord_key") as f:
        bot.run(str(f.read()))
        f.close()