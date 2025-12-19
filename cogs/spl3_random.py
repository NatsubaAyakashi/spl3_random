import discord
from discord.ext import commands
from discord import app_commands
from data.weapon_api import WeaponDataManager
from typing import List, Optional
import io
import random
import asyncio
import aiohttp
from PIL import Image

class Spl3Random(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_manager = WeaponDataManager()
        # ギアパワーのデータ格納用
        self.gear_powers = {
            'head': [],
            'clothing': [],
            'shoes': []
        }
        # 部位限定ギアのキー定義 (stat.ink APIのkeyに基づく)
        self.EXCLUSIVE_KEYS = {
            'head': ['opening_gambit', 'last_ditch_effort', 'tenacity', 'comeback'],
            'clothing': ['ninja_squid', 'haunt', 'thermal_ink', 'respawn_punisher', 'ability_doubler'],
            'shoes': ['stealth_jump', 'object_shredder', 'drop_roller']
        }
        # Inkipedia (SplatoonWiki) の画像URL定義
        self.GEAR_IMAGE_URLS = {
            'ink_saver_main': 'https://splatoonwiki.org/wiki/Special:Redirect/file/S3_Ability_Ink_Saver_(Main).png',
            'ink_saver_sub': 'https://splatoonwiki.org/wiki/Special:Redirect/file/S3_Ability_Ink_Saver_(Sub).png',
            'ink_recovery_up': 'https://splatoonwiki.org/wiki/Special:Redirect/file/S3_Ability_Ink_Recovery_Up.png',
            'run_speed_up': 'https://splatoonwiki.org/wiki/Special:Redirect/file/S3_Ability_Run_Speed_Up.png',
            'swim_speed_up': 'https://splatoonwiki.org/wiki/Special:Redirect/file/S3_Ability_Swim_Speed_Up.png',
            'special_charge_up': 'https://splatoonwiki.org/wiki/Special:Redirect/file/S3_Ability_Special_Charge_Up.png',
            'special_saver': 'https://splatoonwiki.org/wiki/Special:Redirect/file/S3_Ability_Special_Saver.png',
            'special_power_up': 'https://splatoonwiki.org/wiki/Special:Redirect/file/S3_Ability_Special_Power_Up.png',
            'quick_respawn': 'https://splatoonwiki.org/wiki/Special:Redirect/file/S3_Ability_Quick_Respawn.png',
            'quick_super_jump': 'https://splatoonwiki.org/wiki/Special:Redirect/file/S3_Ability_Quick_Super_Jump.png',
            'sub_power_up': 'https://splatoonwiki.org/wiki/Special:Redirect/file/S3_Ability_Sub_Power_Up.png',
            'ink_resistance_up': 'https://splatoonwiki.org/wiki/Special:Redirect/file/S3_Ability_Ink_Resistance_Up.png',
            'sub_resistance_up': 'https://splatoonwiki.org/wiki/Special:Redirect/file/S3_Ability_Sub_Resistance_Up.png',
            'intensify_action': 'https://splatoonwiki.org/wiki/Special:Redirect/file/S3_Ability_Intensify_Action.png',
            'opening_gambit': 'https://splatoonwiki.org/wiki/Special:Redirect/file/S3_Ability_Opening_Gambit.png',
            'last_ditch_effort': 'https://splatoonwiki.org/wiki/Special:Redirect/file/S3_Ability_Last-Ditch_Effort.png',
            'tenacity': 'https://splatoonwiki.org/wiki/Special:Redirect/file/S3_Ability_Tenacity.png',
            'comeback': 'https://splatoonwiki.org/wiki/Special:Redirect/file/S3_Ability_Comeback.png',
            'ninja_squid': 'https://splatoonwiki.org/wiki/Special:Redirect/file/S3_Ability_Ninja_Squid.png',
            'haunt': 'https://splatoonwiki.org/wiki/Special:Redirect/file/S3_Ability_Haunt.png',
            'thermal_ink': 'https://splatoonwiki.org/wiki/Special:Redirect/file/S3_Ability_Thermal_Ink.png',
            'respawn_punisher': 'https://splatoonwiki.org/wiki/Special:Redirect/file/S3_Ability_Respawn_Punisher.png',
            'ability_doubler': 'https://splatoonwiki.org/wiki/Special:Redirect/file/S3_Ability_Ability_Doubler.png',
            'stealth_jump': 'https://splatoonwiki.org/wiki/Special:Redirect/file/S3_Ability_Stealth_Jump.png',
            'object_shredder': 'https://splatoonwiki.org/wiki/Special:Redirect/file/S3_Ability_Object_Shredder.png',
            'drop_roller': 'https://splatoonwiki.org/wiki/Special:Redirect/file/S3_Ability_Drop_Roller.png'
        }

    async def cog_load(self):
        """Cog読み込み時にデータをフェッチ（キャッシュ）します"""
        await self.data_manager.fetch_weapons()
        await self.fetch_gear_abilities()
        print("Splatoon 3 Weapon Data loaded.")

    async def fetch_gear_abilities(self):
        """stat.ink APIからギアパワー情報を取得して分類する"""
        url = "https://stat.ink/api/v3/ability"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        self._process_gear_data(data)
                    else:
                        print(f"Failed to fetch gear data: {response.status}")
        except Exception as e:
            print(f"Error fetching gear data: {e}")

    def _process_gear_data(self, data):
        head = []
        clothing = []
        shoes = []
        
        for item in data:
            key = item.get('key')
            name = item.get('name', {}).get('ja_JP')
            
            if not key or not name:
                continue

            # 追加ギアパワー倍化 (ability_doubler) は特殊なギアのため除外
            if key == 'ability_doubler':
                continue
                
            # 部位限定の判定
            is_head = key in self.EXCLUSIVE_KEYS['head']
            is_clothing = key in self.EXCLUSIVE_KEYS['clothing']
            is_shoes = key in self.EXCLUSIVE_KEYS['shoes']
            
            item_data = {'name': name, 'key': key}
            if is_head:
                head.append(item_data)
            elif is_clothing:
                clothing.append(item_data)
            elif is_shoes:
                shoes.append(item_data)
            else:
                # 汎用ギア
                head.append(item_data)
                clothing.append(item_data)
                shoes.append(item_data)
        
        self.gear_powers['head'] = head
        self.gear_powers['clothing'] = clothing
        self.gear_powers['shoes'] = shoes

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

    @commands.hybrid_command(name="random_weapon", description="スプラトゥーン3のブキとギアをランダムに選出します")
    @app_commands.describe(
        weapon_type="ブキの種類（シューター、チャージャーなど）",
        sub="サブウェポン（スプラッシュボムなど）",
        special="スペシャルウェポン（ウルトラショットなど）",
        count="選出する人数（1〜8人）"
    )
    @app_commands.autocomplete(
        weapon_type=weapon_type_autocomplete,
        sub=sub_autocomplete,
        special=special_autocomplete
    )
    async def random_weapon(self, ctx: commands.Context, weapon_type: str = None, sub: str = None, special: str = None, count: int = 1):
        """ブキとギアをランダムに選出して表示するコマンド"""
        
        processing_msg = None
        try:
            # テキストコマンドで「!random_weapon 4」のように数値のみ指定された場合、それを人数として扱う
            if ctx.interaction is None and weapon_type and weapon_type.isdigit():
                count = int(weapon_type)
                weapon_type = None

            if count < 1 or count > 8:
                await ctx.reply("人数は 1〜8 の間で指定してください。")
                return
            
            # 処理中メッセージを送信
            processing_msg = await ctx.reply("生成中... ⏳")
            
            # データが空の場合は再取得を試みる
            await self.data_manager.fetch_weapons()
            if not self.gear_powers['head']:
                await self.fetch_gear_abilities()

            selected_weapons = []
            # 重複なしで武器を選出するロジック
            # 無限ループ防止のため試行回数制限を設ける
            max_attempts = count * 20
            attempts = 0
            
            while len(selected_weapons) < count and attempts < max_attempts:
                attempts += 1
                weapon = self.data_manager.get_random_weapon(weapon_type, sub, special)
                
                if not weapon:
                    break
                
                # 重複チェック (keyで比較)
                if any(w['key'] == weapon['key'] for w in selected_weapons):
                    continue
                    
                selected_weapons.append(weapon)

            if not selected_weapons:
                await ctx.reply("条件に一致するブキが見つかりませんでした。")
                return

            # ギア構成を先に生成
            selected_gears = []
            for _ in range(len(selected_weapons)):
                selected_gears.append(self._generate_gear_set())

            # 画像を合成して生成 (1人の場合もこれを使用)
            combined_image = await self._generate_combined_image(selected_weapons, selected_gears)
            file = None
            if combined_image:
                filename = f"loadout_{random.randint(1000, 9999)}.png"
                file = discord.File(combined_image, filename=filename)

            # 処理中メッセージを削除
            if processing_msg:
                try:
                    await processing_msg.delete()
                except Exception:
                    pass

            if count == 1:
                # 1人の場合は詳細Embed
                weapon = selected_weapons[0]
                head, clothing, shoes = selected_gears[0]
                
                # 画像は添付ファイルを使用
                embed = self._create_weapon_embed(weapon, f"attachment://{filename}" if file else None)
                embed.add_field(name="おすすめギア(ランダム)", value=f"🧢 {head['name']}\n👕 {clothing['name']}\n👟 {shoes['name']}", inline=False)
                embed.set_author(name=f"{ctx.author.display_name} さんの選出結果", icon_url=ctx.author.display_avatar.url)
                await ctx.reply(embed=embed, file=file)
            
            else:
                # 複数人の場合はリスト表示 + 合成画像
                embed = discord.Embed(
                    title=f"🦑 ランダムブキ＆ギア選出 ({len(selected_weapons)}人分)",
                    color=discord.Color.orange()
                )
                
                if file:
                    embed.set_image(url=f"attachment://{filename}")

                for i, weapon in enumerate(selected_weapons):
                    w_name = self.data_manager.get_localized_name(weapon, 'name')
                    head, clothing, shoes = selected_gears[i]
                    gear_text = f"🧢 {head['name']} | 👕 {clothing['name']} | 👟 {shoes['name']}"
                    embed.add_field(name=f"{i+1}: {w_name}", value=gear_text, inline=False)
                
                await ctx.reply(embed=embed, file=file)
        except Exception as e:
            # エラー時も処理中メッセージを削除
            if processing_msg:
                try:
                    await processing_msg.delete()
                except Exception:
                    pass
            await ctx.reply(f"エラーが発生しました: {e}")

    def _create_weapon_embed(self, weapon: dict, image_url: Optional[str] = None) -> discord.Embed:
        """ブキ情報からEmbedを作成するヘルパーメソッド"""
        w_name = self.data_manager.get_localized_name(weapon, 'name')
        sub_name = self.data_manager.get_localized_name(weapon.get('sub', {}), 'name')
        sp_name = self.data_manager.get_localized_name(weapon.get('special', {}), 'name')
        w_type = self.data_manager.get_localized_name(weapon.get('type', {}), 'name')
        
        if image_url is None:
            image_url = self.data_manager.get_image_url(weapon)

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

    def _generate_gear_set(self):
        """ランダムなギア構成を生成する"""
        # データがない場合のフォールバック
        if not self.gear_powers['head']:
             return {'name': "データ取得エラー", 'key': None}, {'name': "データ取得エラー", 'key': None}, {'name': "データ取得エラー", 'key': None}

        head = random.choice(self.gear_powers['head'])
        clothing = random.choice(self.gear_powers['clothing'])
        shoes = random.choice(self.gear_powers['shoes'])
        return head, clothing, shoes

    async def _fetch_external_image(self, url: str) -> Optional[bytes]:
        """外部URLから画像をダウンロードする"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.read()
        except Exception as e:
            print(f"Failed to fetch external image {url}: {e}")
        return None

    async def _generate_combined_image(self, weapons: List[dict], gear_sets: List[tuple]) -> Optional[io.BytesIO]:
        """複数のブキ画像とギアパワー画像を合成して1枚の画像にする"""
        
        async def _fetch_image(item, type_hint="Main"):
            if not item: return None
            url = self.data_manager.get_image_url(item, type_hint=type_hint)
            if not url: return None
            return await self.data_manager.fetch_image_data(url)

        # 画像取得タスク (メインのみ)
        tasks = []
        for w in weapons:
            tasks.append(_fetch_image(w, "Main"))           # Main

        # メインウェポンの画像データリスト
        main_weapon_images_data = await asyncio.gather(*tasks)
        
        # 有効な画像データがあるか確認
        if not main_weapon_images_data or all(d is None for d in main_weapon_images_data):
            return None

        # メイン画像のサイズ基準を取得 (最初の有効な画像から)
        first_valid_data = next((d for d in main_weapon_images_data if d is not None), None)
        try:
            with Image.open(io.BytesIO(first_valid_data)) as img:
                w, h = img.size
        except Exception as e:
            print(f"Error opening first image: {e}")
            return None
            
        # グリッド計算 (4人以上は2列、それ以下は1列など)
        count = len(weapons)
        if count <= 3:
            cols = count
            rows = 1
        else:
            cols = 2
            rows = (count + 1) // 2

        # ギアアイコンのサイズと余白
        gear_size = 64
        padding = 10
        
        # 1セルのサイズ計算
        # レイアウト:
        # [Main Weapon]
        # [Gear] [Gear] [Gear]
        cell_w = max(w, (gear_size * 3) + (padding * 2))
        cell_h = h + padding + gear_size + padding
        
        combined = Image.new('RGBA', (cell_w * cols, cell_h * rows), (0, 0, 0, 0))
        
        # ギア画像のキャッシュ
        gear_icon_cache = {}

        for i, main_bytes in enumerate(main_weapon_images_data):
            if not main_bytes: continue
            
            c = i % cols
            r = i // cols
            base_x = c * cell_w
            base_y = r * cell_h
            
            # 1. メインウェポン描画 (中央揃え)
            try:
                main_img = Image.open(io.BytesIO(main_bytes))
                if main_img.size != (w, h):
                    main_img = main_img.resize((w, h))
                
                main_x = base_x + (cell_w - w) // 2
                combined.paste(main_img, (int(main_x), int(base_y)))
            except Exception:
                print(f"Error processing weapon image index {i}")
                continue

            current_y = base_y + h + padding

            # 2. ギアパワー描画 (中央揃え)
            gears = gear_sets[i] # (head, clothing, shoes) dicts
            valid_gears = []
            
            for gear_data in gears:
                gear_key = gear_data.get('key')
                if not gear_key: continue

                # キャッシュ確認またはダウンロード
                if gear_key not in gear_icon_cache:
                    url = self.GEAR_IMAGE_URLS.get(gear_key)
                    if url:
                        gear_data_bytes = await self._fetch_external_image(url)
                        if gear_data_bytes:
                            try:
                                gear_img = Image.open(io.BytesIO(gear_data_bytes)).resize((gear_size, gear_size))
                                gear_icon_cache[gear_key] = gear_img
                            except Exception:
                                gear_icon_cache[gear_key] = None
                        else:
                            gear_icon_cache[gear_key] = None
                    else:
                        gear_icon_cache[gear_key] = None
                
                gear_icon = gear_icon_cache.get(gear_key)
                if gear_icon:
                    valid_gears.append(gear_icon)

            if valid_gears:
                total_w = (gear_size * len(valid_gears)) + (padding * (len(valid_gears) - 1))
                start_x = base_x + (cell_w - total_w) // 2
                for idx, img in enumerate(valid_gears):
                    combined.paste(img, (int(start_x + (gear_size + padding) * idx), int(current_y)))
            
        output = io.BytesIO()
        combined.save(output, format='PNG')
        output.seek(0)
        return output

async def setup(bot):
    await bot.add_cog(Spl3Random(bot))