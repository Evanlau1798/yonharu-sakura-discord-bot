ver = '姬宮真步#4176  discord bot  V2.0 先行開發版'

def help(embed, page):
  embed.set_author(name="姬宮真步#4176",icon_url="https://cdn.discordapp.com/app-icons/909796683418832956/13e44ec11c3a69d1bd042e3c41e5e320.png?size=128")
  embed.set_image(url="attachment://introduction.jpg")
  embed.add_field(name="** **", value="** **", inline=False)
  if page == '一般指令':
    embed.add_field(name="一般指令", value="** **", inline=False)
    embed.add_field(name="/help", value="開啟幫助列表", inline=True)
    embed.add_field(name="/random", value="直接打出指令，可以召喚香圖🤩\n(圖庫由 優衣 linebot 機器人提供)", inline=True)
    embed.add_field(name="/picture", value="用法: /picture [狀態]\n可以召喚指定角色的香圖\n(圖庫依然由 優衣 linebot 機器人提供)", inline=True)
    embed.add_field(name="/weather", value="用法: /weather [地區]\n查看指定地區的天氣狀況", inline=True)
    embed.add_field(name="/trans", value="用法: /trans [欲翻譯的句子或單詞]\n將輸入的文字翻譯成繁體中文\n(翻譯由google提供)", inline=True)
    embed.add_field(name="/pixiv", value="用法: /pixiv [搜尋關鍵字] [指定搜尋序列]\n可以直接搜尋pixiv上的圖片\n(目前暫不開放18+圖片搜尋)\n註:搜尋關鍵字內不可有空格", inline=True)
    embed.add_field(name="/create", value="用法: /create [頻道名稱] [頻道人數]\n可以創建動態性的語音頻道，方便使用者自訂頻道名稱及人數", inline=True)
    embed.add_field(name="/chat", value="AI對話", inline=True)
    embed.add_field(name="/dm", value="私訊作者", inline=True)
    embed.add_field(name="/game", value="遊玩小遊戲", inline=True)
    embed.add_field(name="/leaderboard", value="查看本伺服器總字數排名", inline=True)
    embed.add_field(name="/n", value="開車囉~(車子拋錨中OwO)", inline=True)
    embed.add_field(name="/pool", value="有問題就問問我吧!我可以幫你解答的", inline=True)
    embed.add_field(name="/rank", value="查看個人伺服器總字數排名", inline=True)
    embed.add_field(name="** **", value="** **", inline=False)
  elif page == "音樂相關指令":
    embed.add_field(name="音樂相關指令", value="** **", inline=False)
    embed.add_field(name="/resume", value="繼續撥放音樂", inline=True)
    embed.add_field(name="/play", value="從youtube撥放音樂!", inline=True)
    embed.add_field(name="/pause", value="暫停音樂", inline=True)
    embed.add_field(name="/leave", value="讓機器人離開語音頻道", inline=True)
    embed.add_field(name="/stop", value="停止撥放音樂", inline=True)
    embed.add_field(name="** **", value="** **", inline=False)
  elif page == "管理員專用指令":
    embed.add_field(name="管理員專用指令", value="** **", inline=False)
    embed.add_field(name="/vcset", value="用法: /vcset [頻道id]\n設定指定的頻道為動態語音創建用文字頻道", inline=True)
    embed.add_field(name="/vcdel", value="用法: /vcdel [頻道id]\n恢復指定的動態語音創建用文字頻道為一般頻道", inline=True)
    embed.add_field(name="/dvcset", value="設定指定的語音頻道為動態語音創建用語音頻道", inline=True)
    embed.add_field(name="** **", value="** **", inline=False)
  elif page == "額外指令":
    embed.add_field(name="額外指令", value="** **", inline=False)
    embed.add_field(name="/ping", value="測試機器人延遲", inline=True)
    embed.add_field(name="/roll", value="擲骰子", inline=True)
    embed.add_field(name="** **", value="** **", inline=False)
  elif page == "額外功能":
    embed.add_field(name="額外功能", value="** **", inline=False)
    embed.add_field(name="*這裡空空如也...*", value="** **", inline=True)
    embed.add_field(name="** **", value="** **", inline=False)
  embed.set_footer(text=ver)
  return embed