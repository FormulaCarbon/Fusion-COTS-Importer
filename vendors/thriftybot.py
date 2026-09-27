from vendor import Vendor
import os, re, sys
import adsk.core # type: ignore[import-not-found]

lib_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if lib_path not in sys.path:
    sys.path.append(lib_path)

import requests

STOREFRONT = 'https://thethriftybot.com'
SUGGEST_URL = f'{STOREFRONT}/search/suggest.json'
DRIVE_DIRECT = 'https://drive.google.com/uc?export=download&id={id}'
MAX_RESULTS = 10
MAX_PROBES = 8
TIMEOUT = 30

HEADERS = {
    'Accept': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:154.0) Gecko/20100101 Firefox/154.0',
}

# CAD is linked from the product description, and the drive links carry no extension, so match the link text first and probe whatever is left.
ANCHOR = re.compile(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.S | re.I)
DRIVE_FILE = re.compile(r'drive\.google\.com/file/d/([A-Za-z0-9_-]{10,})')
TAG = re.compile(r'<[^>]+>')
EXTENSION = re.compile(r'\b(step|stp|iges|igs|sat|smt|f3d)\b', re.I)
SKU = re.compile(r'TTB-?\s?\d{3,4}', re.I)
UNSAFE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
CONTENT_DISPOSITION = re.compile(r'filename\*?="?([^";]+)', re.I)
NOISE = re.compile(r'^\s*(step\s*)?(cad\s*)?(file|files|model|models|available)?\s*$', re.I)

EXTENSION_MAP = {
    'step': 'step', 'stp': 'step', 'iges': 'iges', 'igs': 'iges',
    'sat': 'sat', 'smt': 'smt', 'f3d': 'f3d',
}

# drive ids don't change, so a resolved name can be kept
RESOLVED = {}


class ThriftyBot(Vendor):
    _probes = MAX_PROBES

    @property
    def name(self):
        return 'Thrifty Bot'

    def search(self, query: str, filters: dict, app) -> list[dict] | int:
        query = (query or '').strip()
        if not query:
            return []

        self._probes = MAX_PROBES

        allowed_types = [
            t.strip().lower()
            for t in (filters or {}).get('allowed_types', 'step').split(',')
            if t.strip()
        ]

        params = {
            'q': query,
            'resources[type]': 'product',
            'resources[limit]': str(MAX_RESULTS),
        }
        app.log(f'{self.name}: requesting search results for "{query}"')

        response = requests.get(
            SUGGEST_URL, params=params, headers=HEADERS, timeout=TIMEOUT
        )

        if response.status_code != 200:
            return response.status_code

        products = (
            response.json().get('resources', {}).get('results', {}).get('products', [])
        )

        out = []
        for product in products:
            result = self.__reformat__(product, allowed_types)
            if result['files']:
                out.append(result)

        app.log(f'{self.name}: {len(out)} of {len(products)} result(s) offer CAD')
        return out

    def add_inputs(self, inputs) -> dict:
        # hidden: search is keyword-driven from the shared search input
        allowed_types = inputs.addStringValueInput(
            f'allowed_types{self.name}', 'Allowed Types', 'step'
        )
        allowed_types.isVisible = False
        return {'allowed_types': allowed_types}

    def __reformat__(self, item: dict, allowed_types: list) -> dict:
        title = item.get('title', '').strip()

        links = []
        for href, text in ANCHOR.findall(item.get('body') or ''):
            link = self.__link__(href, text, allowed_types)
            if link:
                links.append(link)

        for link in links:
            link['name'] = self.__filename__(
                title, link.pop('label'), len(links) > 1, link['type'].lower()
            )

        return {
            'name': title,
            'author': self.__author__(title, item),
            'image': (item.get('featured_image') or item.get('image') or {}).get('url', ''),
            'files': links,
        }

    def __link__(self, href: str, text: str, allowed_types: list) -> dict | None:
        drive_id = DRIVE_FILE.search(href)
        if not drive_id:
            return None

        label = TAG.sub('', text).replace('&amp;', '&').strip()
        label = re.sub(r'\s+', ' ', label)
        extension = self.__extension__(label, href, allowed_types)

        if not extension:
            return None

        return {
            'name': '',
            'type': extension.upper(),
            'download_url': DRIVE_DIRECT.format(id=drive_id.group(1)),
            'label': label,
        }

    def __extension__(self, label: str, href: str, allowed_types: list) -> str | None:
        match = EXTENSION.search(label) or EXTENSION.search(href)
        if match:
            extension = EXTENSION_MAP[match.group(1).lower()]
            return extension if extension in allowed_types else None

        # some links are drawings rather than cads
        probed = self.__probe__(href)
        if not probed:
            return None

        extension = EXTENSION_MAP.get(probed.rsplit('.', 1)[-1].lower())
        return extension if extension in allowed_types else None

    def __probe__(self, href: str) -> str:
        drive_id = DRIVE_FILE.search(href)
        if not drive_id:
            return ''

        file_id = drive_id.group(1)
        if file_id in RESOLVED:
            return RESOLVED[file_id]

        if self._probes <= 0:
            return ''
        self._probes -= 1

        response = None
        try:
            response = requests.get(
                DRIVE_DIRECT.format(id=file_id),
                headers=HEADERS,
                stream=True,
                timeout=TIMEOUT,
            )
            disposition = response.headers.get('content-disposition', '')
            match = CONTENT_DISPOSITION.search(disposition)
            filename = match.group(1).strip() if match else ''
        except Exception:
            filename = ''
        finally:
            if response is not None:
                response.close()

        RESOLVED[file_id] = filename
        return filename

    def __filename__(self, title: str, label: str, disambiguate: bool, extension: str) -> str:
        stem = title
        if disambiguate and label and not NOISE.match(label):
            stem = f'{title} - {label}'

        stem = UNSAFE.sub('', stem.replace('"', 'in'))
        stem = re.sub(r'\s+', ' ', stem).strip(' .')
        return f'{stem[:100] or "part"}.{extension}'

    def __author__(self, title: str, item: dict) -> str:
        sku = SKU.search(f"{title} {item.get('body') or ''}")
        if sku:
            return re.sub(r'\s+', '', sku.group(0)).upper()
        return item.get('vendor') or 'The Thrifty Bot'
