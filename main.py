import discord
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

# .envファイルからトークンを読み込み
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

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

    bot = MyBot()
    async with bot:
        await bot.start(TOKEN)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass