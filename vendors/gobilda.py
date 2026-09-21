from vendor import Vendor
import os, sys, re, html
import adsk.core #  type: ignore[import-not-found]

lib_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if lib_path not in sys.path:
    sys.path.append(lib_path)

import requests

class GoBilda(Vendor):
    @property
    def name(self):
        return 'GoBilda'

    UA = (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:154.0) '
        'Gecko/20100101 Firefox/154.0'
    )

    STEP_ZIP_RE = re.compile(
        r'(?:<a[^>]*class="[^"]*ext-zip[^"]*"[^>]*href="([^"]+\.zip)"'
        r'|"name"\s*:\s*"download STEP File"\s*,\s*"value"\s*:\s*"([^"]+\.zip)")'
    )
    SKU_RE = re.compile(r'"sku"\s*:\s*"([0-9-]+)"')
    OG_IMAGE_RE = re.compile(r'og:image[^>]*content="([^"]+)"')
    H1_RE = re.compile(r'<h1 class="productView-title"[^>]*>([^<]+)</h1>')

    _prod_cache = {}

    def search(self, query: str, filters: dict, app) -> list[dict] | int:
        app.log(f'{self.name}: search called with query="{query}" filters={filters}')

        # GB take the grid straight off gobilda.com (BigCommerce 'search.php')
        grid_url = (
            'https://www.gobilda.com/search.php?search_query='
            + query.replace(' ', '+')
        )
        headers = {'User-Agent': self.UA}

        response = requests.get(grid_url, headers=headers)
        if response.status_code != 200:
            return response.status_code

        cards = self._parse_grid(response.text)
        items = []

        # GrabCAD-style contract: each item carries name/author/image/files with
        # download_url. GoBilda's STEP zip lives on the *product page* (a
        # BigCommerce custom option 'download STEP File' -> /content/step_files/SKU.zip),
        # so we resolve each card by fetching its product page (cached).
        page_urls = [c['page_url'] for c in cards]
        for purl in page_urls:
            files = self._resolve_step(purl)
            items.append({
                'name': c['name'] if (c := next((x for x in cards if x['page_url'] == purl), {})) else '',
                'author': 'goBILDA',
                'image': c['image'] if (c := next((x for x in cards if x['page_url'] == purl), {})) else '',
                'files': files,
            })

        return items

    def add_inputs(self, inputs) -> dict:
        # hidden — gobilda search is keyword-driven via the search input
        allowed_types = inputs.addStringValueInput(
            f"allowed_types{self.name}", 'Allowed Types', 'step'
        )
        allowed_types.isVisible = False
        return {'allowed_types': allowed_types}

    def _parse_grid(self, grid_html: str) -> list[dict]:
        cards = []
        for li in re.findall(r'<li class="product".*?</li>', grid_html, re.S):
            href = re.search(r'<a href="(https://www\.gobilda\.com/[^"]+)"', li)
            img = re.search(r'<img[^>]*data-src="([^"]+)"', li) or \
                  re.search(r'<img[^>]*src="([^"]+)"', li)
            name = re.search(r'<h[43][^>]*>\s*<a [^>]*>([^<]{2,90})<', li) or \
                   re.search(r'title="([^"]{2,90})"', li)
            if not href:
                continue
            cards.append({
                'page_url': html.unescape(href.group(1)),
                'image': html.unescape(img.group(1)) if img else '',
                'name': html.unescape(name.group(1)).strip() if name else '',
            })
        return cards

    def _resolve_step(self, page_url: str) -> list[dict]:
        if page_url in self._prod_cache:
            return self._prod_cache[page_url]

        files = []
        try:
            resp = requests.get(page_url, headers={'User-Agent': self.UA}, timeout=30)
            if resp.status_code != 200:
                self._prod_cache[page_url] = files
                return files

            body = resp.text

            m = self.STEP_ZIP_RE.search(body)
            if not m:
                # fallback: classic <a href="/content/step_files/SKU.zip"> on today's BigCommerce page
                m2 = re.search(r'<a[^>]*href="([^"]+\.zip)"', body)
                if m2:
                    files.append(self._zip_dict(m2.group(1), body))
            else:
                files.append(self._zip_dict(m.group(1), body))

            self._prod_cache[page_url] = files
            return files
        except Exception:
            self._prod_cache[page_url] = files
            return files

    def _zip_dict(self, zip_rel: str, body: str) -> dict:
        zip_url = zip_rel if zip_rel.startswith('http') else 'https://www.gobilda.com' + zip_rel
        sku = self.SKU_RE.search(body)
        name = (sku.group(1) if sku else zip_rel.rsplit('/', 1)[-1]).removesuffix('.zip')
        return {
            'name': f'{name}.step',
            'type': 'step',
            'download_url': zip_url,
        }

    def __reformat__(self, item: dict, allowed_types: list) -> dict:
        links = [{
            'name': f['name'],
            'type': f['type'],
            'download_url': f['download_url'],
        } for f in item.get('files', [])]
        return {
            'name': item.get('name', ''),
            'author': 'goBILDA',
            'image': item.get('image', ''),
            'files': links,
        }
