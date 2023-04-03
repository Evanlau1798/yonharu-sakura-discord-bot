import discord
from utils.EmbedMessage import SakuraEmbedMsg
from typing import Dict

COMMANDS: Dict[str, Dict[str, str]] = {
    "一般指令": {
        "/help": "開啟幫助列表",
        "/random": "直接打出指令，可以召喚香圖🤩\n(圖庫由 優衣 linebot 機器人提供)",
        "/picture": "用法: /picture [狀態]\n可以召喚指定角色的香圖\n(圖庫依然由 優衣 linebot 機器人提供)",
        "/weather": "用法: /weather [地區]\n查看指定地區的天氣狀況",
        "/trans": "用法: /trans [欲翻譯的句子或單詞]\n將輸入的文字翻譯成繁體中文\n(翻譯由google提供)",
        "/pixiv": "用法: /pixiv [搜尋關鍵字] [指定搜尋序列]\n可以直接搜尋pixiv上的圖片\n(目前暫不開放18+圖片搜尋)\n註:搜尋關鍵字內不可有空格",
        "/create": "用法: /create [頻道名稱] [頻道人數]\n可以創建動態性的語音頻道，方便使用者自訂頻道名稱及人數",
        "/chat": "AI對話",
        "/dm": "私訊作者",
        "/game": "遊玩小遊戲",
        "/leaderboard": "查看本伺服器總字數排名",
        "/n": "開車囉~(車子拋錨中OwO)",
        "/pool": "有問題就問問我吧!我可以幫你解答的",
        "/rank": "查看個人伺服器總字數排名",
    },
    "音樂相關指令": {
        "/resume": "繼續撥放音樂",
        "/play": "從youtube撥放音樂!",
        "/pause": "暫停音樂",
        "/leave": "讓機器人離開語音頻道",
        "/stop": "停止撥放音樂",
    },
    "管理員專用指令": {
        "/vcset": "用法: /vcset [頻道id]\n設定指定的頻道為動態語音創建用文字頻道",
        "/vcdel": "用法: /vcdel [頻道id]\n恢復指定的動態語音創建用文字頻道為一般頻道",
        "/dvcset": "設定指定的語音頻道為動態語音創建用語音頻道",
    },
    "額外指令": {
        "/ping": "測試機器人延遲",
        "/roll": "擲骰子",
    },
    "額外功能": {
        "這裡空空如也...": "** **",
    },
}

EMBED_CONTENTS: Dict[str, str] = {
    "一般指令": "一般指令",
    "音樂相關指令": "音樂相關指令",
    "管理員專用指令": "管理員專用指令",
    "額外指令": "額外指令",
    "額外功能": "額外功能",
}

class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        title = ['一般指令','音樂相關指令','管理員專用指令','額外指令','額外功能']
        description = ["/game,/create,/leaderboard,/rank,/pool等指令",
                       "/resume,/play,/stop等指令",
                       "/vcset,/vcdel,/dvcset,/kick,/ban等指令",
                       "/ping,/roll等指令",
                       "額外的指令功能"]
        options = []
        for i in range(len(title)):
            options.append(discord.SelectOption(label=title[i], description=description[i]))
        self.select = discord.ui.Select(placeholder="請選擇選項",options=options,custom_id="help_list")
        self.select.callback = self.select_callback
        self.add_item(item=self.select)

    def set_message(self,message: discord.Interaction):
        self.EphemeralMessage = message

    async def select_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        page: str = str(self.select.values[0])
        embed = SakuraEmbedMsg(title="指令使用說明")
        if (contents := COMMANDS.get(page)) is not None:
            embed.add_field(name=EMBED_CONTENTS[page], value="** **", inline=False)
            for cmd, desc in contents.items():
                embed.add_field(name=cmd, value=desc, inline=True)
        else:
            embed.add_field(name="未知指令類別", value="請選擇正確的指令類別。", inline=True)
        await self.EphemeralMessage.edit_original_response(embed=embed)