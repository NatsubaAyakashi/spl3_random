import discord
from discord.ext import commands
from discord import app_commands
from data.weapon_api import WeaponDataManager
from typing import List, Optional
import io

class Spl3Random(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_manager = WeaponDataManager()

    async def cog_load(self):
        """Cog読み込み時にデータをフェッチ（キャッシュ）します"""
        await self.data_manager.fetch_weapons()
        print("Splatoon 3 Weapon Data loaded.")

    async def _autocomplete_helper(self, current: str, get_items_method) -> List[app_commands.Choice[str]]:
        """オートコンプリートの共通ロジック"""
        await self.data_manager.fetch_weapons()
        items = get_items_method()
        choices = []
        for item in items:
            name = self.data_manager.get_localized_name(item, 'name')
            if current in name:
                choices.append(app_commands.Choice(name=name, value=item['key']))
        return choices[:25]

    async def weapon_type_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        return await self._autocomplete_helper(current, self.data_manager.get_weapon_types)

    async def sub_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        return await self._autocomplete_helper(current, self.data_manager.get_sub_weapons)

    async def special_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        return await self._autocomplete_helper(current, self.data_manager.get_special_weapons)

    @commands.hybrid_command(name="random_weapon", description="スプラトゥーン3のブキをランダムに選出します")
    @app_commands.describe(
        weapon_type="ブキの種類（シューター、チャージャーなど）",
        sub="サブウェポン（スプラッシュボムなど）",
        special="スペシャルウェポン（ウルトラショットなど）"
    )
    @app_commands.autocomplete(
        weapon_type=weapon_type_autocomplete,
        sub=sub_autocomplete,
        special=special_autocomplete
    )
    async def random_weapon(self, ctx: commands.Context, weapon_type: str = None, sub: str = None, special: str = None):
        """ブキをランダムに選出して表示するコマンド"""
        
        # データが空の場合は再取得を試みる
        await self.data_manager.fetch_weapons()

        weapon = self.data_manager.get_random_weapon(weapon_type, sub, special)

        if not weapon:
            await ctx.send("条件に一致するブキが見つかりませんでした。")
            return

        # 画像を取得して添付ファイルとして送信する処理
        key = weapon.get('key')
        image_url = self.data_manager.get_image_url(key)
        image_data = await self.data_manager.fetch_image_data(image_url)

        file = None
        embed_image_url = image_url

        if image_data:
            file = discord.File(io.BytesIO(image_data), filename=f"{key}.png")
            embed_image_url = f"attachment://{key}.png"

        embed = self._create_weapon_embed(weapon, embed_image_url)
        await ctx.send(embed=embed, file=file)

    def _create_weapon_embed(self, weapon: dict, image_url: Optional[str] = None) -> discord.Embed:
        """ブキ情報からEmbedを作成するヘルパーメソッド"""
        w_name = self.data_manager.get_localized_name(weapon, 'name')
        sub_name = self.data_manager.get_localized_name(weapon.get('sub', {}), 'name')
        sp_name = self.data_manager.get_localized_name(weapon.get('special', {}), 'name')
        w_type = self.data_manager.get_localized_name(weapon.get('type', {}), 'name')
        
        if image_url is None:
            image_url = self.data_manager.get_image_url(weapon.get('key'))

        # Embedの作成
        embed = discord.Embed(
            title="🦑 ランダムブキ選出結果",
            description=f"**{w_name}** が選ばれました！",
            color=discord.Color.orange()
        )
        
        embed.add_field(name="種類", value=w_type, inline=True)
        embed.add_field(name="サブ", value=sub_name, inline=True)
        embed.add_field(name="スペシャル", value=sp_name, inline=True)
        embed.set_image(url=image_url)

        return embed

async def setup(bot):
    await bot.add_cog(Spl3Random(bot))