import discord
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# .envファイルからトークンを読み込み
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Flaskアプリケーションのセットアップ
app = Flask(__name__)

@app.route('/')
def home():
    return "Discord bot is alive."

def run_web_server():
    # Renderが指定するポート、またはローカルテスト用に5000番ポートを使用
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# Discord Botのセットアップ
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        # Cogsフォルダ内の拡張機能をロード
        await self.load_extension("cogs.spl3_random")
        # スラッシュコマンドの同期
        await self.tree.sync()

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

async def main():
    if not TOKEN:
        print("Error: DISCORD_BOT_TOKEN not found in .env")
        return

    # Webサーバーを別スレッドで起動
    web_thread = Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()

    bot = MyBot()
    async with bot:
        await bot.start(TOKEN)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass