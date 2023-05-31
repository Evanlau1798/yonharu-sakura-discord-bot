import discord
from discord.ext import commands
from discord import default_permissions,option,OptionChoice
from discord import SlashCommandOptionType as type
from utils.EmbedMessage import SakuraEmbedMsg
from collections import deque

delete_snipes = {} # 建立兩個字典，用來儲存每個伺服器最近刪除和編輯的訊息
edited_snipes = {}
MAX_MESSAGES = 25 # 定義一個常數，表示每個伺服器能儲存的訊息數量上限

class SnipeEventsListener(commands.Cog):
    def __init__(self, bot:discord.Bot):
        self.bot = bot
        self.edit_serial_no = 1
        self.delete_serial_no = 1
    
    @commands.slash_command(description="查看最近被刪除的訊息")
    @default_permissions(administrator=True)
    async def deletesnipe(self,message: discord.ApplicationContext):
        try:
            view=DeleteSnipeMsgView(message=message)
            await message.respond(embed=SakuraEmbedMsg(title="請選擇欲查看的訊息"),view=view)
        except:
            await message.respond(embed=SakuraEmbedMsg(title="錯誤",description="目前沒有已儲存之被刪除的訊息"), ephemeral=True)

    @commands.slash_command(description="查看最近被編輯的訊息")
    @default_permissions(administrator=True)
    async def editsnipe(self,message: discord.ApplicationContext):
        try:
            view=EditSnipeMsgView(message=message)
            await message.respond(embed=SakuraEmbedMsg(title="請選擇欲查看的訊息"),view=view)
        except:
            await message.respond(embed=SakuraEmbedMsg(title="錯誤",description="目前沒有已儲存之被編輯的訊息"), ephemeral=True)

    @commands.Cog.listener()
    async def on_message_delete(self,message:discord.Message):
        print(message.content)
        global delete_snipes
        if message.author.bot:return
        guild_id = message.guild.id
        message = SerialNoAdder(after=message,SerialNo=self.delete_serial_no)
        self.delete_serial_no += 1
        if guild_id in delete_snipes:
            queue = delete_snipes[guild_id]
            queue.appendleft(message)
            if len(queue) > MAX_MESSAGES:
                queue.pop()
        else:
            queue = deque([message]) # 如果該伺服器沒有儲存的訊息，則建立一個新的雙端佇列，並將被刪除的訊息加入其中
            delete_snipes[guild_id] = queue

    @commands.Cog.listener()
    async def on_message_edit(self,before:discord.Message, after:discord.Message):
        print("舊:",before.content,"新:",after.content)
        global delete_snipes
        if before.author.bot:return
        guild_id = before.guild.id
        message = SerialNoAdder(before=before, after=after, SerialNo=self.edit_serial_no)
        self.edit_serial_no += 1
        if guild_id in edited_snipes:
            queue = edited_snipes[guild_id]
            queue.appendleft(message)
            if len(queue) > MAX_MESSAGES: # 如果佇列的長度超過上限，則移除佇列的右側元素
                queue.pop()
        else:
            queue = deque([message]) # 如果該伺服器沒有儲存的訊息，則建立一個新的雙端佇列，並將被編輯的訊息加入其中
            edited_snipes[guild_id] = queue

class EditSnipeMsgView(discord.ui.View):
    def __init__(self,message: discord.ApplicationContext):
        super().__init__(timeout=None)
        options = []
        if message.guild.id in edited_snipes:
            queue = edited_snipes[message.guild.id]
            for snipe_message in queue:
                snipe_message:discord.Message
                options.append(discord.SelectOption(label=snipe_message.after_message.content[:100], description=f"訊息作者:{snipe_message.after_message.author}",value=str(snipe_message.SerialNo)))
        else:
            return ValueError("未找到紀錄")
        self.select = discord.ui.Select(placeholder="請選擇訊息",options=options,custom_id="Sniped_Msg_View")
        self.select.callback = self.select_callback
        self.add_item(item=self.select)

    async def select_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        guild_edit_message = edited_snipes[interaction.guild.id]
        msg_serial_no = int(interaction.data["values"][0])
        for snipe_message in guild_edit_message:
            if snipe_message.SerialNo == msg_serial_no:
                embed = SakuraEmbedMsg()
                embed.set_author(name="訊息編輯紀錄", icon_url=snipe_message.before_message.author.avatar.url)
                embed.add_field(name="使用者",value=snipe_message.before_message.author.mention)
                embed.add_field(name="發送至的頻道",value=snipe_message.before_message.channel.mention)
                embed.add_field(name="編輯前內容",value=snipe_message.before_message.content,inline=False)
                embed.add_field(name="編輯後內容",value=snipe_message.after_message.content,inline=False)
                embed.add_field(name="發送時間",value=f"{snipe_message.before_message.created_at}\n<t:{int(snipe_message.before_message.created_at.timestamp())}>")
                embed.add_field(name="編輯時間",value=f"{snipe_message.after_message.edited_at}\n<t:{int(snipe_message.after_message.edited_at.timestamp())}>")
                embed.add_field(name="訊息連結",value=snipe_message.after_message.jump_url)
                if len(snipe_message.before_message.attachments) != 0:
                    embed.set_image(url=snipe_message.before_message.attachments[0])
                await interaction.message.edit(embed=embed)
                return
            
class DeleteSnipeMsgView(discord.ui.View):
    def __init__(self,message: discord.ApplicationContext):
        super().__init__(timeout=None)
        options = []
        if message.guild.id in delete_snipes:
            queue = delete_snipes[message.guild.id]
            for snipe_message in queue:
                snipe_message:discord.Message
                options.append(discord.SelectOption(label=snipe_message.after_message.content[:100], description=f"訊息作者:{snipe_message.after_message.author}",value=str(snipe_message.SerialNo)))
        else:
            return ValueError("未找到紀錄")
        self.select = discord.ui.Select(placeholder="請選擇訊息",options=options,custom_id="Deleted_Msg_View")
        self.select.callback = self.select_callback
        self.add_item(item=self.select)

    async def select_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        guild_delete_message = delete_snipes[interaction.guild.id]
        msg_serial_no = int(interaction.data["values"][0])
        for snipe_message in guild_delete_message:
            if snipe_message.SerialNo == msg_serial_no:
                embed = SakuraEmbedMsg()
                embed.set_author(name="訊息刪除紀錄", icon_url=snipe_message.after_message.author.avatar.url)
                embed.add_field(name="使用者",value=snipe_message.after_message.author.mention,inline=False)
                embed.add_field(name="發送至的頻道",value=snipe_message.after_message.channel.mention,inline=False)
                embed.add_field(name="訊息內容",value=snipe_message.after_message.content,inline=False)
                embed.add_field(name="發送時間",value=f"{snipe_message.after_message.created_at}\n<t:{int(snipe_message.after_message.created_at.timestamp())}>",inline=False)
                if len(snipe_message.after_message.attachments) != 0:
                    embed.set_image(url=snipe_message.attachments[0])
                await interaction.message.edit(embed=embed)
                return


class SerialNoAdder():
    def __init__(self,before=None,after=None, SerialNo=None):
        self.before_message = before
        self.after_message = after
        self.SerialNo = SerialNo

def setup(bot:discord.Bot):
    bot.add_cog(SnipeEventsListener(bot))