import aiohttp
import random
import urllib.parse
from typing import List, Dict, Optional

class WeaponDataParams:
    API_URL = "https://stat.ink/api/v3/weapon"
    USER_AGENT = "Spl3RandomBot/1.0"

class WeaponDataManager:
    def __init__(self):
        self._cache: List[Dict] = []

    async def fetch_weapons(self) -> None:
        """APIからブキデータを取得してキャッシュします"""
        if self._cache:
            return

        headers = {"User-Agent": WeaponDataParams.USER_AGENT}
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                async with session.get(WeaponDataParams.API_URL) as response:
                    if response.status == 200:
                        self._cache = await response.json()
                    else:
                        print(f"Error fetching data: {response.status}")
                        self._cache = []
            except Exception as e:
                print(f"Exception during fetch: {e}")
                self._cache = []

    async def fetch_image_data(self, url: str) -> Optional[bytes]:
        """URLから画像データを取得します"""
        headers = {"User-Agent": WeaponDataParams.USER_AGENT}
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        print(f"Failed to fetch image: {response.status} - {url}")
            except Exception as e:
                print(f"Error fetching image: {e}")
        return None

    def get_random_weapon(self, weapon_type: Optional[str] = None, sub: Optional[str] = None, special: Optional[str] = None) -> Optional[Dict]:
        """キャッシュからランダムに1つのブキ情報を返します"""
        if not self._cache:
            return None
        
        candidates = self._cache
        if weapon_type:
            candidates = [w for w in candidates if w.get('type', {}).get('key') == weapon_type]
        if sub:
            candidates = [w for w in candidates if w.get('sub', {}).get('key') == sub]
        if special:
            candidates = [w for w in candidates if w.get('special', {}).get('key') == special]
            
        if not candidates:
            return None
        return random.choice(candidates)

    def _get_unique_items(self, field: str) -> List[Dict]:
        """指定されたフィールドのユニークなアイテムリストを返します"""
        items = {}
        for w in self._cache:
            item = w.get(field)
            if item and 'key' in item:
                items[item['key']] = item
        return list(items.values())

    def get_weapon_types(self) -> List[Dict]:
        """利用可能なブキの種類リストを返します"""
        return self._get_unique_items('type')

    def get_sub_weapons(self) -> List[Dict]:
        """利用可能なサブウェポンのリストを返します"""
        return self._get_unique_items('sub')

    def get_special_weapons(self) -> List[Dict]:
        """利用可能なスペシャルウェポンのリストを返します"""
        return self._get_unique_items('special')

    @staticmethod
    def get_localized_name(data: Dict, key: str = 'name', lang: str = 'ja_JP') -> str:
        """多言語対応フィールドから指定言語の文字列を取り出します"""
        if not data:
            return "Unknown"
        return data.get(key, {}).get(lang, "Unknown")

    @staticmethod
    def get_image_url(weapon: Dict) -> str:
        """Inkipediaの画像URLを生成します"""
        # 英語名を取得し、ファイル名用に整形（空白とスラッシュをアンダースコアに置換）
        name = weapon.get('name', {}).get('en_US', 'Unknown')
        filename = name.replace(' ', '_').replace('/', '_')
        
        # URLエンコードしてRedirect URLを生成
        encoded_name = urllib.parse.quote(f"S3_Weapon_Main_{filename}.png")
        return f"https://splatoonwiki.org/wiki/Special:Redirect/file/{encoded_name}"