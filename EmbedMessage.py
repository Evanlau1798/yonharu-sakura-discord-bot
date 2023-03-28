import discord
from datetime import datetime
from random import choice

#==================建立專用Embed訊息==================
class SakuraEmbedMsg(discord.Embed):
    def __init__(self,title:str=None,description:str=None):
        super().__init__(title=title,description=description,colour=discord.Color.from_rgb(r=217,g=140,b=144))
        self.set_footer(text=f"四春櫻 | 願四季如春，櫻花永不凋零")#,icon_url="https://cdn.discordapp.com/attachments/1050082973891956799/1052222704582922301/BirthUploadPic.png")
        self.timestamp = datetime.now()